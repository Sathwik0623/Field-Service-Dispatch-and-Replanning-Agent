import React, { useState, useEffect } from 'react';
import { Plus, X, AlertTriangle, CheckCircle, Search } from 'lucide-react';
import type { ServiceRequest, EvaluationResult, CandidateEvaluation } from '../types';
import { API_BASE_URL } from '../config';

export const RequestsView: React.FC = () => {
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // New Request Modal State
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [customerName, setCustomerName] = useState('');
  const [locationName, setLocationName] = useState('');
  const [region, setRegion] = useState('NORTH_ZONE');
  const [requiredSkill, setRequiredSkill] = useState('HVAC');
  const [minExpertise, setMinExpertise] = useState(3);
  const [priority, setPriority] = useState<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'>('MEDIUM');
  const [durationHours, setDurationHours] = useState(2.0);
  const [prefStart, setPrefStart] = useState('09:00');
  const [prefEnd, setPrefEnd] = useState('17:00');

  // Candidate Evaluation Modal State
  const [selectedRequest, setSelectedRequest] = useState<ServiceRequest | null>(null);
  const [evalResult, setEvalResult] = useState<EvaluationResult | null>(null);
  const [evaluating, setEvaluating] = useState<boolean>(false);

  const fetchRequests = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/v1/requests`);
      if (res.ok) {
        setRequests(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch requests:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        customer_name: customerName,
        location_name: locationName,
        region,
        latitude: 12.9716,
        longitude: 77.5946,
        required_skills: [requiredSkill],
        min_expertise: Number(minExpertise),
        priority,
        estimated_duration_hours: Number(durationHours),
        preferred_start: prefStart,
        preferred_end: prefEnd,
      };

      const res = await fetch(`${API_BASE_URL}/api/v1/requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setShowCreateModal(false);
        setCustomerName('');
        setLocationName('');
        fetchRequests();
      }
    } catch (err) {
      console.error('Failed to create request:', err);
    }
  };

  const handleEvaluateCandidates = async (req: ServiceRequest) => {
    try {
      setSelectedRequest(req);
      setEvaluating(true);
      setEvalResult(null);
      const res = await fetch(`${API_BASE_URL}/api/v1/requests/${req.id}/evaluate`, {
        method: 'POST',
      });
      if (res.ok) {
        setEvalResult(await res.json());
      }
    } catch (err) {
      console.error('Failed to evaluate candidates:', err);
    } finally {
      setEvaluating(false);
    }
  };

  const getPriorityBadgeClass = (p: string) => {
    switch (p) {
      case 'CRITICAL':
        return 'badge-critical';
      case 'HIGH':
        return 'badge-high';
      case 'MEDIUM':
        return 'badge-medium';
      default:
        return 'badge-low';
    }
  };

  return (
    <div>
      <div className="section-header-row">
        <div>
          <h2 className="section-title">Service Requests</h2>
          <p className="section-desc">Manage inbound service tickets, skill requirements, and candidate evaluations</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
          <Plus size={16} />
          <span>New Service Request</span>
        </button>
      </div>

      {/* Requests Table */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Customer</th>
              <th>Location / Region</th>
              <th>Priority</th>
              <th>Required Skills</th>
              <th>Min Exp</th>
              <th>Duration</th>
              <th>Time Window</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center' }}>
                  Loading requests...
                </td>
              </tr>
            ) : requests.length === 0 ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center' }}>
                  No requests found.
                </td>
              </tr>
            ) : (
              requests.map((req) => (
                <tr key={req.id}>
                  <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{req.id}</td>
                  <td style={{ fontWeight: 600 }}>{req.customer_name}</td>
                  <td>
                    <div>{req.location_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{req.region}</div>
                  </td>
                  <td>
                    <span className={`badge ${getPriorityBadgeClass(req.priority)}`}>{req.priority}</span>
                  </td>
                  <td>
                    {req.required_skills.map((s) => (
                      <span key={s} className="skill-tag">
                        {s}
                      </span>
                    ))}
                  </td>
                  <td>Lvl {req.min_expertise}</td>
                  <td>{req.estimated_duration_hours}h</td>
                  <td>
                    {req.preferred_start} - {req.preferred_end}
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        req.status === 'SCHEDULED' ? 'badge-scheduled' : 'badge-unassigned'
                      }`}
                    >
                      {req.status}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-secondary" style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }} onClick={() => handleEvaluateCandidates(req)}>
                      <Search size={14} />
                      <span>Evaluate Techs</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Request Modal */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">Create New Service Request</h3>
              <button className="close-btn" onClick={() => setShowCreateModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreateRequest} style={{ display: 'grid', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                  Customer Name
                </label>
                <input
                  type="text"
                  required
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Location Name
                  </label>
                  <input
                    type="text"
                    required
                    value={locationName}
                    onChange={(e) => setLocationName(e.target.value)}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Region
                  </label>
                  <select
                    value={region}
                    onChange={(e) => setRegion(e.target.value)}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                  >
                    <option value="NORTH_ZONE">NORTH_ZONE</option>
                    <option value="SOUTH_ZONE">SOUTH_ZONE</option>
                    <option value="EAST_ZONE">EAST_ZONE</option>
                    <option value="WEST_ZONE">WEST_ZONE</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Required Skill
                  </label>
                  <select
                    value={requiredSkill}
                    onChange={(e) => setRequiredSkill(e.target.value)}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                  >
                    <option value="HVAC">HVAC</option>
                    <option value="ELECTRICAL">ELECTRICAL</option>
                    <option value="PLUMBING">PLUMBING</option>
                    <option value="NETWORKING">NETWORKING</option>
                    <option value="SOLAR">SOLAR</option>
                    <option value="SECURITY_SYSTEMS">SECURITY_SYSTEMS</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Min Expertise (1-5)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={minExpertise}
                    onChange={(e) => setMinExpertise(Number(e.target.value))}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Priority
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value as any)}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Duration (Hours)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={durationHours}
                    onChange={(e) => setDurationHours(Number(e.target.value))}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Preferred Start Time
                  </label>
                  <input
                    type="text"
                    value={prefStart}
                    onChange={(e) => setPrefStart(e.target.value)}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Preferred End Time
                  </label>
                  <input
                    type="text"
                    value={prefEnd}
                    onChange={(e) => setPrefEnd(e.target.value)}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Candidate Evaluation Modal */}
      {selectedRequest && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '760px' }}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Candidate Evaluation Engine</h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                  Target Request: <strong style={{ color: 'var(--text-primary)' }}>{selectedRequest.id}</strong> ({selectedRequest.customer_name})
                </p>
              </div>
              <button className="close-btn" onClick={() => setSelectedRequest(null)}>
                <X size={20} />
              </button>
            </div>

            {evaluating ? (
              <div style={{ textAlign: 'center', padding: '2rem' }}>Evaluating candidate technicians...</div>
            ) : evalResult ? (
              <div>
                {/* Eligible Candidates */}
                <h4 style={{ color: 'var(--accent-emerald)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <CheckCircle size={18} /> Eligible & Ranked Candidates ({evalResult.eligible_candidates.length})
                </h4>
                {evalResult.eligible_candidates.length === 0 ? (
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                    No eligible technicians meet all hard constraints for this request.
                  </p>
                ) : (
                  <div style={{ display: 'grid', gap: '0.75rem', marginBottom: '1.5rem' }}>
                    {evalResult.eligible_candidates.map((cand: CandidateEvaluation, idx: number) => (
                      <div
                        key={cand.technician_id}
                        style={{
                          background: 'var(--bg-secondary)',
                          border: '1px solid var(--border-color)',
                          borderRadius: 'var(--radius-md)',
                          padding: '1rem',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                          <div>
                            <strong>
                              #{idx + 1} {cand.technician_name}
                            </strong>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
                              ({cand.distance_km} km away)
                            </span>
                          </div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                            Score: {cand.score}/100
                          </div>
                        </div>

                        {/* Breakdown Metrics Bar */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.5rem', fontSize: '0.725rem', color: 'var(--text-secondary)' }}>
                          <div>Exp: {cand.score_breakdown.expertise}/30</div>
                          <div>Avail: {cand.score_breakdown.availability}/20</div>
                          <div>Workload: {cand.score_breakdown.workload}/20</div>
                          <div>Prox: {cand.score_breakdown.proximity}/20</div>
                          <div>Nearby: {cand.score_breakdown.nearby_request}/10</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Ineligible Candidates */}
                <h4 style={{ color: 'var(--accent-rose)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <AlertTriangle size={18} /> Ineligible Technicians ({evalResult.ineligible_candidates.length})
                </h4>
                <div style={{ display: 'grid', gap: '0.75rem' }}>
                  {evalResult.ineligible_candidates.map((cand: CandidateEvaluation) => (
                    <div
                      key={cand.technician_id}
                      style={{
                        background: 'rgba(244, 63, 94, 0.05)',
                        border: '1px solid rgba(244, 63, 94, 0.2)',
                        borderRadius: 'var(--radius-md)',
                        padding: '0.85rem 1rem',
                      }}
                    >
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                        {cand.technician_name}
                      </div>
                      <ul style={{ paddingLeft: '1.25rem', fontSize: '0.825rem', color: 'var(--accent-rose)' }}>
                        {cand.reasons.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
