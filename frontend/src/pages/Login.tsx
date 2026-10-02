import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import apiClient from '../api/client';
import { setToken } from '../utils/auth';
import './Auth.css';

/* ─────────────────────────────────────────────────────────────────────────────
   Brand panel
   ───────────────────────────────────────────────────────────────────────────── */

const LogoIcon: React.FC = () => (
  <div className="auth-brand-logo-icon">
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <rect x="1.5" y="1.5" width="6"  height="6"  rx="1.4" fill="white" opacity="0.95" />
      <rect x="10.5" y="1.5" width="6" height="6"  rx="1.4" fill="white" opacity="0.5"  />
      <rect x="1.5" y="10.5" width="6" height="6"  rx="1.4" fill="white" opacity="0.5"  />
      <rect x="10.5" y="10.5" width="6" height="6" rx="1.4" fill="white" opacity="0.95" />
    </svg>
  </div>
);

/* SVG icons — no emojis, consistent sizing across OS */
const IconDatabase: React.FC<{ color: string }> = ({ color }) => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
    <ellipse cx="8" cy="4" rx="6" ry="2.2" stroke={color} strokeWidth="1.4" />
    <path d="M2 4v4c0 1.2 2.7 2.2 6 2.2s6-1 6-2.2V4" stroke={color} strokeWidth="1.4" />
    <path d="M2 8v4c0 1.2 2.7 2.2 6 2.2s6-1 6-2.2V8" stroke={color} strokeWidth="1.4" />
  </svg>
);

const IconGear: React.FC<{ color: string }> = ({ color }) => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
    <circle cx="8" cy="8" r="2.2" stroke={color} strokeWidth="1.4" />
    <path d="M8 1.5v1.3M8 13.2v1.3M1.5 8h1.3M13.2 8h1.3M3.4 3.4l.9.9M11.7 11.7l.9.9M3.4 12.6l.9-.9M11.7 4.3l.9-.9"
      stroke={color} strokeWidth="1.4" strokeLinecap="round" />
  </svg>
);

const IconCheck: React.FC<{ color: string }> = ({ color }) => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
    <circle cx="8" cy="8" r="6" stroke={color} strokeWidth="1.4" />
    <path d="M5 8.2l2 2 4-4" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const IconChart: React.FC<{ color: string }> = ({ color }) => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
    <rect x="2" y="8"  width="2.5" height="6" rx="0.8" fill={color} />
    <rect x="6.75" y="5" width="2.5" height="9" rx="0.8" fill={color} />
    <rect x="11.5" y="2" width="2.5" height="12" rx="0.8" fill={color} />
  </svg>
);

const IconFeature: React.FC = () => (
  <span className="auth-feature-dot" aria-hidden="true" />
);

const PipelineSteps: React.FC = () => (
  <div className="auth-pipeline">
    <div className="auth-pipeline-steps">
      <div className="auth-step">
        <div className="auth-step-icon s-source">
          <IconDatabase color="#60a5fa" />
        </div>
        <span className="auth-step-label">Source</span>
      </div>

      <div className="auth-step-connector" />

      <div className="auth-step">
        <div className="auth-step-icon s-transform">
          <IconGear color="#a78bfa" />
        </div>
        <span className="auth-step-label">Transform</span>
      </div>

      <div className="auth-step-connector" />

      <div className="auth-step">
        <div className="auth-step-icon s-validate">
          <IconCheck color="#34d399" />
        </div>
        <span className="auth-step-label">Validate</span>
      </div>

      <div className="auth-step-connector" />

      <div className="auth-step">
        <div className="auth-step-icon s-output">
          <IconChart color="#fbbf24" />
        </div>
        <span className="auth-step-label">Output</span>
      </div>
    </div>
  </div>
);

const BrandPanel: React.FC = () => (
  <aside className="auth-brand-panel">
    {/* Logo */}
    <div className="auth-brand-logo">
      <LogoIcon />
      <span className="auth-brand-logo-name">DataForge</span>
    </div>

    {/* Headline and sub-copy */}
    <div className="auth-brand-copy">
      <h2 className="auth-brand-headline">
        Build reliable<br />data pipelines.
      </h2>
      <p className="auth-brand-subtext">
        Manage data workflows, validate data quality, and monitor pipeline
        executions — all in one place.
      </p>
      <PipelineSteps />
    </div>

    {/* Feature list — honest, factual, no fake numbers */}
    <div className="auth-feature-list">
      <div className="auth-feature-item"><IconFeature />Pipeline builder with real-time execution</div>
      <div className="auth-feature-item"><IconFeature />Automated data quality checks</div>
      <div className="auth-feature-item"><IconFeature />GitHub integration for CI/CD workflows</div>
    </div>
  </aside>
);

/* ─────────────────────────────────────────────────────────────────────────────
   Login page
   ───────────────────────────────────────────────────────────────────────────── */

const AlertError: React.FC<{ message: string }> = ({ message }) => (
  <div className="auth-alert auth-alert-error" role="alert">
    <svg className="auth-alert-icon" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="7" stroke="#f87171" strokeWidth="1.4" />
      <path d="M8 5v3.5" stroke="#f87171" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="8" cy="11" r="0.8" fill="#f87171" />
    </svg>
    <span>{message}</span>
  </div>
);

const Login: React.FC = () => {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      setToken(response.data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <BrandPanel />

      <main className="auth-form-panel">
        <div className="auth-form-inner">

          <h1 className="auth-form-heading">Welcome back</h1>
          <p className="auth-form-subheading">Sign in to continue to DataForge.</p>

          {error && <AlertError message={error} />}

          <form onSubmit={handleSubmit} noValidate>
            <div className="auth-form-group">
              <label htmlFor="login-email" className="auth-form-label">
                Email address
              </label>
              <input
                id="login-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="auth-form-input"
                placeholder="name@company.com"
              />
            </div>

            <div className="auth-form-group">
              <label htmlFor="login-password" className="auth-form-label">
                Password
              </label>
              <input
                id="login-password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className="auth-form-input"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="auth-submit-btn"
              aria-busy={loading}
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <hr className="auth-divider" />

          <p className="auth-footer-text">
            Don't have an account?{' '}
            <Link to="/register" className="auth-footer-link">
              Create one
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
};

export default Login;
