export type TabType = 'dashboard' | 'ai_planner' | 'replanning' | 'requests' | 'technicians' | 'schedule';

export type PriorityType = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type RequestStatusType = 'UNASSIGNED' | 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
export type AssignmentStatusType = 'PROPOSED' | 'CONFIRMED' | 'DECLINED' | 'COMPLETED' | 'CANCELLED';

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  database: string;
}

export interface Technician {
  id: string;
  name: string;
  skills: string[];
  skill_expertise: Record<string, number>;
  region: string;
  latitude: number;
  longitude: number;
  availability_start: string;
  availability_end: string;
  max_daily_hours: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ServiceRequest {
  id: string;
  customer_name: string;
  location_name: string;
  region: string;
  latitude: number;
  longitude: number;
  required_skills: string[];
  min_expertise: number;
  priority: PriorityType;
  estimated_duration_hours: number;
  preferred_start: string;
  preferred_end: string;
  status: RequestStatusType;
  created_at?: string;
  updated_at?: string;
}

export interface ScoreBreakdown {
  expertise: number;
  availability: number;
  workload: number;
  proximity: number;
  nearby_request: number;
  total: number;
}

export interface CandidateEvaluation {
  technician_id: string;
  technician_name: string;
  eligible: boolean;
  reasons: string[];
  score: number;
  score_breakdown: ScoreBreakdown;
  distance_km: number;
}

export interface EvaluationResult {
  request_id: string;
  eligible_candidates: CandidateEvaluation[];
  ineligible_candidates: CandidateEvaluation[];
}

export interface Assignment {
  id: string;
  service_request_id: string;
  technician_id: string;
  schedule_version_id: string;
  start_time: string;
  end_time: string;
  score: number;
  score_breakdown: ScoreBreakdown;
  status: AssignmentStatusType;
  created_at?: string;
  updated_at?: string;
}

export interface ScheduleVersion {
  id: string;
  version_number: number;
  parent_version_id?: string | null;
  trigger_reason: string;
  created_by: string;
  created_at: string;
  assignments: Assignment[];
}

export interface AuditLog {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  actor: string;
  metadata_json: Record<string, any>;
  timestamp: string;
}
