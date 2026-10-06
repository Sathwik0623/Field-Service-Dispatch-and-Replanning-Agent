import React, { useState, useEffect } from 'react';
import { Plus, X, MapPin, Clock } from 'lucide-react';
import type { Technician } from '../types';
import { API_BASE_URL } from '../config';

export const TechniciansView: React.FC = () => {
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);

  // Form State
  const [name, setName] = useState('');
  const [region, setRegion] = useState('NORTH_ZONE');
  const [primarySkill, setPrimarySkill] = useState('HVAC');
  const [expertiseLevel, setExpertiseLevel] = useState(4);
  const [availStart, setAvailStart] = useState('08:00');
  const [availEnd, setAvailEnd] = useState('17:00');
  const [maxHours, setMaxHours] = useState(8.0);

  const fetchTechnicians = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/v1/technicians`);
      if (res.ok) {
        setTechnicians(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch technicians:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTechnicians();
  }, []);

  const handleCreateTechnician = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        name,
        skills: [primarySkill],
        skill_expertise: { [primarySkill]: Number(expertiseLevel) },
        region,
        latitude: 12.9716,
        longitude: 77.5946,
        availability_start: availStart,
        availability_end: availEnd,
        max_daily_hours: Number(maxHours),
        is_active: true,
      };

      const res = await fetch(`${API_BASE_URL}/api/v1/technicians`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setShowCreateModal(false);
        setName('');
        fetchTechnicians();
      }
    } catch (err) {
      console.error('Failed to create technician:', err);
    }
  };

  return (
    <div>
      <div className="section-header-row">
        <div>
          <h2 className="section-title">Technician Roster</h2>
          <p className="section-desc">Manage field service technicians, certifications, and shift availability</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
          <Plus size={16} />
          <span>New Technician</span>
        </button>
      </div>

      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Technician Name</th>
              <th>Region</th>
              <th>Skills & Expertise</th>
              <th>Shift Availability</th>
              <th>Max Hours</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center' }}>
                  Loading technicians...
                </td>
              </tr>
            ) : technicians.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center' }}>
                  No technicians found.
                </td>
              </tr>
            ) : (
              technicians.map((tech) => (
                <tr key={tech.id}>
                  <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{tech.id}</td>
                  <td style={{ fontWeight: 600 }}>{tech.name}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <MapPin size={14} style={{ color: 'var(--text-muted)' }} />
                      <span>{tech.region}</span>
                    </div>
                  </td>
                  <td>
                    {tech.skills.map((skill) => (
                      <span key={skill} className="skill-tag">
                        {skill} (Lvl {tech.skill_expertise[skill] || 1})
                      </span>
                    ))}
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Clock size={14} style={{ color: 'var(--text-muted)' }} />
                      <span>
                        {tech.availability_start} - {tech.availability_end}
                      </span>
                    </div>
                  </td>
                  <td>{tech.max_daily_hours}h</td>
                  <td>
                    <span className={`badge ${tech.is_active ? 'badge-scheduled' : 'badge-critical'}`}>
                      {tech.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Technician Modal */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">Register New Technician</h3>
              <button className="close-btn" onClick={() => setShowCreateModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreateTechnician} style={{ display: 'grid', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                  Technician Full Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
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
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Primary Skill
                  </label>
                  <select
                    value={primarySkill}
                    onChange={(e) => setPrimarySkill(e.target.value)}
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
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Expertise Rating (1-5)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={expertiseLevel}
                    onChange={(e) => setExpertiseLevel(Number(e.target.value))}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Max Daily Hours
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={maxHours}
                    onChange={(e) => setMaxHours(Number(e.target.value))}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Shift Start Time
                  </label>
                  <input
                    type="text"
                    value={availStart}
                    onChange={(e) => setAvailStart(e.target.value)}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    Shift End Time
                  </label>
                  <input
                    type="text"
                    value={availEnd}
                    onChange={(e) => setAvailEnd(e.target.value)}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Technician
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
