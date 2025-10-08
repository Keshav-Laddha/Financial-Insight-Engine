from fastapi import FastAPI
from app.routes import upload
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app=FastAPI( #instantiate app with metadata
    title="Financial Document Analaysis API",
    description="Secure backend for OCR, text extraction, and analysis of financial reports."
)

#To prevent Host Header Injection Attack
#Attackers can attack host header to perform cache poisning or redirect attackks
app.add_middleware( #add only trusted host middleware (OWASP- prevent host header attacks)
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app"] #allow req from these specific hostnames only
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:5173", "https://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"]
)

app.include_router(upload.router, prefix="/upload", tags=["Upload"])
#app.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])


@app.get("/ping", tags=["Health"])
def ping():
    """
    Simple endpoint to verify that backend is running.
    Does not expose sensitive info (OWASP: A6 Sensitive Data Exposure)
    """
    return {"status": "ok", "message": "Backend is alive and secure!"}