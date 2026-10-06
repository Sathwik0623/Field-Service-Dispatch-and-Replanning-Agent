import React, { useState, useEffect } from 'react';
import { Activity, Server, Database, Bell, X } from 'lucide-react';
import type { HealthResponse } from '../types';
import { API_BASE_URL } from '../config';

interface HeaderProps {
  health: HealthResponse | null;
  loading: boolean;
  error: string | null;
}

export const Header: React.FC<HeaderProps> = ({ health, loading, error }) => {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [showNotifModal, setShowNotifModal] = useState<boolean>(false);

  const fetchNotifications = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/notifications`);
      if (res.ok) {
        setNotifications(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusDotClass = () => {
    if (loading) return 'checking';
    if (error || !health || health.status !== 'ok') return 'disconnected';
    return 'connected';
  };

  const getStatusText = () => {
    if (loading) return 'Connecting...';
    if (error) return 'API Offline';
    if (health?.status === 'ok') return `API Online (DB: ${health.database})`;
    return 'Unknown Status';
  };

  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-icon">
          <Activity size={20} />
        </div>
        <div>
          <span className="brand-title">FieldOps AI</span>
        </div>
      </div>

      <div className="status-bar">
        {/* Mock Notifications Inbox */}
        <button
          className="status-pill"
          onClick={() => setShowNotifModal(true)}
          style={{ cursor: 'pointer', background: 'var(--bg-card)', border: '1px solid var(--border-color)', color: 'white' }}
        >
          <Bell size={14} style={{ color: 'var(--accent-cyan)' }} />
          <span>Notifications ({notifications.length})</span>
        </button>

        <div className="status-pill">
          <Server size={14} style={{ color: 'var(--text-secondary)' }} />
          <span style={{ color: 'var(--text-secondary)' }}>{API_BASE_URL}</span>
        </div>

        <div className="status-pill">
          <Database size={14} style={{ color: 'var(--text-secondary)' }} />
          <span className={`status-dot ${getStatusDotClass()}`} />
          <span>{getStatusText()}</span>
        </div>
      </div>

      {/* Notifications Modal */}
      {showNotifModal && (
        <div className="modal-overlay" onClick={() => setShowNotifModal(false)}>
          <div className="modal-content" style={{ maxWidth: '560px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Bell style={{ color: 'var(--accent-cyan)' }} />
                Mock Notification Inbox
              </h3>
              <button
                className="close-btn"
                onClick={() => setShowNotifModal(false)}
                title="Close notifications"
                aria-label="Close notifications"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '0.35rem 0.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'grid', gap: '0.75rem', maxHeight: '60vh', overflowY: 'auto' }}>
              {notifications.length === 0 ? (
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1rem' }}>
                  No notifications recorded.
                </p>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    style={{
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '0.85rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <strong style={{ fontSize: '0.875rem', color: 'var(--accent-cyan)' }}>{n.title}</strong>
                      <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
                        {new Date(n.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.825rem', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>{n.message}</p>
                    <div style={{ fontSize: '0.725rem', color: 'var(--text-secondary)' }}>
                      Recipient: {n.recipient_type} ({n.recipient_id})
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
