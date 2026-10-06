import math
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    expertise: float = 0.0
    availability: float = 0.0
    workload: float = 0.0
    proximity: float = 0.0
    nearby_request: float = 0.0
    total: float = 0.0


class CandidateEvaluation(BaseModel):
    technician_id: str
    technician_name: str
    eligible: bool
    reasons: List[str] = Field(default_factory=list)
    score: float = 0.0
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    distance_km: float = 0.0


class EvaluationResult(BaseModel):
    request_id: str
    eligible_candidates: List[CandidateEvaluation] = Field(default_factory=list)
    ineligible_candidates: List[CandidateEvaluation] = Field(default_factory=list)


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points on the earth.
    """
    R = 6371.0  # Earth radius in kilometers

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return round(distance, 2)


def parse_time_to_minutes(time_str: Optional[str]) -> int:
    """Helper to convert HH:MM string into minutes from midnight."""
    if not time_str:
        return 480  # Default 08:00 AM
    try:
        parts = str(time_str).split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 480


def get_obj_val(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely extracts attribute or dict key, falling back to default if None."""
    if isinstance(obj, dict):
        val = obj.get(attr)
    else:
        val = getattr(obj, attr, None)
    return val if val is not None else default


def get_assignment_duration_hours(a: Any) -> float:
    """Helper to get actual duration in hours from assignment object or start/end times."""
    dur = get_obj_val(a, "duration_hours")
    if dur is not None:
        return float(dur)
    
    start_str = str(get_obj_val(a, "start_time", "08:00"))
    end_str = str(get_obj_val(a, "end_time", "10:00"))
    start_min = parse_time_to_minutes(start_str[-5:])
    end_min = parse_time_to_minutes(end_str[-5:])
    if end_min > start_min:
        return round((end_min - start_min) / 60.0, 2)
    return 2.0


def get_assignment_coordinates(a: Any, fallback_lat: float, fallback_lon: float) -> Tuple[float, float]:
    """Helper to extract latitude and longitude from an assignment or its linked service request."""
    lat = get_obj_val(a, "latitude")
    lon = get_obj_val(a, "longitude")
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    
    # Check linked service_request relation
    sr = get_obj_val(a, "service_request")
    if sr:
        sr_lat = get_obj_val(sr, "latitude")
        sr_lon = get_obj_val(sr, "longitude")
        if sr_lat is not None and sr_lon is not None:
            return float(sr_lat), float(sr_lon)
            
    return fallback_lat, fallback_lon


