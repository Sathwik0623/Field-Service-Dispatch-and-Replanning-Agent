import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Navigation } from './components/Navigation';
import { DashboardView } from './components/DashboardView';
import { AIPlannerView } from './components/AIPlannerView';
import { ReplanningView } from './components/ReplanningView';
import { RequestsView } from './components/RequestsView';
import { TechniciansView } from './components/TechniciansView';
import { ScheduleView } from './components/ScheduleView';
import type { TabType, HealthResponse } from './types';
import { API_BASE_URL } from './config';

export function App() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/health`);
      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }
      const data: HealthResponse = await res.json();
      setHealth(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to reach API server');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      <Header health={health} loading={loading} error={error} />
      <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="main-content">
        {activeTab === 'dashboard' && <DashboardView health={health} />}
        {activeTab === 'ai_planner' && <AIPlannerView />}
        {activeTab === 'replanning' && <ReplanningView />}
        {activeTab === 'requests' && <RequestsView />}
        {activeTab === 'technicians' && <TechniciansView />}
        {activeTab === 'schedule' && <ScheduleView />}
      </main>

      <footer className="app-footer">
        <div>Field Service Dispatch and Replanning Agent</div>
        <div>FastAPI + SQLAlchemy + AI Agent + React + TypeScript</div>
      </footer>
    </div>
  );
}

export default App;
