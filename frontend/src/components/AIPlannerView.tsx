import React, { useState } from 'react';
import { Sparkles, AlertTriangle, ShieldCheck, X, HelpCircle, ArrowRight } from 'lucide-react';
import { API_BASE_URL } from '../config';

export const AIPlannerView: React.FC = () => {
  const [proposalData, setProposalData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);

  // Reject Modal
  const [showRejectModal, setShowRejectModal] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>('');

  const handleGenerateAIPlan = async () => {
    try {
      setLoading(true);
      setMessage(null);
      const res = await fetch(`${API_BASE_URL}/api/v1/ai/planning/propose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });

      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }

      const data = await res.json();
      setProposalData(data);
    } catch (err: any) {
      setMessage(`AI Proposal Generation Failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveProposal = async () => {
    if (!proposalData) return;
    try {
      setLoading(true);
      const propId = proposalData.proposal.proposal_id;
      const res = await fetch(`${API_BASE_URL}/api/v1/ai/proposals/${propId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actor: 'DISPATCHER_UI' }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }

      const result = await res.json();
      setMessage(
        `AI Proposal Approved! New Schedule Version v${result.version_number} created with ${result.confirmed_count} confirmed assignments.`
      );
      setProposalData(null);
    } catch (err: any) {
      setMessage(`Approval Failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRejectProposal = async () => {
    if (!proposalData || !rejectReason) return;
    try {
      setLoading(true);
      const propId = proposalData.proposal.proposal_id;
      const res = await fetch(`${API_BASE_URL}/api/v1/ai/proposals/${propId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: rejectReason, actor: 'DISPATCHER_UI' }),
      });

      if (res.ok) {
        setMessage(`AI Proposal Rejected. Reason: ${rejectReason}`);
        setShowRejectModal(false);
        setRejectReason('');
        setProposalData(null);
      }
    } catch (err: any) {
      setMessage(`Rejection Failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Workspace Header */}
      <div className="section-header-row">
        <div>
          <h2 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles style={{ color: 'var(--accent-purple)' }} />
            AI Dispatch Planner & Proposal Agent
          </h2>
          <p className="section-desc">
            Structured LLM schedule proposal generation with deterministic backend hard-constraint validation
          </p>
        </div>
        <button className="btn btn-primary" onClick={handleGenerateAIPlan} disabled={loading}>
          <Sparkles size={16} />
          <span>{loading ? 'AI Planner Thinking...' : 'Generate AI Proposal Plan'}</span>
        </button>
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

      {/* AI Observability Bar */}
      {proposalData && (
        <div
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem 1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.825rem',
          }}
        >
          <div>
            Provider: <strong style={{ color: 'var(--accent-purple)' }}>{proposalData.observability.provider}</strong> | Model: <strong>{proposalData.observability.model_name}</strong> | Latency: <strong>{proposalData.observability.latency_ms} ms</strong>
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <div>Proposed: <strong>{proposalData.observability.proposed_count}</strong></div>
            <div>Validated: <strong style={{ color: 'var(--accent-emerald)' }}>{proposalData.observability.validated_count}</strong></div>
            <div>Rejected by Backend: <strong style={{ color: 'var(--accent-rose)' }}>{proposalData.observability.rejected_count}</strong></div>
          </div>
        </div>
      )}

      {proposalData ? (
        <div style={{ display: 'grid', gap: '1.5rem' }}>
          {/* Reasoning Summary Card */}
          <div className="card">
            <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: 'var(--accent-cyan)' }}>AI Reasoning Summary</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{proposalData.proposal.reasoning_summary}</p>
          </div>

          {/* Validated Assignments Table */}
          <div className="card">
            <div className="section-header-row" style={{ marginBottom: '1rem' }}>
              <h3 className="section-title" style={{ fontSize: '1.1rem' }}>
                Proposed Assignments & Deterministic Validation
              </h3>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button className="btn btn-secondary" onClick={() => setShowRejectModal(true)}>
                  Reject Plan
                </button>
                <button className="btn btn-primary" onClick={handleApproveProposal}>
                  Approve Plan & Confirm
                </button>
              </div>
            </div>

            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Request ID</th>
                    <th>Proposed Tech</th>
                    <th>Proposed Window</th>
                    <th>Backend Validation</th>
                    <th>AI Confidence</th>
                    <th>Score</th>
                    <th>AI Rationale</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Valid Assignments */}
                  {proposalData.validation.validated_assignments.map((item: any) => (
                    <tr key={item.service_request_id}>
                      <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{item.service_request_id}</td>
                      <td style={{ fontWeight: 600 }}>{item.technician_id}</td>
                      <td>{item.proposed_start} - {item.proposed_end}</td>
                      <td>
                        <span className="badge badge-scheduled" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                          <ShieldCheck size={12} /> VALIDATED
                        </span>
                      </td>
                      <td>{(item.confidence * 100).toFixed(0)}%</td>
                      <td style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{item.score}/100</td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: '280px' }}>{item.rationale}</td>
                    </tr>
                  ))}

                  {/* Invalid Assignments flagged by Validator */}
                  {proposalData.validation.invalid_assignments.map((item: any) => (
                    <tr key={item.service_request_id} style={{ background: 'rgba(244, 63, 94, 0.05)' }}>
                      <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{item.service_request_id}</td>
                      <td style={{ fontWeight: 600 }}>{item.technician_id}</td>
                      <td>{item.proposed_start} - {item.proposed_end}</td>
                      <td>
                        <span className="badge badge-critical" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                          <AlertTriangle size={12} /> REJECTED BY BACKEND
                        </span>
                      </td>
                      <td>{(item.confidence * 100).toFixed(0)}%</td>
                      <td>--</td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--accent-rose)' }}>
                        <strong>Validation Rejection:</strong> {item.rejection_reasons?.join('; ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Tradeoffs, Risks & Questions Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
            {/* Tradeoffs */}
            <div className="card">
              <h4 style={{ fontSize: '0.95rem', color: 'var(--accent-purple)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <ArrowRight size={16} /> Trade-off Analysis ("Why This Plan?")
              </h4>
              {proposalData.proposal.tradeoffs.length === 0 ? (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No operational trade-offs required for this plan.</p>
              ) : (
                proposalData.proposal.tradeoffs.map((t: any, i: number) => (
                  <div key={i} style={{ marginBottom: '0.75rem', fontSize: '0.825rem', background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{t.factor}</div>
                    <div style={{ color: 'var(--text-secondary)' }}>{t.tradeoff_explanation}</div>
                  </div>
                ))
              )}
            </div>

            {/* Capacity Risks */}
            <div className="card">
              <h4 style={{ fontSize: '0.95rem', color: 'var(--accent-rose)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <AlertTriangle size={16} /> Capacity & Unassigned Risks
              </h4>
              {proposalData.proposal.risks.length === 0 ? (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No unassigned request risks identified.</p>
              ) : (
                proposalData.proposal.risks.map((r: any, i: number) => (
                  <div key={i} style={{ marginBottom: '0.75rem', fontSize: '0.825rem', background: 'rgba(244, 63, 94, 0.08)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(244, 63, 94, 0.2)' }}>
                    <div style={{ fontWeight: 600, color: 'var(--accent-rose)' }}>{r.category} ({r.severity})</div>
                    <div style={{ color: 'var(--text-primary)' }}>{r.description}</div>
                  </div>
                ))
              )}
            </div>

            {/* Questions */}
            <div className="card">
              <h4 style={{ fontSize: '0.95rem', color: 'var(--accent-amber)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <HelpCircle size={16} /> Clarification Questions for Dispatcher
              </h4>
              {proposalData.proposal.clarification_questions.length === 0 ? (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No missing information questions.</p>
              ) : (
                proposalData.proposal.clarification_questions.map((q: any, i: number) => (
                  <div key={i} style={{ marginBottom: '0.75rem', fontSize: '0.825rem', background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontWeight: 600, color: 'var(--accent-amber)' }}>Target: {q.target_entity}</div>
                    <div style={{ color: 'var(--text-primary)' }}>{q.question}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="placeholder-box">
          <div className="placeholder-icon">
            <Sparkles size={28} />
          </div>
          <h3 className="placeholder-title">AI Dispatch Planner Ready</h3>
          <p className="placeholder-text">
            Click "Generate AI Proposal Plan" to trigger the LLM planning agent. The agent will analyze unassigned requests,
            runtimes, and deterministic evaluations, returning a structured proposal with trade-offs, risk analysis, and backend validation results.
          </p>
        </div>
      )}

      {/* Reject Reason Modal */}
      {showRejectModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '480px' }}>
            <div className="modal-header">
              <h3 className="modal-title">Reject AI Proposal Plan</h3>
              <button className="close-btn" onClick={() => setShowRejectModal(false)}>
                <X size={20} />
              </button>
            </div>
            <div style={{ display: 'grid', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                  Rejection Reason (Required)
                </label>
                <textarea
                  rows={3}
                  required
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="e.g. Over-allocates North region technicians during morning rush."
                  style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button className="btn btn-secondary" onClick={() => setShowRejectModal(false)}>
                  Cancel
                </button>
                <button className="btn btn-primary" style={{ background: 'var(--accent-rose)' }} onClick={handleRejectProposal}>
                  Confirm Rejection
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
