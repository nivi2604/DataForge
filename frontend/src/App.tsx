import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Organizations from './pages/Organizations';
import Workspaces from './pages/Workspaces';
import Projects from './pages/Projects';
import DataSources from './pages/DataSources';
import Executions from './pages/Executions';
import DataQuality from './pages/DataQuality';
import PipelineBuilder from './pages/PipelineBuilder';
import GitHub from './pages/GitHub';
import ProtectedRoute from './routes/ProtectedRoute';
import MainLayout from './layouts/MainLayout';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected Routes */}
        <Route element={<ProtectedRoute />}>
          {/* Main Layout pages */}
          <Route element={<MainLayout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/organizations" element={<Organizations />} />
            <Route path="/workspaces" element={<Workspaces />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/data-sources" element={<DataSources />} />
            <Route path="/executions" element={<Executions />} />
            <Route path="/data-quality" element={<DataQuality />} />
            <Route path="/github" element={<GitHub />} />
          </Route>
          
          {/* Standalone pages (no side nav) */}
          <Route path="/projects/:projectId/pipelines/:pipelineId" element={<PipelineBuilder />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