class AssignmentEngine:
    """
    Deterministic assignment evaluation and ranking engine.
    Applies hard constraints filtering BEFORE scoring eligible candidates.
    """

    @staticmethod
    def evaluate_candidates(
        request: Any,
        technicians: List[Any],
        existing_assignments: List[Any] = None,
    ) -> EvaluationResult:
        if existing_assignments is None:
            existing_assignments = []

        eligible_list: List[CandidateEvaluation] = []
        ineligible_list: List[CandidateEvaluation] = []

        req_id = get_obj_val(request, "id", "unknown")
        req_region = get_obj_val(request, "region", "")
        req_skills = get_obj_val(request, "required_skills", [])
        req_min_expertise = get_obj_val(request, "min_expertise", 1)
        req_lat = get_obj_val(request, "latitude", 0.0)
        req_lon = get_obj_val(request, "longitude", 0.0)
        req_pref_start = get_obj_val(request, "preferred_start", "08:00")
        req_pref_end = get_obj_val(request, "preferred_end", "17:00")
        req_duration = get_obj_val(request, "estimated_duration_hours", 2.0)

        req_start_min = parse_time_to_minutes(req_pref_start)
        req_end_min = parse_time_to_minutes(req_pref_end)

        for tech in technicians:
            reasons: List[str] = []
            tech_id = get_obj_val(tech, "id", "")
            tech_name = get_obj_val(tech, "name", "")
            is_active = get_obj_val(tech, "is_active", True)
            tech_skills = get_obj_val(tech, "skills", [])
            tech_expertise_map = get_obj_val(tech, "skill_expertise", {})
            tech_region = get_obj_val(tech, "region", "")
            tech_avail_start = get_obj_val(tech, "availability_start", "08:00")
            tech_avail_end = get_obj_val(tech, "availability_end", "17:00")
            max_daily_hours = get_obj_val(tech, "max_daily_hours", 8.0)
            tech_lat = get_obj_val(tech, "latitude", 0.0)
            tech_lon = get_obj_val(tech, "longitude", 0.0)

            tech_start_min = parse_time_to_minutes(tech_avail_start)
            tech_end_min = parse_time_to_minutes(tech_avail_end)

            # -------------------------------------------------------------
            # HARD CONSTRAINTS CHECKING
            # -------------------------------------------------------------
            # Constraint 1: Active status
            if not is_active:
                reasons.append("Technician is currently INACTIVE.")

            # Constraint 2: Required skill check
            missing_skills = [skill for skill in req_skills if skill not in tech_skills]
            if missing_skills:
                reasons.append(f"Missing required skill(s): {', '.join(missing_skills)}.")

            # Constraint 3: Skill expertise level
            for skill in req_skills:
                if skill in tech_skills:
                    expertise_level = tech_expertise_map.get(skill, 0)
                    if expertise_level < req_min_expertise:
                        reasons.append(
                            f"Insufficient expertise for {skill}: Has level {expertise_level}, requires minimum {req_min_expertise}."
                        )

            # Constraint 4: Region match
            if tech_region != req_region:
                reasons.append(f"Region mismatch: Tech operates in {tech_region}, request requires {req_region}.")

            # Constraint 5: Availability shift window
            if req_start_min < tech_start_min or req_end_min > tech_end_min:
                reasons.append(
                    f"Request window ({req_pref_start}-{req_pref_end}) outside tech shift availability ({tech_avail_start}-{tech_avail_end})."
                )

            # Constraint 6 & 7: Calculate current workload and check schedule conflicts
            tech_assignments = [a for a in existing_assignments if get_obj_val(a, "technician_id") == tech_id]
            current_workload_hours = sum(get_assignment_duration_hours(a) for a in tech_assignments)

            if current_workload_hours + req_duration > max_daily_hours:
                reasons.append(
                    f"Workload limit exceeded: Current {current_workload_hours}h + New {req_duration}h > Daily Max {max_daily_hours}h."
                )

            # Schedule Overlap Check
            has_overlap = False
            for assignment in tech_assignments:
                a_start_min = parse_time_to_minutes(get_obj_val(assignment, "start_time", "00:00")[-5:])
                a_end_min = parse_time_to_minutes(get_obj_val(assignment, "end_time", "00:00")[-5:])
                if max(req_start_min, a_start_min) < min(req_end_min, a_end_min):
                    has_overlap = True
                    break

            if has_overlap:
                reasons.append("Time window conflicts with technician's existing scheduled assignment.")

            # Calculate distance
            dist_km = calculate_haversine_distance(tech_lat, tech_lon, req_lat, req_lon)

            if reasons:
                ineligible_list.append(
                    CandidateEvaluation(
                        technician_id=tech_id,
                        technician_name=tech_name,
                        eligible=False,
                        reasons=reasons,
                        distance_km=dist_km,
                    )
                )
            else:
                # -------------------------------------------------------------
                # DETERMINISTIC SCORING MODEL FOR ELIGIBLE CANDIDATES
                # -------------------------------------------------------------
                # 1. Expertise Score (max 30 pts)
                max_exp = max([tech_expertise_map.get(s, 0) for s in req_skills], default=req_min_expertise)
                expertise_score = min(30.0, round((max_exp / max(1, req_min_expertise)) * 20.0, 1))

                # 2. Availability Fit Score (max 20 pts)
                avail_delta_hours = (req_start_min - tech_start_min) / 60.0
                availability_score = max(0.0, round(20.0 - (avail_delta_hours * 2.0), 1))

                # 3. Workload Balance Score (max 20 pts)
                remaining_workload_ratio = max(0.0, 1.0 - (current_workload_hours / max(1.0, max_daily_hours)))
                workload_score = round(remaining_workload_ratio * 20.0, 1)

                # 4. Proximity Score (max 20 pts)
                proximity_score = max(0.0, round(20.0 - (dist_km * 2.0), 1))

                # 5. Nearby Request Opportunity Score (max 10 pts)
                nearby_score = 0.0
                for a in tech_assignments:
                    a_lat, a_lon = get_assignment_coordinates(a, tech_lat, tech_lon)
                    a_dist = calculate_haversine_distance(a_lat, a_lon, req_lat, req_lon)
                    if a_dist <= 3.0:
                        nearby_score = 10.0
                        break

                total_score = round(
                    expertise_score + availability_score + workload_score + proximity_score + nearby_score,
                    1,
                )

                breakdown = ScoreBreakdown(
                    expertise=expertise_score,
                    availability=availability_score,
                    workload=workload_score,
                    proximity=proximity_score,
                    nearby_request=nearby_score,
                    total=total_score,
                )

                eligible_list.append(
                    CandidateEvaluation(
                        technician_id=tech_id,
                        technician_name=tech_name,
                        eligible=True,
                        reasons=[],
                        score=total_score,
                        score_breakdown=breakdown,
                        distance_km=dist_km,
                    )
                )

        # Sort eligible candidates descending by total score
        eligible_list.sort(key=lambda x: x.score, reverse=True)

        return EvaluationResult(
            request_id=req_id,
            eligible_candidates=eligible_list,
            ineligible_candidates=ineligible_list,
        )
