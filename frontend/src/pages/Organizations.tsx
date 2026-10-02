import React, { useEffect, useState } from 'react';
import { getOrganizations, createOrganization } from '../api/organizations';
import type { Organization } from '../types';

const Organizations: React.FC = () => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  const fetchOrgs = async () => {
    try {
      setLoading(true);
      const data = await getOrganizations();
      setOrganizations(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load organizations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrgs();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    
    try {
      const newOrg = await createOrganization({ name, description });
      setOrganizations([...organizations, newOrg]);
      setName('');
      setDescription('');
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create organization.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Organizations</h1>
      </div>
      
      {error && <div className="form-error">{error}</div>}
      
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
                  <tr><td colSpan={3} style={{ padding: '20px', textAlign: 'center' }}>Loading organizations...</td></tr>
                ) : organizations.length === 0 ? (
                  <tr><td colSpan={3} style={{ padding: '20px', textAlign: 'center' }}>No organizations found.</td></tr>
                ) : (
                  organizations.map(org => (
                    <tr key={org.id}>
                      <td><strong>{org.name}</strong></td>
                      <td>{org.description || '-'}</td>
                      <td>{org.created_at ? new Date(org.created_at).toLocaleDateString() : '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <div className="card"><div className="card-body">
            <h3 className="card-title" style={{ marginBottom: '16px' }}>Create Organization</h3>
            
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
                disabled={submitting}
                className="btn btn-primary"
              >
                {submitting ? 'Creating...' : 'Create Organization'}
              </button>
            </form>
          </div></div>
        </div>
      </div>
    </div>
  );
};

export default Organizations;
