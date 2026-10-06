import React, { useState, useEffect } from 'react';
import { X, Award } from 'lucide-react';
import type { ScheduleVersion, Assignment, Technician } from '../types';
import { API_BASE_URL } from '../config';

export const ScheduleView: React.FC = () => {
  const [schedule, setSchedule] = useState<ScheduleVersion | null>(null);
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Selected Assignment for Explanation Modal
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);

  const fetchScheduleAndTechs = async () => {
    try {
      setLoading(true);
      const [schedRes, techRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/schedule`),
        fetch(`${API_BASE_URL}/api/v1/technicians`),
      ]);
      if (schedRes.ok) setSchedule(await schedRes.json());
      if (techRes.ok) setTechnicians(await techRes.json());
    } catch (err) {
      console.error('Failed to load schedule:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScheduleAndTechs();
  }, []);

  const hours = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'];

  const getTechName = (techId: string) => {
    const t = technicians.find((tech) => tech.id === techId);
    return t ? t.name : techId;
  };

  return (
    <div>
      <div className="section-header-row">
        <div>
          <h2 className="section-title">Dispatch Schedule Timeline & Versioning</h2>
          <p className="section-desc">
            Active Schedule Version:{' '}
            <strong style={{ color: 'var(--accent-cyan)' }}>
              v{schedule?.version_number || 1}
            </strong>{' '}
            ({schedule?.assignments?.length || 0} assignments)
          </p>
        </div>
      </div>

      {/* Timeline Grid */}
      <div className="timeline-container">
        <div className="timeline-header-hours">
          <div style={{ textAlign: 'left', fontWeight: 600, color: 'var(--text-primary)' }}>Technician</div>
          {hours.map((h) => (
            <div key={h}>{h}</div>
          ))}
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>Loading timeline...</div>
        ) : technicians.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>No technicians in roster.</div>
        ) : (
          technicians.map((tech) => {
            const techAssignments =
              schedule?.assignments?.filter((a) => a.technician_id === tech.id) || [];

            return (
              <div key={tech.id} className="timeline-row">
                <div className="timeline-tech-info">
                  <div>{tech.name}</div>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>{tech.region}</div>
                </div>

                <div style={{ gridColumn: '2 / 12', display: 'flex', gap: '0.5rem', position: 'relative' }}>
                  {techAssignments.length === 0 ? (
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic', padding: '0.4rem 0' }}>
                      No assignments scheduled for shift ({tech.availability_start}-{tech.availability_end})
                    </div>
                  ) : (
                    techAssignments.map((assignment) => (
                      <div
                        key={assignment.id}
                        className="timeline-assignment-block"
                        onClick={() => setSelectedAssignment(assignment)}
                        title="Click to view Ranking Rationale & Score Breakdown"
                      >
                        <div style={{ fontWeight: 600 }}>{assignment.service_request_id}</div>
                        <div>
                          {assignment.start_time} - {assignment.end_time} | Score: {assignment.score}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Ranking Explanation Drawer / Modal */}
      {selectedAssignment && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '640px' }}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Award style={{ color: 'var(--accent-amber)' }} />
                  Ranking Rationale & Score Breakdown
                </h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                  Assignment ID: <strong style={{ color: 'var(--text-primary)' }}>{selectedAssignment.id}</strong>
                </p>
              </div>
              <button className="close-btn" onClick={() => setSelectedAssignment(null)}>
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'grid', gap: '1rem' }}>
              <div style={{ background: 'var(--bg-secondary)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Assigned Technician</div>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{getTechName(selectedAssignment.technician_id)}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Service Request ID</div>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{selectedAssignment.service_request_id}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Time Slot Window</div>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{selectedAssignment.start_time} - {selectedAssignment.end_time}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Overall Match Score</div>
                  <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--accent-cyan)' }}>
                    {selectedAssignment.score} / 100
                  </div>
                </div>
              </div>

              {/* Transparent Sub-Score Bars */}
              <div>
                <h4 style={{ fontSize: '0.9rem', marginBottom: '0.85rem', color: 'var(--text-primary)' }}>
                  Transparent Scoring Factor Breakdown
                </h4>

                <div className="score-metric-row">
                  <div className="score-metric-label">
                    <span>Skill Expertise Level</span>
                    <span>{selectedAssignment.score_breakdown.expertise} / 30 pts</span>
                  </div>
                  <div className="score-bar-bg">
                    <div className="score-bar-fill" style={{ width: `${(selectedAssignment.score_breakdown.expertise / 30) * 100}%` }} />
                  </div>
                </div>

                <div className="score-metric-row">
                  <div className="score-metric-label">
                    <span>Shift Availability Fit</span>
                    <span>{selectedAssignment.score_breakdown.availability} / 20 pts</span>
                  </div>
                  <div className="score-bar-bg">
                    <div className="score-bar-fill" style={{ width: `${(selectedAssignment.score_breakdown.availability / 20) * 100}%` }} />
                  </div>
                </div>

                <div className="score-metric-row">
                  <div className="score-metric-label">
                    <span>Workload Balance (Remaining Capacity)</span>
                    <span>{selectedAssignment.score_breakdown.workload} / 20 pts</span>
                  </div>
                  <div className="score-bar-bg">
                    <div className="score-bar-fill" style={{ width: `${(selectedAssignment.score_breakdown.workload / 20) * 100}%` }} />
                  </div>
                </div>

                <div className="score-metric-row">
                  <div className="score-metric-label">
                    <span>Geographical Proximity</span>
                    <span>{selectedAssignment.score_breakdown.proximity} / 20 pts</span>
                  </div>
                  <div className="score-bar-bg">
                    <div className="score-bar-fill" style={{ width: `${(selectedAssignment.score_breakdown.proximity / 20) * 100}%` }} />
                  </div>
                </div>

                <div className="score-metric-row">
                  <div className="score-metric-label">
                    <span>Nearby Request Opportunity</span>
                    <span>{selectedAssignment.score_breakdown.nearby_request} / 10 pts</span>
                  </div>
                  <div className="score-bar-bg">
                    <div className="score-bar-fill" style={{ width: `${(selectedAssignment.score_breakdown.nearby_request / 10) * 100}%` }} />
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: '0.5rem' }}>
                Note: Candidate passed all deterministic hard constraints (Skill, Expertise, Active Status, Region, Availability, Workload Limit) before score ranking.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
