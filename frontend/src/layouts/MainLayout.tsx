import React from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { removeToken } from '../utils/auth';

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    removeToken();
    navigate('/login');
  };

  const linkStyle = (path: string) => ({
    display: 'block',
    padding: '8px 12px',
    color: location.pathname === path ? '#ffffff' : '#94a3b8',
    textDecoration: 'none',
    backgroundColor: location.pathname === path ? '#334155' : 'transparent',
    borderRadius: '6px',
    fontSize: '13px',
    fontWeight: 500,
    transition: 'all 0.2s ease',
    marginBottom: '2px'
  });

  const sectionStyle = {
    fontSize: '11px',
    fontWeight: 700,
    color: '#64748b',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
    margin: '20px 0 8px 12px'
  };

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: "Inter, 'Segoe UI', system-ui, sans-serif", overflow: 'hidden' }}>
      {/* Sidebar — fixed width, never shrinks */}
      <nav style={{
        width: '220px',
        flexShrink: 0,
        backgroundColor: '#0f172a',
        padding: '24px 12px',
        color: 'white',
        display: 'flex',
        flexDirection: 'column',
        boxSizing: 'border-box',
        overflowY: 'auto',
        zIndex: 10,
      }}>
        <div style={{ padding: '0 12px', marginBottom: '32px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '28px', height: '28px', backgroundColor: '#3b82f6', borderRadius: '7px', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <rect x="2" y="2" width="5" height="5" rx="1" fill="white" opacity="0.9"/>
              <rect x="9" y="2" width="5" height="5" rx="1" fill="white" opacity="0.6"/>
              <rect x="2" y="9" width="5" height="5" rx="1" fill="white" opacity="0.6"/>
              <rect x="9" y="9" width="5" height="5" rx="1" fill="white" opacity="0.9"/>
            </svg>
          </div>
          <span style={{ margin: 0, fontSize: '17px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.3px' }}>DataForge</span>
        </div>

        <div style={{ flex: 1 }}>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            <li><Link to="/dashboard" style={linkStyle('/dashboard')}>Dashboard</Link></li>

            <li style={sectionStyle}>Workspace</li>
            <li><Link to="/organizations" style={linkStyle('/organizations')}>Organizations</Link></li>
            <li><Link to="/workspaces" style={linkStyle('/workspaces')}>Workspaces</Link></li>
            <li><Link to="/projects" style={linkStyle('/projects')}>Projects</Link></li>

            <li style={sectionStyle}>Data</li>
            <li><Link to="/data-sources" style={linkStyle('/data-sources')}>Data Sources</Link></li>
            <li><Link to="/executions" style={linkStyle('/executions')}>Run History</Link></li>
            <li><Link to="/data-quality" style={linkStyle('/data-quality')}>Data Quality</Link></li>

            <li style={sectionStyle}>Integrations</li>
            <li><Link to="/github" style={linkStyle('/github')}>GitHub</Link></li>
          </ul>
        </div>

        <button
          onClick={handleLogout}
          style={{
            marginTop: '20px',
            width: '100%',
            padding: '10px',
            backgroundColor: 'transparent',
            color: '#ef4444',
            border: '1px solid rgba(239,68,68,0.5)',
            cursor: 'pointer',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 500,
            transition: 'all 0.2s',
          }}
          onMouseOver={(e) => { e.currentTarget.style.backgroundColor = '#ef4444'; e.currentTarget.style.color = 'white'; }}
          onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = '#ef4444'; }}
        >
          Logout
        </button>
      </nav>

      {/* Main content — scrollable independently */}
      <main style={{
        flex: 1,
        backgroundColor: '#f8fafc',
        overflowY: 'auto',
        overflowX: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        minWidth: 0,
      }}>
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;
