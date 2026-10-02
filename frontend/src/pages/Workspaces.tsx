import React, { useEffect, useState } from 'react';
import { getOrganizations } from '../api/organizations';
import { getWorkspaces, createWorkspace } from '../api/workspaces';
import type { Organization, Workspace } from '../types';

const Workspaces: React.FC = () => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState('');
  
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  useEffect(() => {
    const fetchOrgs = async () => {
      try {
        const data = await getOrganizations();
        setOrganizations(data);
        if (data.length > 0) {
          setSelectedOrgId(data[0].id);
        }
      } catch (err) {
        console.error("Failed to load orgs", err);
      }
    };
    fetchOrgs();
  }, []);

  useEffect(() => {
    const fetchWorkspaces = async () => {
      if (!selectedOrgId) return;
      try {
        setLoading(true);
        const data = await getWorkspaces(selectedOrgId);
        setWorkspaces(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load workspaces.');
      } finally {
        setLoading(false);
      }
    };
    fetchWorkspaces();
  }, [selectedOrgId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrgId) {
      setFormError('Please select an organization first.');
      return;
    }
    
    setFormError('');
    setSubmitting(true);
    
    try {
      const newWs = await createWorkspace({ organization_id: selectedOrgId, name, description });
      setWorkspaces([...workspaces, newWs]);
      setName('');
      setDescription('');
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create workspace.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Workspaces</h1>
        <select 
          value={selectedOrgId} 
          onChange={(e) => setSelectedOrgId(e.target.value)}
          className="form-select" style={{ width: '250px' }}
        >
          <option value="" disabled>Select Organization</option>
          {organizations.map(org => (
            <option key={org.id} value={org.id}>{org.name}</option>
          ))}
        </select>
      </div>
      
      {error && <div className="form-error" style={{ marginTop: '20px' }}>{error}</div>}
      
      {!selectedOrgId ? (
        <div className="empty-state">
          Please select an organization to view workspaces.
        </div>
      ) : (
        <div style={{ display: 'flex', gap: '24px' }}>
          <div style={{ flex: 2 }}>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Description</th>
                    <th>Created At</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr><td colSpan={3} style={{ padding: '20px', textAlign: 'center' }}>Loading workspaces...</td></tr>
                  ) : workspaces.length === 0 ? (
                    <tr><td colSpan={3} style={{ padding: '20px', textAlign: 'center' }}>No workspaces found in this organization.</td></tr>
                  ) : (
                    workspaces.map(ws => (
                      <tr key={ws.id}>
                        <td><strong>{ws.name}</strong></td>
                        <td>{ws.description || '-'}</td>
                        <td>{ws.created_at ? new Date(ws.created_at).toLocaleDateString() : '-'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div style={{ flex: 1 }}>
            <div className="card"><div className="card-body">
              <h3 className="card-title" style={{ marginBottom: '16px' }}>Create Workspace</h3>
              
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
                  disabled={submitting || !selectedOrgId}
                  className="btn btn-primary"
                >
                  {submitting ? 'Creating...' : 'Create Workspace'}
                </button>
              </form>
            </div></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Workspaces;
