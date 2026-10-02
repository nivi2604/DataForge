import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import apiClient from '../api/client';
import './Auth.css';

/* ─────────────────────────────────────────────────────────────────────────────
   Shared brand panel — identical to Login, keeps both pages coherent.
   Extracted here to avoid an import cycle or a separate shared file.
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

const PipelineSteps: React.FC = () => (
  <div className="auth-pipeline">
    <div className="auth-pipeline-steps">
      <div className="auth-step">
        <div className="auth-step-icon s-source"><IconDatabase color="#60a5fa" /></div>
        <span className="auth-step-label">Source</span>
      </div>
      <div className="auth-step-connector" />
      <div className="auth-step">
        <div className="auth-step-icon s-transform"><IconGear color="#a78bfa" /></div>
        <span className="auth-step-label">Transform</span>
      </div>
      <div className="auth-step-connector" />
      <div className="auth-step">
        <div className="auth-step-icon s-validate"><IconCheck color="#34d399" /></div>
        <span className="auth-step-label">Validate</span>
      </div>
      <div className="auth-step-connector" />
      <div className="auth-step">
        <div className="auth-step-icon s-output"><IconChart color="#fbbf24" /></div>
        <span className="auth-step-label">Output</span>
      </div>
    </div>
  </div>
);

const BrandPanel: React.FC = () => (
  <aside className="auth-brand-panel">
    <div className="auth-brand-logo">
      <LogoIcon />
      <span className="auth-brand-logo-name">DataForge</span>
    </div>

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

    <div className="auth-feature-list">
      <div className="auth-feature-item">
        <span className="auth-feature-dot" aria-hidden="true" />
        Pipeline builder with real-time execution
      </div>
      <div className="auth-feature-item">
        <span className="auth-feature-dot" aria-hidden="true" />
        Automated data quality checks
      </div>
      <div className="auth-feature-item">
        <span className="auth-feature-dot" aria-hidden="true" />
        GitHub integration for CI/CD workflows
      </div>
    </div>
  </aside>
);

/* ─────────────────────────────────────────────────────────────────────────────
   Alert components
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

const AlertSuccess: React.FC<{ message: string }> = ({ message }) => (
  <div className="auth-alert auth-alert-success" role="status">
    <svg className="auth-alert-icon" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="7" stroke="#4ade80" strokeWidth="1.4" />
      <path d="M5 8.2l2 2 4-4" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
    <span>{message}</span>
  </div>
);

/* ─────────────────────────────────────────────────────────────────────────────
   Register page
   ───────────────────────────────────────────────────────────────────────────── */

const Register: React.FC = () => {
  const [firstName, setFirstName] = useState('');
  const [lastName,  setLastName]  = useState('');
  const [email,     setEmail]     = useState('');
  const [password,  setPassword]  = useState('');
  const [error,     setError]     = useState('');
  const [success,   setSuccess]   = useState('');
  const [loading,   setLoading]   = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      await apiClient.post('/auth/register', {
        first_name: firstName,
        last_name:  lastName,
        email,
        password,
      });
      setSuccess('Registration successful! Redirecting to sign in…');
      setTimeout(() => navigate('/login'), 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <BrandPanel />

      <main className="auth-form-panel">
        <div className="auth-form-inner">

          <h1 className="auth-form-heading">Create your account</h1>
          <p className="auth-form-subheading">
            Join DataForge and start building data pipelines.
          </p>

          {error   && <AlertError   message={error}   />}
          {success && <AlertSuccess message={success} />}

          <form onSubmit={handleSubmit} noValidate>
            <div className="auth-name-row">
              <div className="auth-form-group">
                <label htmlFor="reg-first-name" className="auth-form-label">
                  First name
                </label>
                <input
                  id="reg-first-name"
                  type="text"
                  autoComplete="given-name"
                  value={firstName}
                  onChange={e => setFirstName(e.target.value)}
                  required
                  className="auth-form-input"
                  placeholder="Jane"
                />
              </div>
              <div className="auth-form-group">
                <label htmlFor="reg-last-name" className="auth-form-label">
                  Last name
                </label>
                <input
                  id="reg-last-name"
                  type="text"
                  autoComplete="family-name"
                  value={lastName}
                  onChange={e => setLastName(e.target.value)}
                  required
                  className="auth-form-input"
                  placeholder="Doe"
                />
              </div>
            </div>

            <div className="auth-form-group">
              <label htmlFor="reg-email" className="auth-form-label">
                Email address
              </label>
              <input
                id="reg-email"
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
              <label htmlFor="reg-password" className="auth-form-label">
                Password
                <span className="auth-field-hint">min. 8 characters</span>
              </label>
              <input
                id="reg-password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={8}
                className="auth-form-input"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !!success}
              className="auth-submit-btn"
              aria-busy={loading}
            >
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <hr className="auth-divider" />

          <p className="auth-footer-text">
            Already have an account?{' '}
            <Link to="/login" className="auth-footer-link">
              Sign in
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
};

export default Register;
