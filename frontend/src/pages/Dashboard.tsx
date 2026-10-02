import React, { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { getPipelines } from '../api/pipelines';
import { getDataSources } from '../api/dataSources';
import { listExecutions, getExecutionLogs } from '../api/executions';
import { listConnections, listPullRequests, listPRValidations } from '../api/github';
import type { Pipeline, ExecutionResponse } from '../types';
import './Dashboard.css';

interface DashboardStats {
  totalPipelines: number;
  totalDataSources: number;
  successfulExecutions: number;
  failedExecutions: number;
}

interface EnrichedExecution extends ExecutionResponse {
  pipelineName: string;
  rowsProcessed?: number | string;
  dataQuality?: {
    score: number;
    missingValues: number;
    duplicateCount: number;
    status: string;
    missingCols?: string;
  };
}

/** Return the CSS class for a DQ score */
function dqClass(score: number): string {
  if (score >= 90) return 'excellent';
  if (score >= 75) return 'good';
  if (score >= 50) return 'warning';
  return 'critical';
}

const Dashboard: React.FC = () => {
  const [profile, setProfile] = useState<any>(null);
  const [stats, setStats] = useState<DashboardStats>({
    totalPipelines: 0,
    totalDataSources: 0,
    successfulExecutions: 0,
    failedExecutions: 0
  });

  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [recentExecutions, setRecentExecutions] = useState<EnrichedExecution[]>([]);

  const [githubStats, setGithubStats] = useState<{
    totalConnections: number;
    totalPRs: number;
    validations: any[];
  }>({ totalConnections: 0, totalPRs: 0, validations: [] });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [profileRes, pipes, sources] = await Promise.all([
          apiClient.get('/auth/me'),
          getPipelines(),
          getDataSources()
        ]);

        setProfile(profileRes.data);
        setPipelines(pipes);

        // Fetch executions for all pipelines in parallel
        const execPromises = pipes.map(p => listExecutions(p.id));
        const execResults = await Promise.all(execPromises);
        let allExecutions: EnrichedExecution[] = [];

        execResults.forEach((execList, idx) => {
          const pName = pipes[idx].name;
          const enriched = execList.map(e => ({ ...e, pipelineName: pName }));
          allExecutions = allExecutions.concat(enriched);
        });

        // Sort by started_at desc (most recent first)
        allExecutions.sort((a, b) => {
          return new Date(b.started_at || 0).getTime() - new Date(a.started_at || 0).getTime();
        });

        // Counts come directly from the real execution records — no fabrication
        const success = allExecutions.filter(e => e.status === 'completed').length;
        const failed  = allExecutions.filter(e => e.status === 'failed').length;

        setStats({
          totalPipelines: pipes.length,
          totalDataSources: sources.length,
          successfulExecutions: success,
          failedExecutions: failed
        });

        // Take top 5 recent executions and fetch their logs for DQ & rows processed
        const top5 = allExecutions.slice(0, 5);
        for (const exec of top5) {
          if (exec.pipeline_id && exec.id) {
            try {
              const logs = await getExecutionLogs(exec.pipeline_id, exec.id);

              // rows processed — look for "Extracted N rows" or "Loaded N rows"
              const loadLog = [...logs].reverse().find(
                l => l.message?.includes('Loaded ') || l.message?.includes('Extracted ')
              );
              if (loadLog) {
                const match = loadLog.message?.match(/(\d+) rows/);
                if (match) exec.rowsProcessed = parseInt(match[1], 10);
              }

              // Data Quality log format:
              // "Data Quality: X rows, Y missing values, Z duplicate, score S/100 (status)"
              const dqLog = [...logs].reverse().find(l => l.message?.startsWith('Data Quality:'));
              if (dqLog?.message) {
                const missingMatch   = dqLog.message.match(/(\d+) missing values/);
                const duplicateMatch = dqLog.message.match(/(\d+) duplicate/);
                const scoreMatch     = dqLog.message.match(/score (\d+)\/100/);
                const statusMatch    = dqLog.message.match(/\(([^)]+)\)/);
                const colsMatch      = dqLog.message.match(/missing cols: (.*)$/);

                exec.dataQuality = {
                  score:          scoreMatch     ? parseInt(scoreMatch[1], 10)     : 0,
                  missingValues:  missingMatch   ? parseInt(missingMatch[1], 10)   : 0,
                  duplicateCount: duplicateMatch ? parseInt(duplicateMatch[1], 10) : 0,
                  status:         statusMatch    ? statusMatch[1]                  : 'unknown',
                  missingCols:    colsMatch      ? colsMatch[1]                    : undefined
                };
              }
            } catch (err) {
              console.error('Failed to fetch logs for execution', exec.id, err);
            }
          }
        }

        setRecentExecutions(top5);

        // GitHub stats — failures are swallowed so they don't break the dashboard
        try {
          const connections = await listConnections();
          let prCount = 0;
          for (const conn of connections) {
            const prs = await listPullRequests(conn.id);
            prCount += prs.length;
          }
          const validations = await listPRValidations();
          setGithubStats({
            totalConnections: connections.length,
            totalPRs: prCount,
            validations: validations.slice(0, 3)
          });
        } catch (ghErr) {
          console.error('Failed to fetch github stats', ghErr);
        }

      } catch (err) {
        console.error('Failed to fetch dashboard data', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div className="loading-spinner" />;

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="empty-state" style={{ color: '#ef4444', paddingTop: '60px' }}>
          {error}
        </div>
      </div>
    );
  }

  // Use the most recent execution that has DQ data
  const latestDQExec  = recentExecutions.find(e => e.dataQuality);
  const latestDQ      = latestDQExec?.dataQuality;
  const dqStatusClass = latestDQ ? dqClass(latestDQ.score) : '';

  return (
    <div className="dashboard-container">

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="dashboard-header">
        <div>
          <h1 className="dashboard-title">Dashboard</h1>
          <p className="dashboard-subtitle">
            Welcome back, {profile?.first_name || 'User'}. Here's what's happening today.
          </p>
        </div>
      </div>

      {/* ── Summary cards ───────────────────────────────────────────────────── */}
      <div className="metrics-grid">
        <div className="metric-card info">
          <div className="metric-title">Total Pipelines</div>
          <div className="metric-value">{stats.totalPipelines}</div>
          <div className="metric-trend">Configured in your workspaces</div>
        </div>
        <div className="metric-card info">
          <div className="metric-title">Data Sources</div>
          <div className="metric-value">{stats.totalDataSources}</div>
          <div className="metric-trend">Active connections</div>
        </div>
        <div className="metric-card good">
          <div className="metric-title">Successful Executions</div>
          <div className="metric-value">{stats.successfulExecutions}</div>
          <div className="metric-trend good">All time successful runs</div>
        </div>
        <div className={`metric-card ${stats.failedExecutions > 0 ? 'bad' : 'good'}`}>
          <div className="metric-title">Failed Executions</div>
          <div className="metric-value">{stats.failedExecutions}</div>
          <div className={`metric-trend ${stats.failedExecutions > 0 ? 'bad' : 'good'}`}>
            {stats.failedExecutions > 0 ? 'Action might be required' : 'No failures recorded'}
          </div>
        </div>
      </div>

      {/* ── Two-column layout ────────────────────────────────────────────────── */}
      <div className="dashboard-layout">

        {/* Left column — tables */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* Recent Executions */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Recent Pipeline Executions</h2>
            </div>
            <div className="card-body">
              {recentExecutions.length === 0 ? (
                <div className="empty-state">No recent executions found.</div>
              ) : (
                <table className="data-table exec-table">
                  <colgroup>
                    <col className="col-pipeline" />
                    <col className="col-status" />
                    <col className="col-rows" />
                    <col className="col-duration" />
                    <col className="col-timestamp" />
                  </colgroup>
                  <thead>
                    <tr>
                      <th>Pipeline</th>
                      <th>Status</th>
                      <th>Rows</th>
                      <th>Duration</th>
                      <th>When</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentExecutions.map(exec => (
                      <tr key={exec.id}>
                        <td
                          title={exec.pipelineName}
                          style={{ fontWeight: 500, color: '#0f172a', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                        >
                          {exec.pipelineName}
                        </td>
                        <td>
                          <span className={`badge ${exec.status?.toLowerCase() || 'unknown'}`}>
                            {exec.status || 'unknown'}
                          </span>
                        </td>
                        <td style={{ color: '#64748b', textAlign: 'right' }}>
                          {exec.rowsProcessed != null ? exec.rowsProcessed.toLocaleString() : '—'}
                        </td>
                        <td style={{ color: '#64748b', textAlign: 'right' }}>
                          {exec.duration != null && exec.duration > 0 ? `${exec.duration}s` : '—'}
                        </td>
                        <td style={{ color: '#94a3b8', fontSize: '11.5px' }}>
                          {exec.started_at
                            ? new Date(exec.started_at).toLocaleString(undefined, {
                                month: 'short', day: 'numeric',
                                hour: '2-digit', minute: '2-digit'
                              })
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Pipeline Overview */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Pipeline Overview</h2>
            </div>
            <div className="card-body">
              {pipelines.length === 0 ? (
                <div className="empty-state">No pipelines configured.</div>
              ) : (
                <table className="data-table pipe-table">
                  <colgroup>
                    <col className="col-name" />
                    <col className="col-version" />
                    <col className="col-status" />
                    <col className="col-date" />
                  </colgroup>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Ver.</th>
                      <th>Status</th>
                      <th>Updated</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pipelines.slice(0, 6).map(pipe => (
                      <tr key={pipe.id}>
                        <td
                          title={pipe.name}
                          style={{ fontWeight: 500, color: '#0f172a' }}
                        >
                          {pipe.name}
                        </td>
                        <td style={{ color: '#94a3b8' }}>v{pipe.version || '1'}</td>
                        <td>
                          <span className={`badge ${pipe.status?.toLowerCase() || 'active'}`}>
                            {pipe.status || 'Active'}
                          </span>
                        </td>
                        <td style={{ color: '#94a3b8', fontSize: '11.5px' }}>
                          {pipe.updated_at || pipe.created_at
                            ? new Date(pipe.updated_at || pipe.created_at || '').toLocaleDateString()
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>

        {/* Right column — DQ + GitHub */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* Data Quality Summary */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Data Quality</h2>
            </div>
            <div className="card-body padded">
              {latestDQ ? (
                <>
                  {/* Score + status in a horizontal row so nothing is cut off */}
                  <div className="dq-score-block">
                    <div className={`dq-score-number ${dqStatusClass}`}>
                      {latestDQ.score}
                    </div>
                    <div className="dq-score-meta">
                      <span className="dq-score-label">Overall Score</span>
                      <span className={`dq-score-badge ${dqStatusClass}`}>
                        {latestDQ.status.charAt(0).toUpperCase() + latestDQ.status.slice(1)}
                      </span>
                    </div>
                  </div>

                  <ul className="quality-list">
                    <li className="quality-item">
                      <span className="quality-label">Missing Values</span>
                      <span className="quality-value"
                        style={{ color: latestDQ.missingValues > 0 ? '#ef4444' : '#0f172a' }}>
                        {latestDQ.missingValues}
                      </span>
                    </li>
                    <li className="quality-item">
                      <span className="quality-label">Duplicate Rows</span>
                      <span className="quality-value"
                        style={{ color: latestDQ.duplicateCount > 0 ? '#f59e0b' : '#0f172a' }}>
                        {latestDQ.duplicateCount}
                      </span>
                    </li>
                    {latestDQ.missingCols && (
                      <li className="quality-item">
                        <span className="quality-label">Missing Cols</span>
                        <span className="quality-value" style={{ color: '#ef4444', fontSize: '11.5px' }}>
                          {latestDQ.missingCols}
                        </span>
                      </li>
                    )}
                  </ul>

                  <p className="dq-footnote">
                    From pipeline &ldquo;{latestDQExec?.pipelineName}&rdquo;
                    {latestDQExec?.started_at && (
                      <> &bull; {new Date(latestDQExec.started_at).toLocaleDateString(undefined, {
                        month: 'short', day: 'numeric'
                      })}</>
                    )}
                  </p>
                </>
              ) : (
                <div className="empty-state">No Data Quality results found.</div>
              )}
            </div>
          </div>

          {/* GitHub Integration */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">GitHub Integration</h2>
            </div>
            <div className="card-body padded">
              <ul className="quality-list">
                <li className="quality-item">
                  <span className="quality-label">Active Connections</span>
                  <span className="quality-value">{githubStats.totalConnections}</span>
                </li>
                <li className="quality-item">
                  <span className="quality-label">Open Pull Requests</span>
                  <span className="quality-value">{githubStats.totalPRs}</span>
                </li>
              </ul>

              {githubStats.validations.length > 0 && (
                <div style={{ marginTop: '14px' }}>
                  <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>
                    Recent PR Validations
                  </div>
                  {githubStats.validations.map(val => (
                    <div key={val.id} style={{ padding: '9px 10px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '7px', marginBottom: '6px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
                        <span style={{ fontWeight: 600, fontSize: '12.5px', color: '#0f172a' }}>PR #{val.pr_number}</span>
                        <span className={`badge ${val.status?.toLowerCase()}`}>{val.status}</span>
                      </div>
                      <div style={{ fontSize: '11.5px', color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {val.repository_name} &bull; {val.head_branch}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Dashboard;
