import { NavLink } from "react-router-dom";
import { FiUpload, FiBarChart2, FiFolder, FiMenu, FiX, FiFileText } from "react-icons/fi";

export default function Sidebar({ collapsed, toggle }) {
  const navItems = [
    { path: "/upload", icon: FiUpload, label: "Upload" },
    { path: "/dashboard", icon: FiBarChart2, label: "Dashboard" },
    { path: "/files", icon: FiFolder, label: "Uploaded Files" },

    // ✅ NEW ITEM BELOW (Company Summary)
    { path: "/summary", icon: FiFileText, label: "Company Summary" },
  ];

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <button className="hamburger" onClick={toggle} aria-label="Toggle sidebar">
        {collapsed ? <FiMenu size={22} /> : <FiX size={22} />}
      </button>

      <div className="brand">
        <div className="logo">FIE</div>
        {!collapsed && <div className="brand-text">Financial Insight Engine</div>}
      </div>

      <nav className="nav">
        {navItems.map(({ path, icon: Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `nav-link ${isActive ? "active" : ""}`
            }
            title={collapsed ? label : undefined}
          >
            <Icon size={20} className="nav-icon" />
            {!collapsed && <span className="nav-label">{label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        {!collapsed && <small>Shivam & Keshav</small>}
      </div>
    </aside>
  );
}
