import React from 'react';
import { LayoutDashboard, Sparkles, RefreshCw, ClipboardList, Users, CalendarDays } from 'lucide-react';
import type { TabType } from '../types';

interface NavigationProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
}

export const Navigation: React.FC<NavigationProps> = ({ activeTab, setActiveTab }) => {
  const tabs: { id: TabType; label: string; icon: React.ReactNode; isAI?: boolean }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
    { id: 'ai_planner', label: 'AI Planner', icon: <Sparkles size={18} />, isAI: true },
    { id: 'replanning', label: 'Replanning & Emergency', icon: <RefreshCw size={18} />, isAI: true },
    { id: 'requests', label: 'Requests', icon: <ClipboardList size={18} /> },
    { id: 'technicians', label: 'Technicians', icon: <Users size={18} /> },
    { id: 'schedule', label: 'Schedule', icon: <CalendarDays size={18} /> },
  ];

  return (
    <nav className="app-nav">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => setActiveTab(tab.id)}
        >
          {tab.icon}
          <span>{tab.label}</span>
          {tab.isAI && (
            <span
              style={{
                fontSize: '0.65rem',
                padding: '1px 5px',
                borderRadius: '8px',
                background: 'rgba(139, 92, 246, 0.2)',
                color: 'var(--accent-purple)',
                border: '1px solid rgba(139, 92, 246, 0.4)',
                fontWeight: 600,
              }}
            >
              AI
            </span>
          )}
        </button>
      ))}
    </nav>
  );
};
