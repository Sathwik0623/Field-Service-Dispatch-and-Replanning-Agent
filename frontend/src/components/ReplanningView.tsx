import React, { useState } from 'react';
import { RefreshCw, AlertTriangle, UserX, CheckCircle2 } from 'lucide-react';
import { API_BASE_URL } from '../config';

export const ReplanningView: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [replanData, setReplanData] = useState<any>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Emergency Form State
  const [customerName, setCustomerName] = useState('Metro General Hospital ICU');
  const [locationName, setLocationName] = useState('Medical Wing Substation');
  const [region, setRegion] = useState('NORTH_ZONE');
  const [requiredSkill, setRequiredSkill] = useState('ELECTRICAL');

  // Technician Cancel Form State
  const [cancelTechId, setCancelTechId] = useState('tech_ravi');
  const [cancelReason, setCancelReason] = useState('Severe vehicle engine breakdown');

  const handleTriggerEmergency = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setMessage(null);
      const res = await fetch(`${API_BASE_URL}/api/v1/ai/emergency`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: customerName,
          location_name: locationName,
          region,
          required_skills: [requiredSkill],
          min_expertise: 4,
          estimated_duration_hours: 2.0,
          actor: 'DISPATCHER_UI',
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setReplanData(data.replan_proposal);
      setMessage(`Emergency CRITICAL Request '${data.emergency_request_id}' created! Generated AI Replanning Proposal.`);
    } catch (err: any) {
      setMessage(`Emergency Trigger Failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelTechnician = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setMessage(null);
      const res = await fetch(`${API_BASE_URL}/api/v1/ai/technicians/${cancelTechId}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: cancelReason, actor: 'DISPATCHER_UI' }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setReplanData(data.replan_proposal);
      setMessage(`Technician '${cancelTechId}' marked INACTIVE. Reassigned affected requests in AI Replanning Proposal.`);
    } catch (err: any) {
      setMessage(`Technician Cancellation Failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveReplan = async () => {
    if (!replanData) return;
    try {
      setLoading(true);
      const propId = replanData.proposal.proposal_id;
      const res = await fetch(`${API_BASE_URL}/api/v1/ai/proposals/${propId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actor: 'DISPATCHER_REPLAN' }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setMessage(`Replanned Schedule Version v${data.version_number} Approved & Confirmed!`);
      setReplanData(null);
    } catch (err: any) {
      setMessage(`Replan Approval Failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="section-header-row">
        <div>
          <h2 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <RefreshCw style={{ color: 'var(--accent-cyan)' }} />
            Replanning & Emergency Workspace
          </h2>
          <p className="section-desc">
            Handle emergency priority dispatches and technician cancellations while preserving completed schedule history
          </p>
        </div>
      </div>

      {message && (
        <div
          style={{
            background: message.includes('Failed') ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
            border: message.includes('Failed') ? '1px solid rgba(244, 63, 94, 0.3)' : '1px solid rgba(16, 185, 129, 0.3)',
            color: message.includes('Failed') ? 'var(--accent-rose)' : 'var(--accent-emerald)',
            padding: '0.85rem 1.25rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            fontSize: '0.875rem',
          }}
        >
          {message}
        </div>
      )}

      {/* Trigger Panels Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Panel 1: Emergency Ticket Trigger */}
        <div className="card">
          <h3 style={{ fontSize: '1rem', color: 'var(--accent-rose)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <AlertTriangle size={18} /> Trigger Emergency Ticket (CRITICAL)
          </h3>
          <form onSubmit={handleTriggerEmergency} style={{ display: 'grid', gap: '0.85rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Customer</label>
              <input
                type="text"
                required
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                style={{ width: '100%', padding: '0.45rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Location Name</label>
              <input
                type="text"
                required
                value={locationName}
                onChange={(e) => setLocationName(e.target.value)}
                style={{ width: '100%', padding: '0.45rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Region</label>
                <select
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  style={{ width: '100%', padding: '0.45rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                >
                  <option value="NORTH_ZONE">NORTH_ZONE</option>
                  <option value="SOUTH_ZONE">SOUTH_ZONE</option>
                  <option value="EAST_ZONE">EAST_ZONE</option>
                  <option value="WEST_ZONE">WEST_ZONE</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Required Skill</label>
                <select
                  value={requiredSkill}
                  onChange={(e) => setRequiredSkill(e.target.value)}
                  style={{ width: '100%', padding: '0.45rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                >
                  <option value="ELECTRICAL">ELECTRICAL</option>
                  <option value="HVAC">HVAC</option>
                  <option value="PLUMBING">PLUMBING</option>
                  <option value="NETWORKING">NETWORKING</option>
                  <option value="SECURITY_SYSTEMS">SECURITY_SYSTEMS</option>
                </select>
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ background: 'var(--accent-rose)', marginTop: '0.5rem' }} disabled={loading}>
              <AlertTriangle size={14} />
              <span>Create Emergency & Replan</span>
            </button>
          </form>
        </div>

        {/* Panel 2: Technician Cancellation Simulator */}
        <div className="card">
          <h3 style={{ fontSize: '1rem', color: 'var(--accent-amber)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <UserX size={18} /> Simulate Technician Cancellation
          </h3>
          <form onSubmit={handleCancelTechnician} style={{ display: 'grid', gap: '0.85rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Target Technician ID</label>
              <select
                value={cancelTechId}
                onChange={(e) => setCancelTechId(e.target.value)}
                style={{ width: '100%', padding: '0.45rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
              >
                <option value="tech_ravi">tech_ravi (Ravi Kumar)</option>
                <option value="tech_arun">tech_arun (Arun Patel)</option>
                <option value="tech_priya">tech_priya (Priya Sharma)</option>
                <option value="tech_vikram">tech_vikram (Vikram Singh)</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Cancellation Reason</label>
              <input
                type="text"
                required
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                style={{ width: '100%', padding: '0.45rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ background: 'var(--accent-amber)', marginTop: '0.5rem' }} disabled={loading}>
              <UserX size={14} />
              <span>Mark Inactive & Replan</span>
            </button>
          </form>
        </div>
      </div>

      {/* Replanning Proposal & Change Explanation View */}
      {replanData && (
        <div className="card">
          <div className="section-header-row" style={{ marginBottom: '1rem' }}>
            <div>
              <h3 className="section-title" style={{ color: 'var(--accent-cyan)' }}>Generated AI Replanning Proposal</h3>
              <p className="section-desc">Proposal ID: {replanData.proposal.proposal_id}</p>
            </div>
            <button className="btn btn-primary" onClick={handleApproveReplan} disabled={loading}>
              <CheckCircle2 size={16} />
              <span>Approve Replanned Schedule</span>
            </button>
          </div>

          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Request ID</th>
                  <th>Assigned Tech</th>
                  <th>Time Slot</th>
                  <th>Validation</th>
                  <th>AI Rationale</th>
                </tr>
              </thead>
              <tbody>
                {replanData.validation.validated_assignments.map((item: any) => (
                  <tr key={item.service_request_id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{item.service_request_id}</td>
                    <td style={{ fontWeight: 600 }}>{item.technician_id}</td>
                    <td>{item.proposed_start} - {item.proposed_end}</td>
                    <td>
                      <span className="badge badge-scheduled">VALIDATED</span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{item.rationale}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
