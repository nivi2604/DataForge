import React, { useEffect, useState } from 'react';
import { getWorkspaces } from '../api/workspaces';
import { getProjects, createProject } from '../api/projects';
import { getPipelines, createPipeline, deletePipeline } from '../api/pipelines';
import type { Workspace, Project, Pipeline } from '../types';
import { useNavigate } from 'react-router-dom';

const Projects: React.FC = () => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWsId, setSelectedWsId] = useState('');
  
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjId, setSelectedProjId] = useState('');
  
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  const [pipeName, setPipeName] = useState('');
  const [pipeDescription, setPipeDescription] = useState('');
  const [pipeSubmitting, setPipeSubmitting] = useState(false);
  const [pipeFormError, setPipeFormError] = useState('');

  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        const data = await getWorkspaces();
        setWorkspaces(data);
        if (data.length > 0) {
          setSelectedWsId(data[0].id);
        }
      } catch (err) {
        console.error("Failed to load workspaces", err);
      }
    };
    fetchWorkspaces();
  }, []);

  useEffect(() => {
    const fetchProjects = async () => {
      if (!selectedWsId) return;
      try {
        setLoading(true);
        const data = await getProjects(selectedWsId);
        setProjects(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load projects.');
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, [selectedWsId]);

  useEffect(() => {
    const fetchPipelines = async () => {
      if (!selectedProjId) return;
      try {
        setLoading(true);
        const data = await getPipelines(selectedProjId);
        setPipelines(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load pipelines.');
      } finally {
        setLoading(false);
      }
    };
    fetchPipelines();
  }, [selectedProjId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWsId) {
      setFormError('Please select a workspace first.');
      return;
    }
    
    setFormError('');
    setSubmitting(true);
    
    try {
      const newProj = await createProject({ workspace_id: selectedWsId, name, description });
      setProjects([...projects, newProj]);
      setName('');
      setDescription('');
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create project.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreatePipeline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjId) return;
    
    setPipeFormError('');
    setPipeSubmitting(true);
    
    try {
      const newPipe = await createPipeline({ project_id: selectedProjId, name: pipeName, description: pipeDescription });
      setPipelines([...pipelines, newPipe]);
      setPipeName('');
      setPipeDescription('');
    } catch (err: any) {
      setPipeFormError(err.response?.data?.detail || 'Failed to create pipeline.');
    } finally {
      setPipeSubmitting(false);
    }
  };

  const handleDeletePipeline = async (id: string) => {
    if (!confirm('Are you sure you want to delete this pipeline?')) return;
    try {
      await deletePipeline(id);
      setPipelines(pipelines.filter(p => p.id !== id));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete pipeline.');
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Projects</h1>
        <select 
          value={selectedWsId} 
          onChange={(e) => setSelectedWsId(e.target.value)}
          className="form-select" style={{ width: '250px' }}
        >
          <option value="" disabled>Select Workspace</option>
          {workspaces.map(ws => (
            <option key={ws.id} value={ws.id}>{ws.name}</option>
          ))}
        </select>
      </div>
      
      {error && <div className="form-error" style={{ marginTop: '20px' }}>{error}</div>}
      
      {!selectedWsId ? (
        <div className="empty-state">
          Please select a workspace to view projects.
        </div>
      ) : (
        <div style={{ display: 'flex', gap: '24px' }}>
          <div style={{ flex: 2 }}>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Created At</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr><td colSpan={4} style={{ padding: '20px', textAlign: 'center' }}>Loading projects...</td></tr>
                  ) : projects.length === 0 ? (
                    <tr><td colSpan={4} style={{ padding: '20px', textAlign: 'center' }}>No projects found in this workspace.</td></tr>
                  ) : (
                    projects.map(proj => (
                      <tr key={proj.id}>
                        <td>
                          <strong>{proj.name}</strong>
                          {proj.description && <div style={{ fontSize: '12px', color: '#7f8c8d' }}>{proj.description}</div>}
                        </td>
                        <td>
                          <span className="badge badge-info">
                            {proj.status || 'Active'}
                          </span>
                        </td>
                        <td>{proj.created_at ? new Date(proj.created_at).toLocaleDateString() : '-'}</td>
                        <td style={{ textAlign: 'right' }}>
                          <button onClick={() => setSelectedProjId(proj.id)} className="btn btn-secondary">Open</button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div style={{ flex: 1 }}>
            <div className="card"><div className="card-body">
              <h3 className="card-title" style={{ marginBottom: '16px' }}>Create Project</h3>
              
              {formError && <div style={{ color: 'red', marginBottom: '10px', fontSize: '14px' }}>{formError}</div>}
              
              <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column' }}>
                <div className="form-group">
                  <label className="form-label">Name</label>
                  <input 
                    type="text" 
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea 
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={3}
                    className="form-input"
                  />
                </div>
                <button 
                  type="submit" 
                  disabled={submitting || !selectedWsId}
                  className="btn btn-primary"
                >
                  {submitting ? 'Creating...' : 'Create Project'}
                </button>
              </form>
            </div></div>
          </div>
        </div>
      )}

      {selectedProjId && (
        <div style={{ marginTop: '40px' }}>
          <h2 className="page-title" style={{ marginBottom: '24px' }}>Pipelines</h2>
          <div style={{ display: 'flex', gap: '20px' }}>
            <div style={{ flex: 2 }}>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Status</th>
                      <th>Created</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr><td colSpan={4} style={{ padding: '20px', textAlign: 'center' }}>Loading pipelines...</td></tr>
                    ) : pipelines.length === 0 ? (
                      <tr><td colSpan={4} style={{ padding: '20px', textAlign: 'center' }}>No pipelines found.</td></tr>
                    ) : (
                      pipelines.map(pipe => (
                        <tr key={pipe.id}>
                          <td>
                            <strong>{pipe.name}</strong>
                            {pipe.description && <div style={{ fontSize: '12px', color: '#7f8c8d' }}>{pipe.description}</div>}
                          </td>
                          <td>{pipe.status || '-'}</td>
                          <td>{pipe.created_at ? new Date(pipe.created_at).toLocaleDateString() : '-'}</td>
                          <td style={{ textAlign: 'right' }}>
                            <button onClick={() => navigate(`/projects/${selectedProjId}/pipelines/${pipe.id}`)} className="btn btn-secondary">Open</button>
                            <button onClick={() => handleDeletePipeline(pipe.id)} className="btn btn-danger">Delete</button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ flex: 1 }}>
              <div className="card"><div className="card-body">
                <h3 className="card-title" style={{ marginBottom: '16px' }}>Create Pipeline</h3>
                
                {pipeFormError && <div style={{ color: 'red', marginBottom: '10px', fontSize: '14px' }}>{pipeFormError}</div>}
                
                <form onSubmit={handleCreatePipeline} style={{ display: 'flex', flexDirection: 'column' }}>
                  <div className="form-group">
                    <label className="form-label">Name</label>
                    <input 
                      type="text" 
                      value={pipeName}
                      onChange={(e) => setPipeName(e.target.value)}
                      required
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Description</label>
                    <textarea 
                      value={pipeDescription}
                      onChange={(e) => setPipeDescription(e.target.value)}
                      rows={3}
                      className="form-input"
                    />
                  </div>
                  <button 
                    type="submit" 
                    disabled={pipeSubmitting || !selectedProjId}
                    className="btn btn-primary"
                  >
                    {pipeSubmitting ? 'Creating...' : 'Create Pipeline'}
                  </button>
                </form>
              </div></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Projects;
