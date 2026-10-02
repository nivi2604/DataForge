import React, { useState, useEffect, useCallback } from 'react';
import { 
  listConnections, 
  createConnection, 
  deleteConnection, 
  listBranches, 
  listPullRequests, 
  mergePullRequest, 
  closePullRequest,
  listPRValidations,
} from '../api/github';
import type {
  GithubConnectionResponse,
  GithubBranch,
  GithubPullRequest,
  PRValidationRecord,
} from '../api/github';
import './GitHub.css';

const STATUS_COLORS: Record<string, string> = {
  passed:  '#059669',
  failed:  '#dc2626',
  running: '#d97706',
  skipped: '#64748b',
  pending: '#2563eb',
  open:    '#059669',
  merged:  '#7c3aed',
  closed:  '#dc2626'
};

function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  const color = STATUS_COLORS[s] ?? '#64748b';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      padding: '4px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 600,
      backgroundColor: color + '15', color: color, border: `1px solid ${color}40`, whiteSpace: 'nowrap', textTransform: 'uppercase'
    }}>
      {status}
    </span>
  );
}

function BranchGroup({ title, branches }: { title: string, branches: GithubBranch[] }) {
  const [expanded, setExpanded] = useState(false);
  const LIMIT = 5;
  const visible = expanded ? branches : branches.slice(0, LIMIT);
  
  return (
    <div>
      <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600, marginBottom: '6px', textTransform: 'uppercase' }}>
        {title} {branches.length > LIMIT && !expanded ? `(${branches.length})` : ''}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
        {visible.map(b => (
          <span key={b.name} className="gh-branch-badge" title={b.name}>{b.name}</span>
        ))}
        {branches.length > LIMIT && !expanded && (
          <button 
            onClick={() => setExpanded(true)}
            style={{ background: 'none', border: 'none', color: '#3b82f6', fontSize: '12px', fontWeight: 500, cursor: 'pointer', padding: '0 4px' }}
          >
            View all
          </button>
        )}
      </div>
    </div>
  );
}

