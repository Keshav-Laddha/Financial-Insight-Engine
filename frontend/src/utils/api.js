// API configuration and utility functions
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Allowed file types - PDF only
export const ALLOWED_FILE_TYPES = {
  pdf: [".pdf"],
};

export const ALLOWED_EXTENSIONS = [".pdf"];

// File size limits (in bytes)
export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

// API functions
export const api = {
  async uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/upload/`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Upload failed");
    }

    return await response.json();
  },

  async analyzeFile(fileId) {
    const response = await fetch(`${API_BASE_URL}/analyze/${fileId}`, {
      method: "GET",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Analysis failed");
    }

    return await response.json();
  },

  async getSummary(fileId) {
    const response = await fetch(`${API_BASE_URL}/summary/${fileId}`, {
      method: "GET",
    });

    if (!response.ok) {
      let err;
      try {
        err = await response.json();
      } catch {
        throw new Error("Summary fetch failed");
      }
      throw new Error(err.detail || "Summary fetch failed");
    }

    return await response.json();
  },

  // async getFiles() {
  //   // Note: This endpoint doesn't exist yet in the backend
  //   // For now, we'll use localStorage as a fallback
  //   // TODO: Implement backend endpoint to list files
  //   try {
  //     const response = await fetch(`${API_BASE_URL}/files/`, {
  //       method: "GET",
  //     });

  //     if (response.ok) {
  //       return await response.json();
  //     }
  //   } catch (error) {
  //     console.warn("Files endpoint not available, using localStorage fallback");
  //   }

  //   // Fallback to localStorage
  //   const storedFiles = localStorage.getItem("uploadedFiles");
  //   return storedFiles ? JSON.parse(storedFiles) : [];
  // },

  // inside your api object
  async getFiles() {
    try {
      const response = await fetch(`${API_BASE_URL}/files/`, { method: "GET" });
      if (response.ok) {
        const serverFiles = await response.json();
        // Merge with localStorage fallback (avoid duplicates by id or stored_as)
        const local = JSON.parse(localStorage.getItem("uploadedFiles") || "[]");
        const map = new Map();
        // add server-first (server is source-of-truth)
        for (const f of serverFiles) {
          map.set(f.id || f.stored_as || f.name, f);
        }
        // add any local items that server doesn't have
        for (const f of local) {
          const key = f.id || f.stored_as || f.name;
          if (!map.has(key)) map.set(key, f);
        }
        return Array.from(map.values());
      }
    } catch (error) {
      console.warn("Files endpoint not available, using localStorage fallback");
    }
    // fallback
    const storedFiles = localStorage.getItem("uploadedFiles");
    return storedFiles ? JSON.parse(storedFiles) : [];
  },

  async saveFileMetadata(info) {
    try {
      const res = await fetch(`${API_BASE_URL}/files/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(info),
      });
      if (res.ok) return await res.json();
      // non-200 -> ignore but return false
      return null;
    } catch (err) {
      console.warn("Failed to save metadata to server (backend may not be running)", err);
      return null;
    }
  },


  async deleteFile(fileId) {
    // Note: This endpoint doesn't exist yet in the backend
    // For now, we'll use localStorage
    try {
      const response = await fetch(`${API_BASE_URL}/files/${fileId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.warn("Delete endpoint not available, using localStorage fallback");
    }

    // Fallback to localStorage
    const storedFiles = localStorage.getItem("uploadedFiles");
    if (storedFiles) {
      const files = JSON.parse(storedFiles);
      const updated = files.filter((f) => f.id !== fileId);
      localStorage.setItem("uploadedFiles", JSON.stringify(updated));
    }
    return { message: "File deleted successfully" };
  },

  // // inside export const api = { ... }
  // async saveFileMetadata(info) {
  //   try {
  //     const res = await fetch(`${API_BASE_URL}/files/save`, {
  //       method: "POST",
  //       headers: { "Content-Type": "application/json" },
  //       body: JSON.stringify(info),
  //     });

  //     if (!res.ok) {
  //       // try to parse server error
  //       let errBody;
  //       try { errBody = await res.json(); } catch (_) { errBody = null; }
  //       throw new Error((errBody && errBody.detail) || `Save metadata failed (${res.status})`);
  //     }

  //     return await res.json();
  //   } catch (err) {
  //     console.error("saveFileMetadata error:", err);
  //     throw err;
  //   }
  // },

};

// File validation utilities
export const validateFile = (file) => {
  const errors = [];

  // Check file type
  const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    errors.push(
      `File type not supported. Allowed types: ${ALLOWED_EXTENSIONS.join(", ")}`
    );
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    errors.push(
      `File size exceeds limit. Maximum size: ${(MAX_FILE_SIZE / 1024 / 1024).toFixed(0)}MB`
    );
  }

  if (file.size === 0) {
    errors.push("File is empty");
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

// Format file size
export const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
};

// Format date
export const formatDate = (dateString) => {
  if (!dateString) return "Unknown";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};