import React, { useEffect, useState, useMemo } from 'react';
import { getPipelines } from '../api/pipelines';
import { listExecutions, getExecutionLogs } from '../api/executions';
import type { ExecutionResponse, ExecutionLogResponse } from '../types';
import './Executions.css';

interface EnrichedExecution extends ExecutionResponse {
  pipelineName: string;
  rowsProcessed?: number;
  dataQuality?: {
    score: number;
    missingValues: number;
    duplicateCount: number;
    status: string;
    missingCols?: string;
  };
  githubData?: {
    repository?: string;
    prNumber?: string;
    status?: string;
  };
}

const Executions: React.FC = () => {
  const [executions, setExecutions] = useState<EnrichedExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [filter, setFilter] = useState('All');
  
  const [selectedExec, setSelectedExec] = useState<EnrichedExecution | null>(null);
  const [selectedLogs, setSelectedLogs] = useState<ExecutionLogResponse[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const pipes = await getPipelines();
        
        const execPromises = pipes.map(p => listExecutions(p.id));
        const execResults = await Promise.all(execPromises);
        
        let allExecutions: EnrichedExecution[] = [];
        
        // Enhance with basic logs data proactively for the table (we'll fetch full logs on click)
        for (let i = 0; i < pipes.length; i++) {
          const pipe = pipes[i];
          const execList = execResults[i];
          
          for (const exec of execList) {
            const enriched: EnrichedExecution = { ...exec, pipelineName: pipe.name };
            if (exec.id && exec.pipeline_id) {
              try {
                const logs = await getExecutionLogs(exec.pipeline_id, exec.id);
                
                // Extract row count
                const loadLog = [...logs].reverse().find(l => l.message?.includes('Loaded ') || l.message?.includes('Extracted '));
                if (loadLog) {
                  const match = loadLog.message?.match(/(\d+) rows/);
                  if (match) enriched.rowsProcessed = parseInt(match[1], 10);
                }

                // Extract DQ
                const dqLog = [...logs].reverse().find(l => l.message?.startsWith('Data Quality:'));
                if (dqLog && dqLog.message) {
                  const missingMatch = dqLog.message.match(/(\d+) missing values/);
                  const duplicateMatch = dqLog.message.match(/(\d+) duplicate/);
                  const scoreMatch = dqLog.message.match(/score (\d+)\/100/);
                  const statusMatch = dqLog.message.match(/\(([^)]+)\)/);
                  const colsMatch = dqLog.message.match(/missing cols: (.*)$/);
                  
                  enriched.dataQuality = {
                    score: scoreMatch ? parseInt(scoreMatch[1], 10) : 0,
                    missingValues: missingMatch ? parseInt(missingMatch[1], 10) : 0,
                    duplicateCount: duplicateMatch ? parseInt(duplicateMatch[1], 10) : 0,
                    status: statusMatch ? statusMatch[1] : 'unknown',
                    missingCols: colsMatch ? colsMatch[1] : undefined
                  };
                }

                // Extract GitHub
                const ghLog = logs.find(l => l.message?.includes('Created PR #'));
                if (ghLog && ghLog.message) {
                  const prMatch = ghLog.message.match(/PR #(\d+)/);
                  enriched.githubData = {
                    prNumber: prMatch ? prMatch[1] : undefined,
                    status: 'Created'
                  };
                }
              } catch (e) {
                // Ignore log fetch errors for the list view
              }
            }
            allExecutions.push(enriched);
          }
        }

        allExecutions.sort((a, b) => new Date(b.started_at || 0).getTime() - new Date(a.started_at || 0).getTime());
        setExecutions(allExecutions);
      } catch (err: any) {
        setError('Failed to load executions.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  const handleSelect = async (exec: EnrichedExecution) => {
    setSelectedExec(exec);
    if (!exec.id || !exec.pipeline_id) return;
    
    setLogsLoading(true);
    try {
      const logs = await getExecutionLogs(exec.pipeline_id, exec.id);
      setSelectedLogs(logs);
    } catch (err) {
      console.error('Failed to fetch detailed logs', err);
    } finally {
      setLogsLoading(false);
    }
  };

  const filtered = useMemo(() => {
    if (filter === 'All') return executions;
    if (filter === 'Completed') return executions.filter(e => e.status?.toLowerCase() === 'completed');
    if (filter === 'Failed') return executions.filter(e => e.status?.toLowerCase() === 'failed');
    return executions;
  }, [executions, filter]);

  const getStatusBadge = (status: string = 'unknown') => {
    const s = status.toLowerCase();
    if (s === 'completed') return <span className="badge badge-success">Completed</span>;
    if (s === 'failed')    return <span className="badge badge-error">Failed</span>;
    if (s === 'running')   return <span className="badge badge-info">Running</span>;
    if (s === 'pending')   return <span className="badge badge-warning">Pending</span>;
    return <span className="badge badge-neutral">{status}</span>;
  };

  const groupLogs = (logs: ExecutionLogResponse[]) => {
    const sections: Record<string, ExecutionLogResponse[]> = {
      'EXTRACT': [],
      'TRANSFORM': [],
      'DATA QUALITY': [],
      'LOAD': [],
      'SYSTEM': []
    };
    
    logs.forEach(log => {
      const msg = log.message || '';
      if (msg.includes('Extracted') || msg.includes('extracting')) sections['EXTRACT'].push(log);
      else if (msg.includes('Transformed') || msg.includes('dropped') || msg.includes('filled')) sections['TRANSFORM'].push(log);
      else if (msg.includes('Data Quality:')) sections['DATA QUALITY'].push(log);
      else if (msg.includes('Loaded') || msg.includes('Created PR') || msg.includes('loading')) sections['LOAD'].push(log);
      else sections['SYSTEM'].push(log);
    });
    
    return sections;
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Run History</h1>
        <p className="page-subtitle">Monitor pipeline executions and inspect their results.</p>
      </div>

      {error && <div style={{ padding: '12px', background: '#fef2f2', color: '#b91c1c', borderRadius: '6px', marginBottom: '20px' }}>{error}</div>}

      <div className="exec-filters">
        {['All', 'Completed', 'Failed'].map(f => (
          <button 
            key={f} 
            className={`exec-filter-btn ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="exec-layout">
        <div className="exec-list-pane">
          {loading ? (
            <div className="empty-state">Loading execution history...</div>
          ) : executions.length === 0 ? (
            <div className="empty-state">
              <h3 className="empty-state-title">No pipeline executions yet</h3>
              <p>Run a pipeline to see execution results here.</p>
            </div>
          ) : (
            <div className="table-container" style={{ flex: 1, overflowY: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Pipeline</th>
                    <th>Status</th>
                    <th>Rows</th>
                    <th>Quality</th>
                    <th>Duration</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(exec => (
                    <tr 
                      key={exec.id} 
                      onClick={() => handleSelect(exec)}
                      className={selectedExec?.id === exec.id ? 'selected' : ''}
                    >
                      <td style={{ fontWeight: 600 }}>{exec.pipelineName}</td>
                      <td>{getStatusBadge(exec.status)}</td>
                      <td>{exec.rowsProcessed ?? '—'}</td>
                      <td>{exec.dataQuality ? `${exec.dataQuality.score}/100` : '—'}</td>
                      <td>{exec.duration ? `${exec.duration}s` : '—'}</td>
                      <td style={{ color: '#64748b' }}>
                        {new Date(exec.started_at || 0).toLocaleString(undefined, {
                          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                        })}
                      </td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                        No executions match the current filter.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {selectedExec && (
          <div className="exec-detail-pane">
            <div className="exec-detail-header">
              <div>
                <h3 className="exec-detail-title">{selectedExec.pipelineName}</h3>
                <div>{getStatusBadge(selectedExec.status)}</div>
              </div>
              <button onClick={() => setSelectedExec(null)} className="exec-detail-close">&times;</button>
            </div>
            
            <div className="exec-detail-body">
              <div className="exec-detail-grid">
                <div className="exec-meta-item">
                  <span className="exec-meta-label">Execution ID</span>
                  <span className="exec-meta-value" style={{ fontFamily: 'monospace', fontSize: '11px' }}>{selectedExec.id}</span>
                </div>
                <div className="exec-meta-item">
                  <span className="exec-meta-label">Triggered By</span>
                  <span className="exec-meta-value">{selectedExec.triggered_by || 'unknown'}</span>
                </div>
                <div className="exec-meta-item">
                  <span className="exec-meta-label">Started</span>
                  <span className="exec-meta-value">{new Date(selectedExec.started_at || 0).toLocaleString()}</span>
                </div>
                <div className="exec-meta-item">
                  <span className="exec-meta-label">Duration</span>
                  <span className="exec-meta-value">{selectedExec.duration ? `${selectedExec.duration}s` : '—'}</span>
                </div>
              </div>

              {selectedExec.dataQuality && (
                <div className="exec-section">
                  <h4 className="exec-section-title">Data Quality</h4>
                  <div className="exec-dq-card">
                    <div className={`exec-dq-score ${selectedExec.dataQuality.score >= 90 ? 'excellent' : selectedExec.dataQuality.score >= 70 ? 'warning' : 'poor'}`}>
                      {selectedExec.dataQuality.score} / 100
                    </div>
                    <div className="exec-dq-row">
                      <span>Missing Values</span>
                      <span style={{ fontWeight: 600 }}>{selectedExec.dataQuality.missingValues}</span>
                    </div>
                    <div className="exec-dq-row">
                      <span>Duplicates</span>
                      <span style={{ fontWeight: 600 }}>{selectedExec.dataQuality.duplicateCount}</span>
                    </div>
                    {selectedExec.dataQuality.missingCols && (
                      <div className="exec-dq-row">
                        <span>Missing Columns</span>
                        <span style={{ fontWeight: 600, color: '#dc2626' }}>{selectedExec.dataQuality.missingCols}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {selectedExec.githubData && (
                <div className="exec-section">
                  <h4 className="exec-section-title">GitHub Output</h4>
                  <div className="exec-gh-card">
                    <div className="exec-dq-row">
                      <span>Pull Request</span>
                      <span style={{ fontWeight: 600 }}>#{selectedExec.githubData.prNumber}</span>
                    </div>
                    <div className="exec-dq-row">
                      <span>Status</span>
                      <span style={{ fontWeight: 600 }}>{selectedExec.githubData.status}</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="exec-section">
                <h4 className="exec-section-title">Execution Logs</h4>
                {logsLoading ? (
                  <div style={{ color: '#64748b', fontSize: '13px' }}>Loading logs...</div>
                ) : (
                  <div className="exec-logs-container">
                    {(() => {
                      const groups = groupLogs(selectedLogs);
                      return ['SYSTEM', 'EXTRACT', 'TRANSFORM', 'DATA QUALITY', 'LOAD'].map(groupName => {
                        const logs = groups[groupName];
                        if (!logs || logs.length === 0) return null;
                        return (
                          <div key={groupName} style={{ marginBottom: '16px' }}>
                            <div style={{ color: '#94a3b8', fontSize: '10px', fontWeight: 700, marginBottom: '8px' }}>[{groupName}]</div>
                            {logs.map(log => (
                              <div key={log.id} className={`exec-log-line ${log.level?.toLowerCase() || ''}`}>
                                <span style={{ color: '#64748b' }}>{new Date(log.timestamp || 0).toLocaleTimeString()}</span> &bull; {log.message}
                              </div>
                            ))}
                          </div>
                        );
                      });
                    })()}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Executions;
