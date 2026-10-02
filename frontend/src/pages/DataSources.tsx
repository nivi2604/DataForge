import React, { useEffect, useState, useMemo } from 'react';
import { getDataSources, createDataSource, updateDataSource, deleteDataSource, testConnection, uploadDataSourceFile } from '../api/dataSources';
import { getProjects } from '../api/projects';
import { listConnections } from '../api/github';
import type { DataSource, Project } from '../types';
import type { GithubConnectionResponse } from '../api/github';
import './DataSources.css';

const DataSources: React.FC = () => {
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [githubConnections, setGithubConnections] = useState<GithubConnectionResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Filter state
  const [filter, setFilter] = useState('All');

  // Drawer State
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState('');
  
  // Form State
  const [projectId, setProjectId] = useState('');
  const [name, setName] = useState('');
  const [type, setType] = useState('PostgreSQL');
  const [statusField, setStatusField] = useState('active');
  
  const [dbHost, setDbHost] = useState('');
  const [dbPort, setDbPort] = useState('5432');
  const [dbName, setDbName] = useState('');
  const [dbUser, setDbUser] = useState('');
  const [dbPass, setDbPass] = useState('');
  
  const [filePath, setFilePath] = useState('');
  const [apiUrl, setApiUrl] = useState('');
  
  const [githubConnectionId, setGithubConnectionId] = useState('');
  const [githubBranch, setGithubBranch] = useState('');
  const [githubFilePath, setGithubFilePath] = useState('');
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  
  // Tests per card
  const [testResults, setTestResults] = useState<Record<string, {success: boolean, message: string}>>({});
  const [testingId, setTestingId] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [dsRes, projRes, githubRes] = await Promise.all([
        getDataSources(),
        getProjects(),
        listConnections().catch(() => [])
      ]);
      setDataSources(dsRes);
      setProjects(projRes);
      setGithubConnections(githubRes as GithubConnectionResponse[]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const resetForm = () => {
    setIsEditing(false);
    setEditingId('');
    setName('');
    setProjectId(projects.length > 0 ? projects[0].id : '');
    setType('PostgreSQL');
    setStatusField('active');
    setDbHost('');
    setDbPort('5432');
    setDbName('');
    setDbUser('');
    setDbPass('');
    setFilePath('');
    setApiUrl('');
    setGithubConnectionId('');
    setGithubBranch('');
    setGithubFilePath('');
    setSelectedFile(null);
    setFormError('');
  };

  const handleOpenDrawer = (ds?: DataSource) => {
    resetForm();
    if (ds) {
      setIsEditing(true);
      setEditingId(ds.id);
      setName(ds.name);
      setProjectId(ds.project_id || (projects.length > 0 ? projects[0].id : ''));
      setType(ds.type);
      setStatusField(ds.status || 'active');
      
      try {
        const details = ds.connection_details ? JSON.parse(ds.connection_details) : {};
        if (ds.type === 'PostgreSQL' || ds.type === 'MySQL') {
          setDbHost(details.host || '');
          setDbPort(details.port || '');
          setDbName(details.database || '');
          setDbUser(details.username || '');
          setDbPass(''); // never populate password
        } else if (['CSV', 'JSON', 'Parquet', 'Excel'].includes(ds.type)) {
          setFilePath(details.path || '');
        } else if (ds.type === 'REST API') {
          setApiUrl(details.url || '');
        } else if (ds.type === 'GitHub') {
          setGithubConnectionId(details.connection_id || '');
          setGithubBranch(details.branch || '');
          setGithubFilePath(details.file_path || '');
        }
      } catch (e) {
        console.error('Failed to parse connection details');
      }
    }
    setIsDrawerOpen(true);
  };

  const closeDrawer = () => {
    setIsDrawerOpen(false);
    resetForm();
  };

  const buildConnectionDetails = () => {
    if (type === 'PostgreSQL' || type === 'MySQL') {
      return JSON.stringify({
        host: dbHost,
        port: parseInt(dbPort) || (type === 'PostgreSQL' ? 5432 : 3306),
        database: dbName,
        username: dbUser,
        password: dbPass
      });
    } else if (['CSV', 'JSON', 'Parquet', 'Excel'].includes(type)) {
      return filePath ? JSON.stringify({ path: filePath }) : '{}';
    } else if (type === 'REST API') {
      return JSON.stringify({ url: apiUrl });
    } else if (type === 'GitHub') {
      return JSON.stringify({
        connection_id: githubConnectionId,
        branch: githubBranch,
        file_path: githubFilePath
      });
    }
    return '{}';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    
    if (isEditing && (type === 'PostgreSQL' || type === 'MySQL') && !dbPass) {
      setFormError('Please re-enter the password to save changes.');
      setSubmitting(false);
      return;
    }

    const payload = {
      project_id: projectId,
      name,
      type,
      status: statusField,
      connection_details: buildConnectionDetails()
    };
    
    try {
      let createdDataSource;
      if (isEditing) {
        createdDataSource = await updateDataSource(editingId, payload);
      } else {
        createdDataSource = await createDataSource(payload);
      }
      
      if (selectedFile && ['CSV', 'JSON', 'Parquet', 'Excel'].includes(type)) {
        await uploadDataSourceFile(createdDataSource.id, selectedFile);
      }
      
      await fetchData();
      closeDrawer();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to save data source.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this data source?')) return;
    try {
      await deleteDataSource(id);
      setDataSources(dataSources.filter(d => d.id !== id));
      setTestResults(prev => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete data source.');
    }
  };

  const handleTestConnection = async (id: string) => {
    setTestingId(id);
    setTestResults(prev => ({ ...prev, [id]: { success: true, message: 'Testing...' } }));
    try {
      const res = await testConnection(id);
      setTestResults(prev => ({ ...prev, [id]: { success: res.success, message: res.message || 'Connection successful!' } }));
    } catch (err: any) {
      setTestResults(prev => ({ ...prev, [id]: { success: false, message: err.response?.data?.detail || 'Connection failed.' } }));
    } finally {
      setTestingId(null);
    }
  };

  const filteredSources = useMemo(() => {
    if (filter === 'All') return dataSources;
    if (filter === 'GitHub') return dataSources.filter(ds => ds.type === 'GitHub');
    if (filter === 'Files') return dataSources.filter(ds => ['CSV', 'JSON', 'Parquet', 'Excel'].includes(ds.type));
    if (filter === 'Databases') return dataSources.filter(ds => ['PostgreSQL', 'MySQL'].includes(ds.type));
    if (filter === 'APIs') return dataSources.filter(ds => ds.type === 'REST API');
    return dataSources;
  }, [dataSources, filter]);

  const getBadgeClass = (type: string) => {
    if (type === 'GitHub') return 'badge badge-github';
    if (['PostgreSQL', 'MySQL'].includes(type)) return 'badge badge-postgres';
    if (type === 'REST API') return 'badge badge-api';
    return 'badge badge-file';
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Data Sources</h1>
          <p className="page-subtitle">Manage the data sources used by your DataForge pipelines.</p>
        </div>
        <button onClick={() => handleOpenDrawer()} className="btn btn-primary">
          + Add Data Source
        </button>
      </div>
      
      {error && <div className="alert alert-error">{error}</div>}

      <div className="ds-filters">
        {['All', 'GitHub', 'Files', 'Databases', 'APIs'].map(f => (
          <button 
            key={f} 
            className={`ds-filter-btn ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ color: '#64748b' }}>Loading data sources...</div>
      ) : filteredSources.length === 0 ? (
        <div className="empty-state">
          <h3 className="empty-state-title">No data sources yet</h3>
          <p className="empty-state-subtitle">Connect a source to start building your first pipeline.</p>
          <button onClick={() => handleOpenDrawer()} className="btn btn-primary">
            + Add Data Source
          </button>
        </div>
      ) : (
        <div className="ds-grid">
          {filteredSources.map(ds => {
            const project = projects.find(p => p.id === ds.project_id);
            let details: any = {};
            try { details = ds.connection_details ? JSON.parse(ds.connection_details) : {}; } catch (e) {}

            return (
              <div key={ds.id} className="ds-card">
                {/* Card header: name + type badge */}
                <div className="ds-card-header">
                  <div className="ds-card-title-group">
                    <h3 className="ds-card-title" title={ds.name}>{ds.name}</h3>
                    <p className="ds-card-project">{project?.name || ds.project_id}</p>
                  </div>
                  <span className={getBadgeClass(ds.type)}>{ds.type}</span>
                </div>

                {/* Card body: metadata rows */}
                <div className="ds-card-body">
                  <div className="ds-info-row">
                    <span className="ds-info-label">Status</span>
                    <span className={`badge ${ds.status === 'active' ? 'badge-active' : 'badge-inactive'}`}>
                      {ds.status || 'unknown'}
                    </span>
                  </div>

                  {ds.type === 'GitHub' && (
                    <>
                      <div className="ds-info-row">
                        <span className="ds-info-label">Repository</span>
                        <span className="ds-info-value" title={githubConnections.find(c => c.id === details.connection_id)?.repository_name || 'Unknown'}>
                          {githubConnections.find(c => c.id === details.connection_id)?.repository_name || 'Unknown'}
                        </span>
                      </div>
                      <div className="ds-info-row">
                        <span className="ds-info-label">Branch</span>
                        <span className="ds-info-value" title={details.branch || '-'}>{details.branch || '-'}</span>
                      </div>
                      <div className="ds-info-row">
                        <span className="ds-info-label">File Path</span>
                        <span className="ds-info-value ds-info-path" title={details.file_path || '-'}>{details.file_path || '-'}</span>
                      </div>
                    </>
                  )}

                  {(ds.type === 'PostgreSQL' || ds.type === 'MySQL') && (
                    <>
                      <div className="ds-info-row">
                        <span className="ds-info-label">Host</span>
                        <span className="ds-info-value" title={details.host || '-'}>{details.host || '-'}</span>
                      </div>
                      <div className="ds-info-row">
                        <span className="ds-info-label">Database</span>
                        <span className="ds-info-value" title={details.database || '-'}>{details.database || '-'}</span>
                      </div>
                    </>
                  )}

                  {['CSV', 'JSON', 'Parquet', 'Excel'].includes(ds.type) && (
                    <div className="ds-info-row">
                      <span className="ds-info-label">File</span>
                      <span className="ds-info-value ds-info-path" title={details.path || 'Auto-generated'}>
                        {details.path ? (details.path.split(/[/\\]/).pop() || details.path) : 'Auto-generated'}
                      </span>
                    </div>
                  )}

                  {ds.type === 'REST API' && (
                    <div className="ds-info-row">
                      <span className="ds-info-label">Endpoint</span>
                      <span className="ds-info-value ds-info-path" title={details.url || '-'}>{details.url || '-'}</span>
                    </div>
                  )}

                  {testResults[ds.id] && (
                    <div className={`ds-test-result ${testResults[ds.id].success ? 'success' : 'error'} ${testResults[ds.id].message === 'Testing...' ? 'pending' : ''}`}>
                      {testResults[ds.id].message}
                    </div>
                  )}
                </div>

                {/* Card footer: action buttons */}
                <div className="ds-card-actions">
                  <button
                    onClick={() => handleTestConnection(ds.id)}
                    disabled={testingId === ds.id}
                    className="btn btn-secondary ds-action-btn"
                  >
                    {testingId === ds.id ? 'Testing…' : 'Test'}
                  </button>
                  <div className="ds-action-spacer" />
                  <button onClick={() => handleOpenDrawer(ds)} className="btn btn-secondary ds-action-btn">Edit</button>
                  <button onClick={() => handleDelete(ds.id)} className="btn btn-danger ds-action-btn">Delete</button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {isDrawerOpen && (
        <div className="drawer-overlay" onClick={(e) => { if (e.target === e.currentTarget) closeDrawer(); }}>
          <div className="drawer-content">
            <div className="drawer-header">
              <h3 className="drawer-title">{isEditing ? 'Edit Data Source' : 'New Data Source'}</h3>
              <button onClick={closeDrawer} className="drawer-close">&times;</button>
            </div>
            
            <div className="drawer-body">
              {formError && <div className="alert alert-error">{formError}</div>}
              
              <form id="ds-form" onSubmit={handleSubmit}>
                <div className="form-group">
                  <label className="form-label">Project</label>
                  <select className="form-input" value={projectId} onChange={(e) => setProjectId(e.target.value)} required>
                    {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Data Source Name</label>
                  <input type="text" className="form-input" value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Production DB" />
                </div>

                <div className="form-group">
                  <label className="form-label">Source Type</label>
                  <select className="form-input" value={type} onChange={(e) => setType(e.target.value)} required>
                    <option value="PostgreSQL">PostgreSQL</option>
                    <option value="MySQL">MySQL</option>
                    <option value="CSV">CSV</option>
                    <option value="JSON">JSON</option>
                    <option value="Parquet">Parquet</option>
                    <option value="Excel">Excel</option>
                    <option value="REST API">REST API</option>
                    <option value="GitHub">GitHub</option>
                  </select>
                </div>

                <div style={{ borderTop: '1px solid #e2e8f0', margin: '24px 0 16px 0', paddingTop: '16px', fontWeight: 600, color: '#0f172a' }}>
                  Connection Configuration
                </div>

                {(type === 'PostgreSQL' || type === 'MySQL') && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Host</label>
                      <input type="text" className="form-input" placeholder="e.g. localhost" required value={dbHost} onChange={e => setDbHost(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Port</label>
                      <input type="number" className="form-input" placeholder="e.g. 5432" required value={dbPort} onChange={e => setDbPort(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Database Name</label>
                      <input type="text" className="form-input" placeholder="e.g. users_db" required value={dbName} onChange={e => setDbName(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Username</label>
                      <input type="text" className="form-input" placeholder="e.g. admin" required value={dbUser} onChange={e => setDbUser(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Password</label>
                      <input type="password" className="form-input" placeholder="Enter password" required={!isEditing} value={dbPass} onChange={e => setDbPass(e.target.value)} />
                      {isEditing && <div className="form-help" style={{ color: '#b91c1c' }}>Please re-enter password to save changes.</div>}
                    </div>
                  </>
                )}

                {['CSV', 'JSON', 'Parquet', 'Excel'].includes(type) && (
                  <div className="form-group">
                    <label className="form-label">File Upload (Optional)</label>
                    <input type="file" className="form-input" accept={type === 'CSV' ? '.csv' : type === 'JSON' ? '.json' : type === 'Parquet' ? '.parquet' : '.xlsx'} onChange={e => setSelectedFile(e.target.files?.[0] || null)} />
                    <div className="form-help">Leave blank to use an auto-generated path for pipeline outputs.</div>
                    {isEditing && filePath && <div className="form-help" style={{ marginTop: '8px', color: '#0f172a' }}>Current path: {filePath}</div>}
                  </div>
                )}

                {type === 'REST API' && (
                  <div className="form-group">
                    <label className="form-label">Endpoint URL</label>
                    <input type="url" className="form-input" placeholder="https://api.example.com/data" required value={apiUrl} onChange={e => setApiUrl(e.target.value)} />
                  </div>
                )}

                {type === 'GitHub' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">GitHub Repository Connection</label>
                      <select className="form-input" value={githubConnectionId} onChange={e => setGithubConnectionId(e.target.value)} required>
                        <option value="" disabled>Select Repository</option>
                        {githubConnections.map(c => <option key={c.id} value={c.id}>{c.repository_name}</option>)}
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Branch</label>
                      <input type="text" className="form-input" placeholder="e.g. main" required value={githubBranch} onChange={e => setGithubBranch(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">File Path</label>
                      <input type="text" className="form-input" placeholder="e.g. data/input.csv" required value={githubFilePath} onChange={e => setGithubFilePath(e.target.value)} />
                      <div className="form-help">The path within the repository for pipeline input/output.</div>
                    </div>
                  </>
                )}
              </form>
            </div>
            
            <div className="drawer-footer">
              <button form="ds-form" type="submit" disabled={submitting} className="btn btn-primary" style={{ width: '100%' }}>
                {submitting ? 'Saving...' : (isEditing ? 'Update Data Source' : 'Create Data Source')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataSources;