const GitHub: React.FC = () => {
  const [connections, setConnections]           = useState<GithubConnectionResponse[]>([]);
  const [loading, setLoading]                   = useState(true);
  const [error, setError]                       = useState('');
  const [repoName, setRepoName]                 = useState('');
  const [token, setToken]                       = useState('');
  const [adding, setAdding]                     = useState(false);
  const [selectedConnection, setSelectedConnection] = useState<GithubConnectionResponse | null>(null);
  const [branches, setBranches]                 = useState<GithubBranch[]>([]);
  const [prs, setPrs]                           = useState<GithubPullRequest[]>([]);
  const [validations, setValidations]           = useState<PRValidationRecord[]>([]);
  const [validationsLoading, setValidationsLoading] = useState(false);

  const fetchConnections = async () => {
    try {
      setLoading(true);
      const data = await listConnections();
      setConnections(data);
      if (data.length > 0 && !selectedConnection) {
        handleSelectConnection(data[0]);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load GitHub connections');
    } finally {
      setLoading(false);
    }
  };

  const fetchValidations = useCallback(async (repoName?: string) => {
    try {
      setValidationsLoading(true);
      const data = await listPRValidations(repoName);
      setValidations(data);
    } catch {
      // non-fatal
    } finally {
      setValidationsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConnections();
    fetchValidations();
  }, [fetchValidations]);

  const handleAddConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setAdding(true);
      await createConnection({ repository_name: repoName, token });
      setRepoName('');
      setToken('');
      await fetchConnections();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to connect repository');
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to remove this connection?')) return;
    try {
      await deleteConnection(id);
      if (selectedConnection?.id === id) {
        setSelectedConnection(null);
        setBranches([]);
        setPrs([]);
      }
      await fetchConnections();
    } catch {
      alert('Failed to delete connection');
    }
  };

  const handleSelectConnection = async (conn: GithubConnectionResponse) => {
    setSelectedConnection(conn);
    try {
      const [bData, pData] = await Promise.all([
        listBranches(conn.id),
        listPullRequests(conn.id),
      ]);
      setBranches(bData);
      setPrs(pData);
      fetchValidations(conn.repository_name);
    } catch {
      // Ignore errors for display
    }
  };

  const handleMergePR = async (prNumber: number) => {
    if (!selectedConnection) return;
    try {
      await mergePullRequest(selectedConnection.id, prNumber);
      await handleSelectConnection(selectedConnection);
    } catch {
      alert('Failed to merge PR');
    }
  };

  const handleClosePR = async (prNumber: number) => {
    if (!selectedConnection) return;
    try {
      await closePullRequest(selectedConnection.id, prNumber);
      await handleSelectConnection(selectedConnection);
    } catch {
      alert('Failed to close PR');
    }
  };

  const repoValidations = selectedConnection
    ? validations.filter(v => v.repository_name === selectedConnection.repository_name)
    : validations;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">GitHub Integration</h1>
        <p className="page-subtitle">Connect repositories and track DataForge pipeline output through GitHub.</p>
      </div>

      <div className="gh-flow-diagram">
        <div className="gh-flow-box gh">GitHub<br/><span style={{fontWeight: 400}}>Input File</span></div>
        <div className="gh-flow-arrow">→</div>
        <div className="gh-flow-box">DataForge<br/><span style={{fontWeight: 400}}>Pipeline</span></div>
        <div className="gh-flow-arrow">→</div>
        <div className="gh-flow-box">Transform</div>
        <div className="gh-flow-arrow">→</div>
        <div className="gh-flow-box">Data Quality</div>
        <div className="gh-flow-arrow">→</div>
        <div className="gh-flow-box">Output</div>
        <div className="gh-flow-arrow">→</div>
        <div className="gh-flow-box final">GitHub PR</div>
      </div>

      {error && <div style={{ padding: '12px', background: '#fef2f2', color: '#b91c1c', borderRadius: '6px', marginBottom: '20px' }}>{error}</div>}

      <div className="gh-layout">
        <div className="gh-sidebar">
          <div className="card">
            <h2 className="card-title" style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>Connected Repositories</h2>
            {loading ? (
              <div style={{ color: '#64748b', fontSize: '13px' }}>Loading connections...</div>
            ) : connections.length === 0 ? (
              <div className="empty-state" style={{ padding: '20px 0' }}>
                <div className="empty-state-title">No GitHub repository connected</div>
                <div style={{ fontSize: '13px' }}>Connect a repository below to process data through GitHub.</div>
              </div>
            ) : (
              <ul className="gh-conn-list">
                {connections.map(c => (
                  <li 
                    key={c.id} 
                    className={`gh-conn-item ${selectedConnection?.id === c.id ? 'selected' : ''}`}
                    onClick={() => handleSelectConnection(c)}
                  >
                    <div className="gh-conn-header">
                      <div className="gh-repo-name" title={c.repository_name}>{c.repository_name}</div>
                    </div>
                    <div className="gh-status-indicator">Connected</div>
                    <button className="gh-btn-remove" onClick={(e) => handleDelete(c.id, e)}>Remove Connection</button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="card">
            <h2 className="card-title" style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>Connect Repository</h2>
            <form onSubmit={handleAddConnection} autoComplete="off">
              <div className="form-group">
                <label className="form-label">Repository Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="owner/repo"
                  value={repoName}
                  onChange={e => setRepoName(e.target.value)}
                  required
                  autoComplete="off"
                  data-1p-ignore
                />
              </div>
              <div className="form-group">
                <label className="form-label">Personal Access Token</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="ghp_..."
                  value={token}
                  onChange={e => setToken(e.target.value)}
                  required
                  autoComplete="new-password"
                  data-1p-ignore
                />
              </div>
              <button type="submit" disabled={adding} className="btn btn-primary" style={{ width: '100%' }}>
                {adding ? 'Connecting...' : 'Connect Repository'}
              </button>
            </form>
          </div>
        </div>

        <div className="gh-main">
          {selectedConnection ? (
            <>
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                  <h2 className="card-title" style={{ margin: 0, fontSize: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    {selectedConnection.repository_name}
                  </h2>
                  <a href={`https://github.com/${selectedConnection.repository_name}`} target="_blank" rel="noreferrer" className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '13px' }}>
                    Open Repository ↗
                  </a>
                </div>

                <div style={{ marginBottom: '32px' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#475569', marginBottom: '12px', textTransform: 'uppercase' }}>Active Branches</h3>
                  {(() => {
                    if (branches.length === 0) {
                      return <span style={{ fontSize: '13px', color: '#64748b' }}>No branches available.</span>;
                    }

                    const mainBranches = branches.filter(b => b.name === 'main' || b.name === 'master');
                    const outputBranches = branches.filter(b => b.name.startsWith('output-pr-'));
                    const otherBranches = branches.filter(b => b.name !== 'main' && b.name !== 'master' && !b.name.startsWith('output-pr-'));

                    return (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {mainBranches.length > 0 && (
                          <div>
                            <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600, marginBottom: '6px', textTransform: 'uppercase' }}>Main</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                              {mainBranches.map(b => (
                                <span key={b.name} className="gh-branch-badge" style={{ borderColor: '#3b82f6', color: '#1d4ed8', background: '#eff6ff' }} title={b.name}>{b.name}</span>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {outputBranches.length > 0 && (
                          <BranchGroup title="DataForge Output" branches={outputBranches} />
                        )}

                        {otherBranches.length > 0 && (
                          <BranchGroup title="Other Branches" branches={otherBranches} />
                        )}
                      </div>
                    );
                  })()}
                </div>

                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#475569', marginBottom: '12px', textTransform: 'uppercase' }}>Pull Requests</h3>
                  {prs.length === 0 ? (
                    <div className="empty-state" style={{ padding: '30px', border: '1px dashed #e2e8f0', borderRadius: '8px' }}>
                      <div className="empty-state-title">No pull requests found</div>
                      <div style={{ fontSize: '13px' }}>DataForge output will generate Pull Requests here.</div>
                    </div>
                  ) : (
                    <div className="gh-pr-list">
                      {prs.map(pr => (
                        <div key={pr.number} className="gh-pr-card">
                          <div className="gh-pr-header">
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <a href={pr.html_url} target="_blank" rel="noreferrer" className="gh-pr-title" style={{ display: 'block', textDecoration: 'none' }} title={pr.title}>
                                #{pr.number} {pr.title}
                              </a>
                              <div className="gh-pr-meta">
                                <span>DataForge Output: <span className="gh-branch-badge" title={pr.head_branch}>{pr.head_branch}</span></span>
                                <span>↓</span>
                                <span className="gh-branch-badge" title={pr.base_branch}>{pr.base_branch}</span>
                              </div>
                            </div>
                            <StatusBadge status={pr.state} />
                          </div>
                          
                          {pr.state === 'open' && (
                            <div className="gh-pr-actions">
                              <button onClick={() => handleMergePR(pr.number)} className="btn btn-primary" style={{ padding: '6px 12px', fontSize: '12px' }}>Merge PR</button>
                              <button onClick={() => handleClosePR(pr.number)} className="btn btn-danger" style={{ padding: '6px 12px', fontSize: '12px' }}>Close</button>
                              <a href={pr.html_url} target="_blank" rel="noreferrer" className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px', textDecoration: 'none' }}>Open on GitHub →</a>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                  <h2 className="card-title" style={{ margin: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>PR Validation Activity</h2>
                  <button onClick={() => fetchValidations(selectedConnection.repository_name)} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
                    ↻ Refresh
                  </button>
                </div>

                {validationsLoading ? (
                  <div style={{ color: '#64748b', fontSize: '13px' }}>Loading validations...</div>
                ) : repoValidations.length === 0 ? (
                  <div className="empty-state" style={{ padding: '40px', border: '1px dashed #e2e8f0', borderRadius: '8px' }}>
                    <div className="empty-state-title">No PR validation activity yet</div>
                    <div style={{ fontSize: '13px' }}>Configure a GitHub webhook pointing to your DataForge instance.</div>
                  </div>
                ) : (
                  <div className="table-container">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>PR</th>
                          <th>Branch</th>
                          <th>Commit</th>
                          <th>Status</th>
                          <th>Summary</th>
                          <th>Time</th>
                        </tr>
                      </thead>
                      <tbody>
                        {repoValidations.map(v => (
                          <tr key={v.id}>
                            <td>
                              {v.pr_html_url ? (
                                <a href={v.pr_html_url} target="_blank" rel="noreferrer" style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 600 }}>
                                  #{v.pr_number}
                                </a>
                              ) : (
                                <span style={{ fontWeight: 600, color: '#475569' }}>#{v.pr_number}</span>
                              )}
                            </td>
                            <td><span className="gh-branch-badge" title={v.head_branch}>{v.head_branch}</span></td>
                            <td><span className="gh-commit-hash">{(v.commit_sha || '').slice(0, 7)}</span></td>
                            <td><StatusBadge status={v.status || 'pending'} /></td>
                            <td style={{ maxWidth: '250px' }}>
                              {v.status === 'failed' && v.failure_reason ? (
                                <div style={{ color: '#dc2626', fontSize: '12px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={v.failure_reason}>
                                  {v.failure_reason}
                                </div>
                              ) : (
                                <div style={{ color: '#475569', fontSize: '12px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={v.result_summary ?? ''}>
                                  {v.result_summary}
                                </div>
                              )}
                            </td>
                            <td style={{ color: '#64748b', fontSize: '12px', whiteSpace: 'nowrap' }}>
                              {v.created_at ? new Date(v.created_at).toLocaleString() : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="empty-state" style={{ flex: 1, backgroundColor: 'white', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <div className="empty-state-title">Select a Repository</div>
              <div style={{ fontSize: '13px' }}>Choose a connected repository from the sidebar to view branches, PRs, and validation activity.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GitHub;
