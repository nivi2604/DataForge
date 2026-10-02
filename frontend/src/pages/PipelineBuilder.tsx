import React, { useState, useCallback, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Handle,
  Position,
} from 'reactflow';
import type {
  Node,
  Edge,
  NodeChange,
  EdgeChange,
  Connection,
  NodeProps,
} from 'reactflow';
import 'reactflow/dist/style.css';
import './PipelineBuilder.css';

import { 
  getPipeline, getPipelineNodes, createPipelineNode, updatePipelineNode, 
  getPipelineVersions, createPipelineVersion, getPipelineVersionDiff, 
  rollbackPipelineVersion, pushPipelineVersionToGithub 
} from '../api/pipelines';
import { executePipeline, getExecutionLogs, listExecutions } from '../api/executions';
import { getDataSources } from '../api/dataSources';
import { getSchedules, createSchedule, updateSchedule, deleteSchedule } from '../api/schedules';
import { listConnections } from '../api/github';
import type { GithubConnectionResponse } from '../api/github';
import type { Pipeline, DataSource, ExecutionLogResponse, ScheduleResponse, PipelineVersion, ExecutionResponse } from '../types';

const defaultViewport = { x: 0, y: 0, zoom: 1.1 };

const CustomNode = ({ data, selected }: NodeProps) => {
  const { node_type, sequence_index, configuration, dataSources, executionFeedback } = data;
  
  const ds = dataSources?.find((d: any) => d.id === configuration?.data_source_id);
  
  let configSummary = null;
  if (node_type === 'extract' || node_type === 'load') {
    if (ds) {
      if (ds.type === 'GitHub' && ds.connection_details) {
         try {
           const details = JSON.parse(ds.connection_details);
           configSummary = <div className="node-summary">{ds.type} • {details.branch}</div>;
         } catch(e) {}
      } else {
         configSummary = <div className="node-summary">{ds.name}</div>;
      }
    } else {
      configSummary = <div className="node-summary warning">No Source</div>;
    }
  } else if (node_type === 'transform') {
    const op = configuration?.operation;
    if (op) {
      const opName = op.replace('_', ' ');
      configSummary = <div className="node-summary" style={{ textTransform: 'capitalize' }}>{opName}</div>;
    } else {
      configSummary = <div className="node-summary warning">Unconfigured</div>;
    }
  } else if (node_type === 'data_quality') {
    const reqCols = configuration?.required_columns ? configuration.required_columns.split(',').length : 0;
    configSummary = <div className="node-summary">Rules: {reqCols > 0 ? reqCols : 'None'}</div>;
  }

  const iconClass = `palette-icon ${node_type}`;
  const typeName = node_type.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());

  return (
    <div className={`custom-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Top} style={{ width: '8px', height: '8px', background: '#94a3b8' }} />
      <div className="custom-node-header">
        <div className={iconClass} style={{ width: '20px', height: '20px', fontSize: '10px' }}>
          {typeName.charAt(0)}
        </div>
        <div className="custom-node-title">
          {typeName} 
          <span style={{ color: '#94a3b8', fontWeight: 'normal', fontSize: '11px' }}>#{sequence_index}</span>
        </div>
      </div>
      <div className="custom-node-body">
        {configSummary}
        
        {executionFeedback && executionFeedback.length > 0 && (
          <div className="node-feedback success">
            {executionFeedback.map((fb: string, i: number) => (
              <div key={i} style={{ fontSize: '10px', marginBottom: '2px' }}>✓ {fb}</div>
            ))}
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} style={{ width: '8px', height: '8px', background: '#94a3b8' }} />
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

const PipelineBuilder: React.FC = () => {
  const { pipelineId } = useParams<{ pipelineId: string }>();
  const [pipeline, setPipeline] = useState<Pipeline | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [activeDrawer, setActiveDrawer] = useState<'none' | 'node' | 'settings' | 'schedules' | 'versions' | 'logs'>('none');

  // Toast and Modal State
  const [toast, setToast] = useState<{text: string, type: 'success'|'error'|'info'} | null>(null);
  const showToast = (text: string, type: 'success'|'error'|'info' = 'info') => {
    setToast({ text, type });
    setTimeout(() => setToast(null), 4000);
  };

  const [promptModal, setPromptModal] = useState<{
    isOpen: boolean; title: string; label: string; value: string;
    onSubmit: (val: string) => void;
  }>({ isOpen: false, title: '', label: '', value: '', onSubmit: () => {} });

  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean; title: string; message: string;
    onConfirm: () => void;
  }>({ isOpen: false, title: '', message: '', onConfirm: () => {} });


  const onNodeClick = (_: any, node: Node) => {
    setSelectedNode(node);
    setActiveDrawer('node');
  };
  const onPaneClick = () => {
    setSelectedNode(null);
    if (activeDrawer === 'node') setActiveDrawer('none');
  };

  const openDrawer = (drawer: 'none' | 'node' | 'settings' | 'schedules' | 'versions' | 'logs') => {
    if (drawer !== 'node') setSelectedNode(null);
    setActiveDrawer(drawer);
  };
  
  // Execution state
  const [executing, setExecuting] = useState(false);
  const [runHistory, setRunHistory] = useState<ExecutionResponse[]>([]);
  
  const [selectedExecutionLogs, setSelectedExecutionLogs] = useState<ExecutionLogResponse[]>([]);
  const [selectedExecutionId, setSelectedExecutionId] = useState<string>('');

  // Scheduler state
  const [schedules, setSchedules] = useState<ScheduleResponse[]>([]);
  const [scheduleExpression, setScheduleExpression] = useState('daily');
  const [scheduleEnabled, setScheduleEnabled] = useState(true);

  // Versioning state
  const [versions, setVersions] = useState<PipelineVersion[]>([]);
  const [savingVersion, setSavingVersion] = useState(false);
  const [compareDiff, setCompareDiff] = useState<string[] | null>(null);

  // GitHub state
  const [githubModalOpen, setGithubModalOpen] = useState(false);
  const [selectedVersionForGithub, setSelectedVersionForGithub] = useState<PipelineVersion | null>(null);
  const [githubConnections, setGithubConnections] = useState<GithubConnectionResponse[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState('');
  const [githubBranch, setGithubBranch] = useState('main');
  const [githubCommitMsg, setGithubCommitMsg] = useState('');
  const [githubCreatePr, setGithubCreatePr] = useState(false);
  const [githubPrTitle, setGithubPrTitle] = useState('');
  const [githubPrBase, setGithubPrBase] = useState('main');
  const [pushingToGithub, setPushingToGithub] = useState(false);

  const fetchLogsForLatestExecution = async (executions: ExecutionResponse[]) => {
    if (executions.length === 0 || !pipelineId) return [];
    const latest = executions[0];
    try {
      const logs = await getExecutionLogs(pipelineId, latest.id!);
      return logs;
    } catch (e) {
      console.error("Failed to fetch latest logs", e);
      return [];
    }
  };

  const updateNodesWithFeedback = (flowNodes: Node[], logs: ExecutionLogResponse[], ds: DataSource[]) => {
    return flowNodes.map(n => {
      const nodeLogs = logs.filter(l => l.execution_id && (l as any).pipeline_node_id === n.id);
      const feedback = [];
      
      const rowsLog = nodeLogs.find(l => l.message?.match(/(\d+) rows/));
      if (rowsLog) {
        const m = rowsLog.message!.match(/(\d+) rows/);
        feedback.push(`Rows processed: ${m![1]}`);
      }
      
      const dqLog = nodeLogs.find(l => l.message?.startsWith('Data Quality:'));
      if (dqLog) {
        const scoreM = dqLog.message!.match(/score (\d+\/\d+)/);
        if (scoreM) feedback.push(`Quality score: ${scoreM[1]}`);
      }

      return {
        ...n,
        data: {
          ...n.data,
          dataSources: ds,
          executionFeedback: feedback.length > 0 ? feedback : null
        }
      };
    });
  };

  const onNodesChange = useCallback((changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
  const onConnect = useCallback((params: Connection) => setEdges((eds) => addEdge(params, eds)), []);

  useEffect(() => {
    const fetchData = async () => {
      if (!pipelineId) return;
      try {
        const [pipeRes, nodesRes, schedulesRes, versionsRes, executionsRes] = await Promise.all([
          getPipeline(pipelineId),
          getPipelineNodes(pipelineId),
          getSchedules(pipelineId),
          getPipelineVersions(pipelineId),
          listExecutions(pipelineId)
        ]);
        setPipeline(pipeRes);
        setSchedules(schedulesRes);
        setVersions(versionsRes);
        
        const sortedExecutions = executionsRes.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());
        setRunHistory(sortedExecutions);
        
        const dsRes = await getDataSources(pipeRes.project_id);
        setDataSources(dsRes);

        try {
          const conns = await listConnections();
          setGithubConnections(conns);
          if (conns.length > 0) setSelectedConnectionId(conns[0].id);
        } catch (e) {}

        const logs = await fetchLogsForLatestExecution(sortedExecutions);

        const flowNodes: Node[] = nodesRes.map(n => ({
          id: n.id,
          type: 'custom',
          position: { x: n.position_x || 0, y: n.position_y || 0 },
          data: {
            node_type: n.node_type,
            sequence_index: n.sequence_index || 0,
            configuration: n.configuration ? JSON.parse(n.configuration) : {}
          }
        }));
        
        setNodes(updateNodesWithFeedback(flowNodes, logs, dsRes));
        
        const sorted = [...flowNodes].sort((a, b) => a.data.sequence_index - b.data.sequence_index);
        const flowEdges: Edge[] = [];
        for (let i = 0; i < sorted.length - 1; i++) {
          flowEdges.push({
            id: `e-${sorted[i].id}-${sorted[i+1].id}`,
            source: sorted[i].id,
            target: sorted[i+1].id,
          });
        }
        setEdges(flowEdges);
        
      } catch (err) {
        console.error("Failed to load pipeline data", err);
      }
    };
    fetchData();
  }, [pipelineId]);

  const addNode = (type: string) => {
    const newNode: Node = {
      id: `new-${Date.now()}`,
      type: 'custom',
      position: { x: Math.random() * 200, y: Math.random() * 200 },
      data: {
        node_type: type,
        sequence_index: nodes.length + 1,
        configuration: {},
        dataSources: dataSources
      }
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const savePipelineNodes = async () => {
    if (!pipelineId) return;
    for (const node of nodes) {
      const isNew = node.id.startsWith('new-');
      const payload = {
        node_type: node.data.node_type,
        configuration: JSON.stringify(node.data.configuration),
        sequence_index: Number(node.data.sequence_index),
        position_x: Math.round(node.position.x),
        position_y: Math.round(node.position.y),
      };
      
      if (isNew) {
        const created = await createPipelineNode(pipelineId, payload);
        setNodes(nds => nds.map(n => n.id === node.id ? { ...n, id: created.id } : n));
      } else {
        await updatePipelineNode(pipelineId, node.id, payload);
      }
    }
  };

  const handleSave = async () => {
    try {
      await savePipelineNodes();
      showToast('Pipeline saved successfully!', 'success');
    } catch (err: any) {
      showToast('Failed to save pipeline: ' + (err.response?.data?.detail || err.message), 'error');
    }
  };

  const handleSaveVersion = async () => {
    if (!pipelineId) return;
    const desc = prompt("Enter version description:");
    if (desc === null) return;
    setSavingVersion(true);
    try {
      await savePipelineNodes();
      const newVer = await createPipelineVersion(pipelineId, { description: desc });
      setVersions([newVer, ...versions]);
      alert("Version saved successfully!");
    } catch (err: any) {
      alert("Failed to save version: " + (err.response?.data?.detail || err.message));
    } finally {
      setSavingVersion(false);
    }
  };

  const handleCompare = async (v1Id: string, v2Id: string) => {
    if (!pipelineId) return;
    try {
      const diff = await getPipelineVersionDiff(pipelineId, v1Id, v2Id);
      setCompareDiff(diff.length > 0 ? diff : ["No differences found."]);
    } catch (err: any) {
      showToast("Failed to compare: " + (err.response?.data?.detail || err.message), 'error');
    }
  };

  const handleRollback = async (version: PipelineVersion) => {
    if (!pipelineId) return;
    const desc = prompt(`Enter optional rollback message:`, `Rollback to version ${version.version_number}`);
    if (desc === null) return;
    
    setSavingVersion(true);
    try {
      const newVer = await rollbackPipelineVersion(pipelineId, version.id, { description: desc });
      setVersions([newVer, ...versions]);
      
      const nodesRes = await getPipelineNodes(pipelineId);
      const flowNodes: Node[] = nodesRes.map(n => ({
        id: n.id,
        type: 'custom',
        position: { x: n.position_x || 0, y: n.position_y || 0 },
        data: {
          node_type: n.node_type,
          sequence_index: n.sequence_index || 0,
          configuration: n.configuration ? JSON.parse(n.configuration) : {}
        }
      }));
      setNodes(flowNodes);
      
      alert("Rollback successful!");
    } catch (err: any) {
      alert("Failed to rollback: " + (err.response?.data?.detail || err.message));
    } finally {
      setSavingVersion(false);
    }
  };

  const handleRun = async () => {
    if (!pipelineId) return;
    setExecuting(true);
    try {
      const execRes = await executePipeline(pipelineId, 'manual');
      const logs = await getExecutionLogs(pipelineId, execRes.id!);
      
      const newExecutions = await listExecutions(pipelineId);
      const sorted = newExecutions.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());
      setRunHistory(sorted);
      
      setNodes(nds => updateNodesWithFeedback(nds, logs, dataSources));
      showToast(`Pipeline execution ${execRes.status}!`, execRes.status === 'failed' ? 'error' : 'success');
    } catch (err: any) {
      showToast("Failed to run pipeline: " + (err.response?.data?.detail || err.message), 'error');
    } finally {
      setExecuting(false);
    }
  };

  const updateSelectedNodeData = (key: string, value: any) => {
    if (!selectedNode) return;
    setNodes((nds) => 
      nds.map(n => {
        if (n.id === selectedNode.id) {
          const updated = { ...n, data: { ...n.data, [key]: value } };
          setSelectedNode(updated);
          return updated;
        }
        return n;
      })
    );
  };
  
  const updateSelectedNodeConfig = (key: string, value: any) => {
    if (!selectedNode) return;
    updateSelectedNodeData('configuration', { ...selectedNode.data.configuration, [key]: value });
  };

  return (
    <div className="pb-container">
      
      {toast && (
        <div style={{ position: 'absolute', top: '70px', left: '50%', transform: 'translateX(-50%)', zIndex: 999 }}>
          <div className={`pb-status-msg ${toast.type}`}>
            {toast.text}
          </div>
        </div>
      )}

      <div className="pb-header">
        <div className="pb-header-left">
          <Link to="/projects" className="pb-back-btn">← Back to Projects</Link>
          <h2 className="pb-title">{pipeline ? pipeline.name : 'Loading...'}</h2>
          {pipeline?.status && (
            <span className={`badge ${pipeline.status.toLowerCase()}`}>{pipeline.status}</span>
          )}
        </div>
        <div className="pb-header-right">
          <div className="header-status">
            <button onClick={() => openDrawer('schedules')} className="btn btn-ghost">📅 Schedule</button>
            <button onClick={() => openDrawer('settings')} className="btn btn-ghost">⚙ Settings</button>
          </div>
          <div className="header-actions">
            <button onClick={handleSave} className="btn btn-secondary">Save Changes</button>
            <button onClick={handleSaveVersion} disabled={savingVersion} className="btn btn-secondary">
              {savingVersion ? 'Saving...' : 'Create Version'}
            </button>
            <button onClick={handleRun} disabled={executing} className="btn btn-primary">
              {executing ? 'Running Pipeline...' : 'Run Pipeline'}
            </button>
          </div>
        </div>
      </div>

      <div className="pb-content">
        <div className="pb-sidebar-left">
          <div className="pb-sidebar-header">Add Node</div>
          <div className="pb-sidebar-body">
            <button onClick={() => addNode('extract')} className="palette-btn">
              <div className="palette-icon extract">E</div>
              <div className="palette-text">
                <span className="palette-text-title">Extract</span>
                <span className="palette-text-desc">Read input data</span>
              </div>
            </button>
            <button onClick={() => addNode('transform')} className="palette-btn">
              <div className="palette-icon transform">T</div>
              <div className="palette-text">
                <span className="palette-text-title">Transform</span>
                <span className="palette-text-desc">Modify data</span>
              </div>
            </button>
            <button onClick={() => addNode('data_quality')} className="palette-btn">
              <div className="palette-icon data_quality">Q</div>
              <div className="palette-text">
                <span className="palette-text-title">Data Quality</span>
                <span className="palette-text-desc">Validate data</span>
              </div>
            </button>
            <button onClick={() => addNode('load')} className="palette-btn">
              <div className="palette-icon load">L</div>
              <div className="palette-text">
                <span className="palette-text-title">Load</span>
                <span className="palette-text-desc">Write output</span>
              </div>
            </button>
          </div>
        </div>

        <div className="pb-canvas-area">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            defaultViewport={defaultViewport}
            fitView
            fitViewOptions={{ padding: 0.2 }}
          >
            <Background color="#94a3b8" gap={20} size={1} />
            <Controls />
          </ReactFlow>

          {activeDrawer === 'node' && selectedNode && (
            <div className="pb-drawer right">
              <div className="drawer-header">
                <h3>{selectedNode.data.node_type.replace('_', ' ').toUpperCase()} Configuration</h3>
                <button onClick={() => openDrawer('none')} className="drawer-close">✕</button>
              </div>
              <div className="drawer-body">
                <div className="form-group">
                  <label className="form-label">Sequence Index (Execution Order)</label>
                  <input type="number" className="form-control" value={selectedNode.data.sequence_index} onChange={(e) => updateSelectedNodeData('sequence_index', parseInt(e.target.value) || 0)} />
                </div>

                {(selectedNode.data.node_type === 'extract' || selectedNode.data.node_type === 'load') && (
                  <div className="form-group">
                    <label className="form-label">Data Source</label>
                    <select className="form-control" value={selectedNode.data.configuration?.data_source_id || ''} onChange={(e) => updateSelectedNodeConfig('data_source_id', e.target.value)}>
                      <option value="">Select Data Source...</option>
                      {dataSources.map(ds => <option key={ds.id} value={ds.id}>{ds.name} ({ds.type})</option>)}
                    </select>
                  </div>
                )}
                {selectedNode.data.node_type === 'extract' && (dataSources.find(d => d.id === selectedNode.data.configuration?.data_source_id)?.type === 'PostgreSQL') && (
                  <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '4px' }}>
                    <h4 style={{ margin: '0 0 10px 0', fontSize: '13px' }}>SQL Query Builder</h4>
                    <div className="form-group"><label className="form-label">Select Columns</label><input type="text" className="form-control" value={selectedNode.data.configuration?.sql_select || ''} onChange={(e) => updateSelectedNodeConfig('sql_select', e.target.value)} placeholder="*" /></div>
                    
                    <div style={{ display: 'flex', gap: '5px' }}>
                      <div className="form-group" style={{ flex: 1 }}><label className="form-label">Join Type</label><select className="form-control" value={selectedNode.data.configuration?.sql_join_type || 'INNER'} onChange={(e) => updateSelectedNodeConfig('sql_join_type', e.target.value)}><option value="INNER">INNER</option><option value="LEFT">LEFT</option></select></div>
                      <div className="form-group" style={{ flex: 2 }}><label className="form-label">Join Table</label><input type="text" className="form-control" value={selectedNode.data.configuration?.sql_join_table || ''} onChange={(e) => updateSelectedNodeConfig('sql_join_table', e.target.value)} placeholder="users" /></div>
                    </div>
                    {selectedNode.data.configuration?.sql_join_table && (
                      <div style={{ display: 'flex', gap: '5px' }}>
                        <div className="form-group" style={{ flex: 1 }}><label className="form-label">Join Left Col</label><input type="text" className="form-control" value={selectedNode.data.configuration?.sql_join_left || ''} onChange={(e) => updateSelectedNodeConfig('sql_join_left', e.target.value)} placeholder="t1.id" /></div>
                        <div className="form-group" style={{ flex: 1 }}><label className="form-label">Join Right Col</label><input type="text" className="form-control" value={selectedNode.data.configuration?.sql_join_right || ''} onChange={(e) => updateSelectedNodeConfig('sql_join_right', e.target.value)} placeholder="users.id" /></div>
                      </div>
                    )}
                    
                    <div style={{ display: 'flex', gap: '5px' }}>
                      <div className="form-group" style={{ flex: 2 }}><label className="form-label">Where Column</label><input type="text" className="form-control" value={selectedNode.data.configuration?.sql_where_col || ''} onChange={(e) => updateSelectedNodeConfig('sql_where_col', e.target.value)} placeholder="age" /></div>
                      <div className="form-group" style={{ flex: 1 }}><label className="form-label">Op</label><select className="form-control" value={selectedNode.data.configuration?.sql_where_op || '='} onChange={(e) => updateSelectedNodeConfig('sql_where_op', e.target.value)}><option value="=">=</option><option value="!=">!=</option><option value=">">&gt;</option><option value="<">&lt;</option><option value=">=">&gt;=</option><option value="<=">&lt;=</option><option value="LIKE">LIKE</option></select></div>
                      <div className="form-group" style={{ flex: 2 }}><label className="form-label">Where Value</label><input type="text" className="form-control" value={selectedNode.data.configuration?.sql_where_val || ''} onChange={(e) => updateSelectedNodeConfig('sql_where_val', e.target.value)} /></div>
                    </div>
                    
                    <div className="form-group"><label className="form-label">Group By</label><input type="text" className="form-control" value={selectedNode.data.configuration?.sql_group_by || ''} onChange={(e) => updateSelectedNodeConfig('sql_group_by', e.target.value)} placeholder="status" /></div>
                    {selectedNode.data.configuration?.sql_group_by && (
                      <div style={{ display: 'flex', gap: '5px' }}>
                        <div className="form-group" style={{ flex: 2 }}><label className="form-label">Having Column</label><input type="text" className="form-control" value={selectedNode.data.configuration?.sql_having_col || ''} onChange={(e) => updateSelectedNodeConfig('sql_having_col', e.target.value)} placeholder="COUNT(*)" /></div>
                        <div className="form-group" style={{ flex: 1 }}><label className="form-label">Op</label><select className="form-control" value={selectedNode.data.configuration?.sql_having_op || '>'} onChange={(e) => updateSelectedNodeConfig('sql_having_op', e.target.value)}><option value="=">=</option><option value="!=">!=</option><option value=">">&gt;</option><option value="<">&lt;</option><option value=">=">&gt;=</option><option value="<=">&lt;=</option></select></div>
                        <div className="form-group" style={{ flex: 2 }}><label className="form-label">Having Value</label><input type="text" className="form-control" value={selectedNode.data.configuration?.sql_having_val || ''} onChange={(e) => updateSelectedNodeConfig('sql_having_val', e.target.value)} /></div>
                      </div>
                    )}
                    
                    <div style={{ display: 'flex', gap: '5px' }}>
                      <div className="form-group" style={{ flex: 2 }}><label className="form-label">Order By</label><input type="text" className="form-control" value={selectedNode.data.configuration?.sql_order_by || ''} onChange={(e) => updateSelectedNodeConfig('sql_order_by', e.target.value)} placeholder="id DESC" /></div>
                      <div className="form-group" style={{ flex: 1 }}><label className="form-label">Limit</label><input type="number" className="form-control" value={selectedNode.data.configuration?.sql_limit || ''} onChange={(e) => updateSelectedNodeConfig('sql_limit', parseInt(e.target.value) || '')} placeholder="100" /></div>
                    </div>
                  </div>
                )}

                {selectedNode.data.node_type === 'transform' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Operation</label>
                      <select className="form-control" value={selectedNode.data.configuration?.operation || ''} onChange={(e) => updateSelectedNodeConfig('operation', e.target.value)}>
                        <option value="">Select Operation...</option>
                        <option value="drop_nulls">Drop Nulls</option>
                        <option value="select_columns">Select Columns</option>
                        <option value="remove_duplicates">Remove Duplicates</option>
                        <option value="fill_missing">Fill Missing</option>
                        <option value="standardize_values">Standardize Values</option>
                        <option value="merge">Merge Data</option>
                        <option value="filter">Filter</option>
                        <option value="rename_column">Rename Column</option>
                        <option value="drop_columns">Drop Columns</option>
                        <option value="cast_type">Cast Type</option>
                        <option value="inner_join">Inner Join</option>
                        <option value="left_join">Left Join</option>
                        <option value="right_join">Right Join</option>
                        <option value="group_by">Group By</option>
                        <option value="count">Count</option>
                        <option value="sum">Sum</option>
                        <option value="avg">Average</option>
                        <option value="min">Min</option>
                        <option value="max">Max</option>
                      </select>
                    </div>

                    {selectedNode.data.configuration?.operation === 'filter' && (
                      <>
                        <div className="form-group"><label className="form-label">Column</label><input type="text" className="form-control" value={selectedNode.data.configuration?.column || ''} onChange={(e) => updateSelectedNodeConfig('column', e.target.value)} /></div>
                        <div className="form-group">
                          <label className="form-label">Operator</label>
                          <select className="form-control" value={selectedNode.data.configuration?.operator || '=='} onChange={(e) => updateSelectedNodeConfig('operator', e.target.value)}>
                            <option value="==">==</option><option value="!=">!=</option><option value=">">&gt;</option><option value="<">&lt;</option><option value=">=">&gt;=</option><option value="<=">&lt;=</option><option value="contains">Contains</option>
                          </select>
                        </div>
                        <div className="form-group"><label className="form-label">Value</label><input type="text" className="form-control" value={selectedNode.data.configuration?.value || ''} onChange={(e) => updateSelectedNodeConfig('value', e.target.value)} /></div>
                      </>
                    )}
                    {selectedNode.data.configuration?.operation === 'rename_column' && (
                      <>
                        <div className="form-group"><label className="form-label">Old Name</label><input type="text" className="form-control" value={selectedNode.data.configuration?.old_name || ''} onChange={(e) => updateSelectedNodeConfig('old_name', e.target.value)} /></div>
                        <div className="form-group"><label className="form-label">New Name</label><input type="text" className="form-control" value={selectedNode.data.configuration?.new_name || ''} onChange={(e) => updateSelectedNodeConfig('new_name', e.target.value)} /></div>
                      </>
                    )}
                    {selectedNode.data.configuration?.operation === 'drop_columns' && (
                      <div className="form-group">
                        <label className="form-label">Columns (comma separated)</label>
                        <input type="text" className="form-control" value={selectedNode.data.configuration?.columns || ''} onChange={(e) => updateSelectedNodeConfig('columns', e.target.value)} placeholder="id, name" />
                      </div>
                    )}
                    {selectedNode.data.configuration?.operation === 'cast_type' && (
                      <>
                        <div className="form-group"><label className="form-label">Column</label><input type="text" className="form-control" value={selectedNode.data.configuration?.column || ''} onChange={(e) => updateSelectedNodeConfig('column', e.target.value)} /></div>
                        <div className="form-group">
                          <label className="form-label">Target Type</label>
                          <select className="form-control" value={selectedNode.data.configuration?.target_type || 'str'} onChange={(e) => updateSelectedNodeConfig('target_type', e.target.value)}>
                            <option value="str">String</option><option value="int">Integer</option><option value="float">Float</option><option value="bool">Boolean</option>
                          </select>
                        </div>
                      </>
                    )}
                    {['inner_join', 'left_join', 'right_join'].includes(selectedNode.data.configuration?.operation) && (
                      <>
                        <div className="form-group">
                          <label className="form-label">Right Data Source</label>
                          <select className="form-control" value={selectedNode.data.configuration?.right_source || ''} onChange={(e) => updateSelectedNodeConfig('right_source', e.target.value)}>
                            <option value="">Select Data Source...</option>
                            {dataSources.map(ds => <option key={ds.id} value={ds.id}>{ds.name}</option>)}
                          </select>
                        </div>
                        <div className="form-group"><label className="form-label">Left Key</label><input type="text" className="form-control" value={selectedNode.data.configuration?.left_key || ''} onChange={(e) => updateSelectedNodeConfig('left_key', e.target.value)} /></div>
                        <div className="form-group"><label className="form-label">Right Key</label><input type="text" className="form-control" value={selectedNode.data.configuration?.right_key || ''} onChange={(e) => updateSelectedNodeConfig('right_key', e.target.value)} /></div>
                      </>
                    )}
                    {['group_by', 'count', 'sum', 'avg', 'min', 'max'].includes(selectedNode.data.configuration?.operation) && (
                      <>
                        <div className="form-group"><label className="form-label">Group Columns (comma separated)</label><input type="text" className="form-control" value={selectedNode.data.configuration?.group_columns || ''} onChange={(e) => updateSelectedNodeConfig('group_columns', e.target.value)} placeholder="category, status" /></div>
                        {selectedNode.data.configuration?.operation !== 'group_by' && (
                          <div className="form-group"><label className="form-label">Aggregation Column</label><input type="text" className="form-control" value={selectedNode.data.configuration?.agg_column || ''} onChange={(e) => updateSelectedNodeConfig('agg_column', e.target.value)} /></div>
                        )}
                      </>
                    )}
                    {selectedNode.data.configuration?.operation === 'select_columns' && (
                      <div className="form-group">
                        <label className="form-label">Columns (comma separated)</label>
                        <input type="text" className="form-control" value={(selectedNode.data.configuration?.columns || []).join(', ')} onChange={(e) => updateSelectedNodeConfig('columns', e.target.value.split(',').map(s => s.trim()).filter(Boolean))} placeholder="id, name, price" />
                      </div>
                    )}
                    {selectedNode.data.configuration?.operation === 'remove_duplicates' && (
                      <div className="form-group">
                        <label className="form-label">Columns (comma separated, optional)</label>
                        <input type="text" className="form-control" value={(selectedNode.data.configuration?.columns || []).join(', ')} onChange={(e) => updateSelectedNodeConfig('columns', e.target.value.split(',').map(s => s.trim()).filter(Boolean))} placeholder="id, name" />
                      </div>
                    )}
                    {selectedNode.data.configuration?.operation === 'fill_missing' && (
                      <>
                        <div className="form-group"><label className="form-label">Column</label><input type="text" className="form-control" value={selectedNode.data.configuration?.column || ''} onChange={(e) => updateSelectedNodeConfig('column', e.target.value)} /></div>
                        <div className="form-group"><label className="form-label">Fallback Value</label><input type="text" className="form-control" value={selectedNode.data.configuration?.value || ''} onChange={(e) => updateSelectedNodeConfig('value', e.target.value)} /></div>
                      </>
                    )}
                    {selectedNode.data.configuration?.operation === 'standardize_values' && (
                      <>
                        <div className="form-group"><label className="form-label">Column</label><input type="text" className="form-control" value={selectedNode.data.configuration?.column || ''} onChange={(e) => updateSelectedNodeConfig('column', e.target.value)} /></div>
                        <div className="form-group"><label className="form-label">Mapping (JSON format)</label><textarea className="form-control" style={{ minHeight: '80px', fontFamily: 'monospace' }} value={selectedNode.data.configuration?.mapping ? JSON.stringify(selectedNode.data.configuration.mapping, null, 2) : ''} onChange={(e) => { try { updateSelectedNodeConfig('mapping', JSON.parse(e.target.value)); } catch(err) {} }} onBlur={(e) => { try { updateSelectedNodeConfig('mapping', JSON.parse(e.target.value)); } catch(err) { showToast("Invalid JSON format in mapping", 'error'); } }} placeholder='{"old_val": "new_val"}' /></div>
                      </>
                    )}
                    {selectedNode.data.configuration?.operation === 'merge' && (
                      <>
                        <div className="form-group">
                          <label className="form-label">Right Data Source</label>
                          <select className="form-control" value={selectedNode.data.configuration?.right_source || ''} onChange={(e) => updateSelectedNodeConfig('right_source', e.target.value)}>
                            <option value="">Select Data Source...</option>
                            {dataSources.map(ds => <option key={ds.id} value={ds.id}>{ds.name}</option>)}
                          </select>
                        </div>
                        <div className="form-group"><label className="form-label">Left Key</label><input type="text" className="form-control" value={selectedNode.data.configuration?.left_key || ''} onChange={(e) => updateSelectedNodeConfig('left_key', e.target.value)} /></div>
                        <div className="form-group"><label className="form-label">Right Key</label><input type="text" className="form-control" value={selectedNode.data.configuration?.right_key || ''} onChange={(e) => updateSelectedNodeConfig('right_key', e.target.value)} /></div>
                        <div className="form-group">
                          <label className="form-label">Join Type</label>
                          <select className="form-control" value={selectedNode.data.configuration?.how || 'left'} onChange={(e) => updateSelectedNodeConfig('how', e.target.value)}>
                            <option value="left">Left Join</option><option value="inner">Inner Join</option><option value="outer">Outer Join</option>
                          </select>
                        </div>
                      </>
                    )}
                  </>
                )}

                {selectedNode.data.node_type === 'data_quality' && (
                  <>
                    <div className="form-group"><label className="form-label">Required Columns (comma separated)</label><input type="text" className="form-control" value={selectedNode.data.configuration?.required_columns || ''} onChange={(e) => updateSelectedNodeConfig('required_columns', e.target.value)} placeholder="id, email" /></div>
                    <div className="form-group"><label className="form-label">Email Validation Column (optional)</label><input type="text" className="form-control" value={selectedNode.data.configuration?.email_column || ''} onChange={(e) => updateSelectedNodeConfig('email_column', e.target.value)} placeholder="email" /></div>
                    <div className="form-group"><label className="form-label">Unique Columns (comma separated)</label><input type="text" className="form-control" value={selectedNode.data.configuration?.unique_columns || ''} onChange={(e) => updateSelectedNodeConfig('unique_columns', e.target.value)} placeholder="id, email" /></div>
                    <div className="form-group"><label className="form-label">Type Validation (JSON mapping)</label><textarea className="form-control" style={{ minHeight: '60px', fontFamily: 'monospace', fontSize: '11px' }} value={selectedNode.data.configuration?.type_validation ? JSON.stringify(selectedNode.data.configuration.type_validation) : ''} onChange={(e) => { try { updateSelectedNodeConfig('type_validation', JSON.parse(e.target.value)); } catch(err) {} }} placeholder='{"age": "int"}' /></div>
                  </>
                )}
                
                <div style={{ marginTop: '20px' }}>
                  <button onClick={() => {
                    setNodes(nds => nds.filter(n => n.id !== selectedNode.id));
                    openDrawer('none');
                  }} className="btn btn-danger" style={{ width: '100%' }}>Delete Node</button>
                </div>              </div>
            </div>
          )}

          {activeDrawer === 'schedules' && (
            <div className="pb-drawer right">
              <div className="drawer-header">
                <h3>Manage Schedules</h3>
                <button onClick={() => openDrawer('none')} className="drawer-close">✕</button>
              </div>
              <div className="drawer-body">

                  <div style={{ display: 'flex', gap: '5px', marginBottom: '15px' }}>
                    <select className="form-control" style={{ padding: '6px' }} value={scheduleExpression} onChange={e => setScheduleExpression(e.target.value)}>
                      <option value="hourly">Hourly</option><option value="daily">Daily</option><option value="weekly">Weekly</option>
                    </select>
                    <label style={{ display: 'flex', alignItems: 'center', fontSize: '12px', gap: '5px' }}>
                      <input type="checkbox" checked={scheduleEnabled} onChange={e => setScheduleEnabled(e.target.checked)} />
                      Enabled
                    </label>
                    <button onClick={async () => {
                      if (!pipelineId) return;
                      const newSchedule = await createSchedule(pipelineId, { schedule_expression: scheduleExpression, enabled: scheduleEnabled });
                      setSchedules([...schedules, newSchedule]);
                    }} className="btn btn-primary" style={{ padding: '6px 12px' }}>Add</button>
                  </div>
                  {schedules.map(sched => (
                    <div key={sched.id} className="history-card">
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <strong>{sched.schedule_expression}</strong>
                        <span style={{ color: sched.enabled ? '#10b981' : '#ef4444' }}>{sched.enabled ? 'Active' : 'Disabled'}</span>
                      </div>
                      <div style={{ display: 'flex', gap: '5px', marginTop: '8px' }}>
                        <button onClick={async () => {
                          if (!pipelineId) return;
                          const updated = await updateSchedule(pipelineId, sched.id, { enabled: !sched.enabled });
                          setSchedules(schedules.map(s => s.id === sched.id ? updated : s));
                        }} className="btn btn-secondary" style={{ padding: '4px', flex: 1 }}>Toggle</button>
                        <button onClick={async () => {
                          if (!pipelineId || !confirm('Delete?')) return;
                          await deleteSchedule(pipelineId, sched.id);
                          setSchedules(schedules.filter(s => s.id !== sched.id));
                        }} className="btn" style={{ padding: '4px', backgroundColor: '#fee2e2', color: '#991b1b' }}>Delete</button>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {activeDrawer === 'settings' && (
            <div className="pb-drawer right">
              <div className="drawer-header">
                <h3>Pipeline Settings</h3>
                <button onClick={() => openDrawer('none')} className="drawer-close">✕</button>
              </div>
              <div className="drawer-body">
                <div className="accordion-section" style={{ marginTop: 0, borderTop: 'none', paddingTop: 0 }}>
                  <h3 className="accordion-title">Recent Executions</h3>
                  {runHistory.length === 0 ? (
                    <p style={{ fontSize: '12px', color: 'var(--text)' }}>No runs yet.</p>
                  ) : (
                    runHistory.slice(0, 3).map(exec => (
                      <div key={exec.id} className="history-card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                          <span className={`badge ${exec.status?.toLowerCase()}`}>{exec.status}</span>
                          <span style={{ fontSize: '11px', color: 'var(--text)' }}>
                            {new Date(exec.created_at!).toLocaleDateString()}
                          </span>
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text)' }}>
                          Triggered by {exec.triggered_by}
                          {exec.duration && ` • ${exec.duration}s`}
                        </div>
                        {exec.error_message && (
                          <div style={{ fontSize: '11px', color: '#ef4444', marginTop: '4px' }}>Error: {exec.error_message}</div>
                        )}
                        <button onClick={async () => {
                          if (!pipelineId) return;
                          const logs = await getExecutionLogs(pipelineId, exec.id!);
                          setSelectedExecutionLogs(logs);
                          setSelectedExecutionId(exec.id!);
                        }} className="btn btn-secondary" style={{ width: '100%', marginTop: '8px', padding: '4px' }}>
                          {selectedExecutionId === exec.id ? 'Refresh Logs' : 'View Logs'}
                        </button>
                        {selectedExecutionId === exec.id && (
                          <div style={{ marginTop: '8px', maxHeight: '150px', overflowY: 'auto', background: 'white', padding: '8px', border: '1px solid #e2e8f0', borderRadius: '4px' }}>
                            {selectedExecutionLogs.map(l => (
                              <div key={l.id} style={{ fontSize: '10px', color: l.level === 'ERROR' ? '#ef4444' : '#334155' }}>
                                <strong>{l.level}:</strong> {l.message}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>

                <div className="accordion-section">
                  <h3 className="accordion-title">Version History</h3>
                  {compareDiff && (
                    <div style={{ marginBottom: '10px', padding: '8px', backgroundColor: '#fef9c3', border: '1px solid #fde047', borderRadius: '4px', fontSize: '11px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <strong>Compare Results</strong>
                        <button onClick={() => setCompareDiff(null)} style={{ border: 'none', background: 'none', cursor: 'pointer' }}>✖</button>
                      </div>
                      <ul style={{ paddingLeft: '16px', margin: 0 }}>
                        {compareDiff.map((d, i) => <li key={i}>{d}</li>)}
                      </ul>
                    </div>
                  )}
                  {versions.slice(0, 3).map((ver, idx) => (
                    <div key={ver.id} className="history-card">
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <strong style={{ fontSize: '12px' }}>v{ver.version_number}</strong>
                        <span style={{ fontSize: '11px', color: 'var(--text)' }}>{new Date(ver.created_at!).toLocaleDateString()}</span>
                      </div>
                      {ver.description && <div style={{ fontSize: '11px', color: 'var(--text)' }}>{ver.description}</div>}
                      <div style={{ display: 'flex', gap: '4px', marginTop: '8px', flexWrap: 'wrap' }}>
                        {idx < versions.length - 1 && (
                          <button onClick={() => handleCompare(versions[idx + 1].id, ver.id)} className="btn btn-secondary" style={{ padding: '4px', fontSize: '10px', flex: 1 }}>Compare</button>
                        )}
                        <button onClick={() => { setSelectedVersionForGithub(ver); setGithubModalOpen(true); }} className="btn btn-secondary" style={{ padding: '4px', fontSize: '10px', flex: 1 }}>GitHub Push</button>
                        <button onClick={() => handleRollback(ver)} className="btn" style={{ padding: '4px', fontSize: '10px', backgroundColor: '#fee2e2', color: '#991b1b', flex: 1 }}>Rollback</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="pb-status-bar">
        <span>Nodes: {nodes.length}</span>
        {runHistory.length > 0 && (
          <>
            <span className="divider">|</span>
            <span>Last run: <span className={`badge ${runHistory[0].status?.toLowerCase()}`}>{runHistory[0].status}</span></span>
            {runHistory[0].duration && <span> ({runHistory[0].duration}s)</span>}
            <button className="btn-link" onClick={() => {
              setSelectedExecutionId(runHistory[0].id!);
              getExecutionLogs(pipelineId!, runHistory[0].id!).then(setSelectedExecutionLogs);
              openDrawer('logs');
            }}>View Logs</button>
          </>
        )}
      </div>

      {activeDrawer === 'logs' && (
        <div className="pb-drawer bottom">
          <div className="drawer-header">
            <h3>Execution Logs</h3>
            <button onClick={() => openDrawer('none')} className="drawer-close">✕</button>
          </div>
          <div className="drawer-body" style={{ background: '#1e293b', color: '#f8fafc', fontFamily: 'monospace' }}>
            {selectedExecutionLogs.length === 0 ? (
              <p>No logs available for this execution.</p>
            ) : (
              selectedExecutionLogs.map(l => (
                <div key={l.id} style={{ fontSize: '12px', color: l.level === 'ERROR' ? '#fca5a5' : '#f8fafc', marginBottom: '4px' }}>
                  <span style={{ color: '#94a3b8' }}>[{new Date(l.timestamp || '').toLocaleTimeString()}]</span> <strong>{l.level}:</strong> {l.message}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {githubModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 style={{ margin: '0 0 20px 0' }}>Push to GitHub (v{selectedVersionForGithub?.version_number})</h3>
            <div className="form-group">
              <label className="form-label">Connection</label>
              <select className="form-control" value={selectedConnectionId} onChange={e => setSelectedConnectionId(e.target.value)}>
                {githubConnections.map(c => <option key={c.id} value={c.id}>{c.repository_name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Branch</label>
              <input type="text" className="form-control" value={githubBranch} onChange={e => setGithubBranch(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Commit Message</label>
              <input type="text" className="form-control" value={githubCommitMsg} onChange={e => setGithubCommitMsg(e.target.value)} />
            </div>
            <div className="form-group" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input type="checkbox" id="pr" checked={githubCreatePr} onChange={e => setGithubCreatePr(e.target.checked)} />
              <label htmlFor="pr" className="form-label" style={{ margin: 0 }}>Create Pull Request</label>
            </div>
            {githubCreatePr && (
              <>
                <div className="form-group"><label className="form-label">PR Title</label><input type="text" className="form-control" value={githubPrTitle} onChange={e => setGithubPrTitle(e.target.value)} /></div>
                <div className="form-group"><label className="form-label">Base Branch</label><input type="text" className="form-control" value={githubPrBase} onChange={e => setGithubPrBase(e.target.value)} /></div>
              </>
            )}
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '24px' }}>
              <button onClick={() => setGithubModalOpen(false)} className="btn btn-secondary">Cancel</button>
              <button onClick={() => {
                if (!pipelineId || !selectedVersionForGithub) return;
                setPushingToGithub(true);
                pushPipelineVersionToGithub(pipelineId, selectedVersionForGithub.id, {
                  connection_id: selectedConnectionId, branch: githubBranch, commit_message: githubCommitMsg, create_pr: githubCreatePr, pr_title: githubPrTitle, pr_base: githubPrBase
                }).then(() => {
                  showToast('Pushed to GitHub successfully', 'success');
                  setGithubModalOpen(false);
                }).catch(e => showToast('Failed to push: ' + e.message, 'error')).finally(() => setPushingToGithub(false));
              }} disabled={pushingToGithub} className="btn btn-primary">
                {pushingToGithub ? 'Pushing...' : 'Push'}
              </button>
            </div>
          </div>
        </div>
      )}
      {promptModal?.isOpen && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ width: '380px' }}>
            <h3 className="modal-title">{promptModal.title}</h3>
            <div className="form-group">
              <label className="form-label">{promptModal.label}</label>
              <input type="text" className="form-control" autoFocus value={promptModal.value} onChange={(e) => setPromptModal({ ...promptModal, value: e.target.value })} />
            </div>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '24px' }}>
              <button onClick={() => setPromptModal({ ...promptModal, isOpen: false })} className="btn btn-secondary">Cancel</button>
              <button onClick={() => promptModal.onSubmit(promptModal.value)} className="btn btn-primary">Confirm</button>
            </div>
          </div>
        </div>
      )}

      {confirmModal?.isOpen && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ width: '380px' }}>
            <h3 className="modal-title">{confirmModal.title}</h3>
            <p style={{ fontSize: '13px', color: '#475569', margin: '10px 0 20px 0' }}>{confirmModal.message}</p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button onClick={() => setConfirmModal({ ...confirmModal, isOpen: false })} className="btn btn-secondary">Cancel</button>
              <button onClick={() => confirmModal.onConfirm()} className="btn btn-danger">Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PipelineBuilder;
