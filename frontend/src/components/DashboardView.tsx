import React, { useState, useEffect } from 'react';
import { ClipboardList, Users, ShieldAlert, CalendarDays, Play, History, CheckCircle2 } from 'lucide-react';
import type { HealthResponse, ServiceRequest, Technician, ScheduleVersion, AuditLog } from '../types';
import { API_BASE_URL } from '../config';

interface DashboardViewProps {
  health?: HealthResponse | null;
}

export const DashboardView: React.FC<DashboardViewProps> = () => {
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [schedule, setSchedule] = useState<ScheduleVersion | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [generating, setGenerating] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [reqRes, techRes, schedRes, auditRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/requests`),
        fetch(`${API_BASE_URL}/api/v1/technicians`),
        fetch(`${API_BASE_URL}/api/v1/schedule`),
        fetch(`${API_BASE_URL}/api/v1/audit`),
      ]);

      if (reqRes.ok) setRequests(await reqRes.json());
      if (techRes.ok) setTechnicians(await techRes.json());
      if (schedRes.ok) setSchedule(await schedRes.json());
      if (auditRes.ok) setAuditLogs(await auditRes.json());
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleGenerateSchedule = async () => {
    try {
      setGenerating(true);
      setMessage(null);
      const res = await fetch(`${API_BASE_URL}/api/v1/planning/propose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          created_by: 'DISPATCHER_UI',
          trigger_reason: 'Manual Dispatch Generation from Dashboard',
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }

      const data = await res.json();
      setMessage(
        `Generated Schedule Version ${data.version_number} with ${data.assignments.length} proposed assignments!`
      );
      fetchData();
    } catch (err: any) {
      setMessage(`Schedule generation failed: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const totalRequests = requests.length;
  const unassignedRequests = requests.filter((r) => r.status === 'UNASSIGNED').length;
  const criticalRequests = requests.filter((r) => r.priority === 'HIGH' || r.priority === 'CRITICAL').length;
  const activeTechnicians = technicians.filter((t) => t.is_active).length;

  return (
    <div>
      {/* Top Banner & Generation Trigger */}
      <div className="section-header-row" style={{ marginBottom: '1.5rem' }}>
        <div>
          <h2 className="section-title">Field Operations Dispatch Center</h2>
          <p className="section-desc">Deterministic constraint validation, candidate ranking, and schedule versioning</p>
        </div>
        <button className="btn btn-primary" onClick={handleGenerateSchedule} disabled={generating}>
          <Play size={16} />
          <span>{generating ? 'Processing Engine...' : 'Generate Schedule Proposal'}</span>
        </button>
      </div>

      {message && (
        <div
          style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: 'var(--accent-emerald)',
            padding: '0.85rem 1.25rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </div>
      )}

      {/* Metrics Cards */}
      <div className="metrics-grid">
        <div className="card">
          <div className="metric-header">
            <span className="metric-title">Service Requests</span>
            <div className="metric-icon-wrap">
              <ClipboardList size={20} />
            </div>
          </div>
          <div className="metric-value">{totalRequests}</div>
          <div className="metric-subtitle">
            <span style={{ color: 'var(--accent-amber)' }}>{unassignedRequests} Unassigned</span> |{' '}
            <span style={{ color: 'var(--accent-emerald)' }}>{totalRequests - unassignedRequests} Scheduled</span>
          </div>
        </div>

        <div className="card">
          <div className="metric-header">
            <span className="metric-title">High Priority Tickets</span>
            <div className="metric-icon-wrap">
              <ShieldAlert size={20} style={{ color: 'var(--accent-rose)' }} />
            </div>
          </div>
          <div className="metric-value" style={{ color: 'var(--accent-rose)' }}>
            {criticalRequests}
          </div>
          <div className="metric-subtitle">Requires Urgent Assignment</div>
        </div>

        <div className="card">
          <div className="metric-header">
            <span className="metric-title">Technicians Roster</span>
            <div className="metric-icon-wrap">
              <Users size={20} />
            </div>
          </div>
          <div className="metric-value">{technicians.length}</div>
          <div className="metric-subtitle">
            <span style={{ color: 'var(--accent-emerald)' }}>{activeTechnicians} Active Shift Available</span>
          </div>
        </div>

        <div className="card">
          <div className="metric-header">
            <span className="metric-title">Schedule Version</span>
            <div className="metric-icon-wrap">
              <CalendarDays size={20} />
            </div>
          </div>
          <div className="metric-value">v{schedule?.version_number || 1}</div>
          <div className="metric-subtitle">
            {schedule?.assignments?.length || 0} Proposed Assignments
          </div>
        </div>
      </div>

      {/* Audit Log Activity Feed */}
      <div className="card" style={{ marginTop: '2rem' }}>
        <div className="section-header-row" style={{ marginBottom: '1rem' }}>
          <div>
            <h3 className="section-title" style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <History size={18} style={{ color: 'var(--accent-cyan)' }} />
              System Activity & Audit Log
            </h3>
            <p className="section-desc">Tracked dispatch events, requests, and schedule revisions</p>
          </div>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Event Type</th>
                <th>Entity</th>
                <th>Entity ID</th>
                <th>Actor</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                    No audit events recorded yet.
                  </td>
                </tr>
              ) : (
                auditLogs.slice(0, 6).map((log) => (
                  <tr key={log.id}>
                    <td>
                      <span className="badge badge-medium">{log.event_type}</span>
                    </td>
                    <td>{log.entity_type}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{log.entity_id}</td>
                    <td>{log.actor}</td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
