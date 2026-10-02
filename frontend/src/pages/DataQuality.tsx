import React, { useEffect, useState } from 'react';
import { getPipelines } from '../api/pipelines';
import { listExecutions, getExecutionLogs } from '../api/executions';
import type { ExecutionResponse } from '../types';
import './DataQuality.css';

interface EnrichedDQExecution extends ExecutionResponse {
  pipelineName: string;
  rowsProcessed?: number;
  dataQuality: {
    score: number;
    missingValues: number;
    duplicateCount: number;
    status: string;
    missingCols?: string;
  };
  githubData?: {
    prNumber?: string;
    status?: string;
  };
}

const DataQuality: React.FC = () => {
  const [dqExecutions, setDqExecutions] = useState<EnrichedDQExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [selectedExec, setSelectedExec] = useState<EnrichedDQExecution | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const pipes = await getPipelines();
        
        const execPromises = pipes.map(p => listExecutions(p.id));
        const execResults = await Promise.all(execPromises);
        
        let allDqExecutions: EnrichedDQExecution[] = [];
        
        for (let i = 0; i < pipes.length; i++) {
          const pipe = pipes[i];
          const execList = execResults[i];
          
          for (const exec of execList) {
            // Only fetch logs for completed executions to find DQ stats
            if (exec.id && exec.pipeline_id && exec.status === 'completed') {
              try {
                const logs = await getExecutionLogs(exec.pipeline_id, exec.id);
                
                const dqLog = [...logs].reverse().find(l => l.message?.startsWith('Data Quality:'));
                
                if (dqLog && dqLog.message) {
                  const missingMatch = dqLog.message.match(/(\d+) missing values/);
                  const duplicateMatch = dqLog.message.match(/(\d+) duplicate/);
                  const scoreMatch = dqLog.message.match(/score (\d+)\/100/);
                  const statusMatch = dqLog.message.match(/\(([^)]+)\)/);
                  const colsMatch = dqLog.message.match(/missing cols: (.*)$/);
                  
                  const dq = {
                    score: scoreMatch ? parseInt(scoreMatch[1], 10) : 0,
                    missingValues: missingMatch ? parseInt(missingMatch[1], 10) : 0,
                    duplicateCount: duplicateMatch ? parseInt(duplicateMatch[1], 10) : 0,
                    status: statusMatch ? statusMatch[1] : 'unknown',
                    missingCols: colsMatch ? colsMatch[1] : undefined
                  };

                  let rowsProcessed;
                  const loadLog = [...logs].reverse().find(l => l.message?.includes('Loaded ') || l.message?.includes('Extracted '));
                  if (loadLog) {
                    const rMatch = loadLog.message?.match(/(\d+) rows/);
                    if (rMatch) rowsProcessed = parseInt(rMatch[1], 10);
                  }

                  let githubData;
                  const ghLog = logs.find(l => l.message?.includes('Created PR #'));
                  if (ghLog && ghLog.message) {
                    const prMatch = ghLog.message.match(/PR #(\d+)/);
                    githubData = {
                      prNumber: prMatch ? prMatch[1] : undefined,
                      status: 'Created'
                    };
                  }

                  allDqExecutions.push({
                    ...exec,
                    pipelineName: pipe.name,
                    dataQuality: dq,
                    rowsProcessed,
                    githubData
                  });
                }
              } catch (e) {
                // skip failed log fetches
              }
            }
          }
        }

        allDqExecutions.sort((a, b) => new Date(b.started_at || 0).getTime() - new Date(a.started_at || 0).getTime());
        setDqExecutions(allDqExecutions);
      } catch (err: any) {
        setError('Failed to load data quality results.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  const getScoreClass = (score: number) => {
    if (score >= 90) return 'excellent';
    if (score >= 70) return 'warning';
    return 'poor';
  };

  const getStatusText = (score: number) => {
    if (score === 100) return '✓ PASSED';
    if (score >= 70) return '⚠ WARNING';
    return '✕ FAILED';
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Data Quality</h1>
        <p className="page-subtitle">Inspect the quality checks performed during pipeline execution.</p>
      </div>

      {error && <div style={{ padding: '12px', background: '#fef2f2', color: '#b91c1c', borderRadius: '6px', marginBottom: '20px' }}>{error}</div>}

      <div className="dq-layout">
        <div className="dq-list-pane">
          {loading ? (
            <div className="empty-state">Loading data quality results...</div>
          ) : dqExecutions.length === 0 ? (
            <div className="empty-state">
              <h3 className="empty-state-title">No Data Quality results yet</h3>
              <p>Run a pipeline with a Data Quality step to generate a quality report.</p>
            </div>
          ) : (
            <div className="table-container" style={{ flex: 1, overflowY: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Pipeline</th>
                    <th>Execution Time</th>
                    <th>Quality Score</th>
                    <th>Rows</th>
                  </tr>
                </thead>
                <tbody>
                  {dqExecutions.map(exec => (
                    <tr 
                      key={exec.id} 
                      onClick={() => setSelectedExec(exec)}
                      className={selectedExec?.id === exec.id ? 'selected' : ''}
                    >
                      <td style={{ fontWeight: 600 }}>{exec.pipelineName}</td>
                      <td style={{ color: '#64748b' }}>
                        {new Date(exec.started_at || 0).toLocaleString()}
                      </td>
                      <td>
                        <span style={{ fontWeight: 600, color: exec.dataQuality.score >= 90 ? '#059669' : exec.dataQuality.score >= 70 ? '#d97706' : '#dc2626' }}>
                          {exec.dataQuality.score} / 100
                        </span>
                      </td>
                      <td>{exec.rowsProcessed ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {selectedExec && (
          <div className="dq-detail-pane">
            <div className="dq-score-card">
              <h3 className="dq-score-title">Overall Quality</h3>
              <div className={`dq-score-value ${getScoreClass(selectedExec.dataQuality.score)}`}>
                {selectedExec.dataQuality.score} / 100
              </div>
              <div className={`badge ${getScoreClass(selectedExec.dataQuality.score)}`}>
                {getStatusText(selectedExec.dataQuality.score)}
              </div>
            </div>

            <div className="dq-card">
              <h3 className="dq-card-title">Quality Checks</h3>
              <div className="dq-check-row">
                <span className="dq-check-label">Missing Values</span>
                <span className={`dq-check-value ${selectedExec.dataQuality.missingValues === 0 ? 'pass' : 'fail'}`}>
                  {selectedExec.dataQuality.missingValues === 0 ? '✓ Passed (0)' : `✕ Failed (${selectedExec.dataQuality.missingValues})`}
                </span>
              </div>
              <div className="dq-check-row">
                <span className="dq-check-label">Duplicates</span>
                <span className={`dq-check-value ${selectedExec.dataQuality.duplicateCount === 0 ? 'pass' : 'fail'}`}>
                  {selectedExec.dataQuality.duplicateCount === 0 ? '✓ Passed (0)' : `✕ Failed (${selectedExec.dataQuality.duplicateCount})`}
                </span>
              </div>
              <div className="dq-check-row">
                <span className="dq-check-label">Required Columns</span>
                <span className={`dq-check-value ${!selectedExec.dataQuality.missingCols ? 'pass' : 'fail'}`}>
                  {!selectedExec.dataQuality.missingCols ? '✓ Passed' : `✕ Missing: ${selectedExec.dataQuality.missingCols}`}
                </span>
              </div>
            </div>

            <div className="dq-card">
              <h3 className="dq-card-title">Pipeline Context</h3>
              <div className="dq-meta-grid">
                <div className="dq-meta-item">
                  <div className="dq-meta-label">Pipeline</div>
                  <div className="dq-meta-value">{selectedExec.pipelineName}</div>
                </div>
                <div className="dq-meta-item">
                  <div className="dq-meta-label">Execution</div>
                  <div className="dq-meta-value" style={{ textTransform: 'capitalize' }}>{selectedExec.status}</div>
                </div>
                <div className="dq-meta-item">
                  <div className="dq-meta-label">Rows Processed</div>
                  <div className="dq-meta-value">{selectedExec.rowsProcessed ?? 'Unknown'}</div>
                </div>
                <div className="dq-meta-item">
                  <div className="dq-meta-label">Execution ID</div>
                  <div className="dq-meta-value" style={{ fontFamily: 'monospace', fontSize: '10px' }}>{selectedExec.id}</div>
                </div>
              </div>
            </div>

            {selectedExec.githubData && (
              <div className="dq-card">
                <h3 className="dq-card-title">GitHub Output</h3>
                <div className="dq-meta-grid">
                  <div className="dq-meta-item">
                    <div className="dq-meta-label">Pull Request</div>
                    <div className="dq-meta-value">#{selectedExec.githubData.prNumber}</div>
                  </div>
                  <div className="dq-meta-item">
                    <div className="dq-meta-label">Status</div>
                    <div className="dq-meta-value">{selectedExec.githubData.status}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DataQuality;
