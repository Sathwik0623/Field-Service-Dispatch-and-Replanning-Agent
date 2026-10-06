from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine, Base
from app.domain.models import (
    Technician,
    ServiceRequest,
    PriorityEnum,
    RequestStatusEnum,
    ScheduleVersion,
    Assignment,
    AssignmentStatusEnum,
    Approval,
    AuditLog,
    AIProposalRecord,
    Notification,
)


def seed_database(db: Session):
    """
    Populates database with realistic technicians and service requests including deliberate edge cases.
    """
    Base.metadata.create_all(bind=engine)

    # Clear existing data in reverse foreign-key dependency order
    db.query(Notification).delete()
    db.query(AIProposalRecord).delete()
    db.query(Approval).delete()
    db.query(AuditLog).delete()
    db.query(Assignment).delete()
    db.query(ScheduleVersion).delete()
    db.query(ServiceRequest).delete()
    db.query(Technician).delete()
    db.commit()

    # 1. Seed Technicians (7 Technicians)
    technicians = [
        Technician(
            id="tech_ravi",
            name="Ravi Kumar",
            skills=["HVAC", "ELECTRICAL", "PLUMBING"],
            skill_expertise={"HVAC": 4, "ELECTRICAL": 5, "PLUMBING": 3},
            region="NORTH_ZONE",
            latitude=12.9716,
            longitude=77.5946,
            availability_start="08:00",
            availability_end="17:00",
            max_daily_hours=8.0,
            is_active=True,
        ),
        Technician(
            id="tech_arun",
            name="Arun Patel",
            skills=["HVAC", "APPLIANCE"],
            skill_expertise={"HVAC": 3, "APPLIANCE": 4},
            region="NORTH_ZONE",
            latitude=12.9750,
            longitude=77.6000,
            availability_start="09:00",
            availability_end="18:00",
            max_daily_hours=8.0,
            is_active=True,
        ),
        Technician(
            id="tech_priya",
            name="Priya Sharma",
            skills=["ELECTRICAL", "NETWORKING"],
            skill_expertise={"ELECTRICAL": 5, "NETWORKING": 4},
            region="SOUTH_ZONE",
            latitude=12.9141,
            longitude=77.6412,
            availability_start="08:00",
            availability_end="16:00",
            max_daily_hours=7.0,
            is_active=True,
        ),
        Technician(
            id="tech_vikram",
            name="Vikram Singh",
            skills=["PLUMBING", "HVAC"],
            skill_expertise={"PLUMBING": 5, "HVAC": 2},
            region="NORTH_ZONE",
            latitude=12.9800,
            longitude=77.5900,
            availability_start="08:00",
            availability_end="17:00",
            max_daily_hours=8.0,
            is_active=True,
        ),
        Technician(
            id="tech_deepa",
            name="Deepa Menon",
            skills=["NETWORKING", "SECURITY_SYSTEMS"],
            skill_expertise={"NETWORKING": 5, "SECURITY_SYSTEMS": 5},
            region="EAST_ZONE",
            latitude=12.9783,
            longitude=77.6408,
            availability_start="10:00",
            availability_end="19:00",
            max_daily_hours=8.0,
            is_active=True,
        ),
        Technician(
            id="tech_karan",
            name="Karan Malhotra",
            skills=["HVAC", "SOLAR"],
            skill_expertise={"HVAC": 1, "SOLAR": 2},  # Low expertise
            region="NORTH_ZONE",
            latitude=12.9600,
            longitude=77.5800,
            availability_start="08:00",
            availability_end="17:00",
            max_daily_hours=6.0,
            is_active=True,
        ),
        Technician(
            id="tech_suresh",
            name="Suresh Reddy",
            skills=["ELECTRICAL", "HVAC"],
            skill_expertise={"ELECTRICAL": 4, "HVAC": 4},
            region="NORTH_ZONE",
            latitude=12.9700,
            longitude=77.5900,
            availability_start="08:00",
            availability_end="17:00",
            max_daily_hours=8.0,
            is_active=False,  # Inactive technician
        ),
    ]

    for tech in technicians:
        db.add(tech)

    # 2. Seed Service Requests (11 Requests covering edge cases)
    requests = [
        # Edge Case 1: Normal request with several eligible technicians
        ServiceRequest(
            id="req_101",
            customer_name="Acme Corp HQ",
            location_name="MG Road Office Park",
            region="NORTH_ZONE",
            latitude=12.9720,
            longitude=77.5950,
            required_skills=["HVAC"],
            min_expertise=3,
            priority=PriorityEnum.MEDIUM,
            estimated_duration_hours=2.0,
            preferred_start="09:00",
            preferred_end="12:00",
            status=RequestStatusEnum.UNASSIGNED,
        ),
        # Edge Case 2: Wrong skill (Requires SOLAR, only Karan has it but low expertise)
        ServiceRequest(
            id="req_102",
            customer_name="Green Energy Plant",
            location_name="Indiranagar Tech Hub",
            region="NORTH_ZONE",
            latitude=12.9780,
            longitude=77.6380,
            required_skills=["SOLAR"],
            min_expertise=3,  # Karan only has 2 -> Ineligible
            priority=PriorityEnum.HIGH,
            estimated_duration_hours=3.0,
            preferred_start="10:00",
            preferred_end="14:00",
            status=RequestStatusEnum.UNASSIGNED,
        ),
        # Edge Case 3: Insufficient expertise (Requires Electrical level 5, Ravi & Priya have 5)
        ServiceRequest(
            id="req_103",
            customer_name="High Voltage Substation",
            location_name="Koramangala Industrial",
            region="SOUTH_ZONE",
            latitude=12.9350,
            longitude=77.6240,
            required_skills=["ELECTRICAL"],
            min_expertise=5,
            priority=PriorityEnum.HIGH,
            estimated_duration_hours=2.5,
            preferred_start="08:30",
            preferred_end="12:00",
            status=RequestStatusEnum.UNASSIGNED,
        ),
        # Edge Case 4: Technician unavailable (Preferred 18:00-20:00, most tech shifts end by 17:00/18:00)
        ServiceRequest(
            id="req_104",
            customer_name="Late Night Data Center",
            location_name="Whitefield Park",
            region="EAST_ZONE",
            latitude=12.9690,
            longitude=77.7500,
            required_skills=["SECURITY_SYSTEMS"],
            min_expertise=4,
            priority=PriorityEnum.HIGH,
            estimated_duration_hours=2.0,
            preferred_start="18:00",
            preferred_end="20:00",
            status=RequestStatusEnum.UNASSIGNED,
        ),
        # Edge Case 5: Request exceeding daily workload (7.5 hours duration)
        ServiceRequest(
            id="req_105",
            customer_name="Mega Mall Overhaul",
            location_name="Central Mall",
            region="NORTH_ZONE",
            latitude=12.9710,
            longitude=77.5960,
            required_skills=["PLUMBING"],
            min_expertise=3,
            priority=PriorityEnum.MEDIUM,
            estimated_duration_hours=7.5,
            preferred_start="08:00",
            preferred_end="17:00",
            status=RequestStatusEnum.UNASSIGNED,
        ),
        # Edge Case 6: Scheduling conflict target
        ServiceRequest(
            id="req_106",
            customer_name="City Hospital Emergency",
            location_name="Richmond Road",
            region="NORTH_ZONE",
            latitude=12.9680,
            longitude=77.6010,
            required_skills=["ELECTRICAL"],
            min_expertise=4,
            priority=PriorityEnum.CRITICAL,
            estimated_duration_hours=2.0,
            preferred_start="09:00",
            preferred_end="11:00",
            status=RequestStatusEnum.UNASSIGNED,
        ),
        # Edge Case 7: High Priority Critical Request
        ServiceRequest(
            id="req_107",
            customer_name="Fintech Server Room",
            location_name="Outer Ring Road",
            region="EAST_ZONE",
            latitude=12.9770,
            longitude=77.6420,
            required_skills=["NETWORKING"],
            min_expertise=4,
            priority=PriorityEnum.CRITICAL,
            estimated_duration_hours=1.5,
            preferred_start="10:00",
            preferred_end="12:00",
            status=RequestStatusEnum.UNASSIGNED,
        ),
        # Edge Case 8: Standard request with multiple valid candidates
        ServiceRequest(
            id="req_108",
            customer_name="Residential Complex A",
            location_name="Cunningham Road",
            region="NORTH_ZONE",
            latitude=12.9820,
            longitude=77.5920,
            required_skills=["HVAC"],
            min_expertise=2,
            priority=PriorityEnum.LOW,
            estimated_duration_hours=1.5,
            preferred_start="13:00",
            preferred_end="15:00",
            status=RequestStatusEnum.UNASSIGNED,
        ),
        # Edge Case 9 & 10: Nearby pair (REQ-109 and REQ-110 within 1.2km)
        ServiceRequest(
            id="req_109",
            customer_name="Tech Park Tower 1",
            location_name="Commercial Street",
            region="NORTH_ZONE",
            latitude=12.9810,
            longitude=77.6080,
            required_skills=["HVAC"],
            min_expertise=3,
            priority=PriorityEnum.MEDIUM,
            estimated_duration_hours=1.5,
            preferred_start="09:00",
            preferred_end="11:00",
            status=RequestStatusEnum.UNASSIGNED,
        ),
        ServiceRequest(
            id="req_110",
            customer_name="Tech Park Tower 2",
            location_name="Commercial Street Annex",
            region="NORTH_ZONE",
            latitude=12.9825,
            longitude=77.6110,  # ~0.4 km from Tower 1
            required_skills=["HVAC"],
            min_expertise=3,
            priority=PriorityEnum.MEDIUM,
            estimated_duration_hours=1.5,
            preferred_start="11:15",
            preferred_end="13:00",
            status=RequestStatusEnum.UNASSIGNED,
        ),
        # Edge Case 11: No eligible technician at all
        ServiceRequest(
            id="req_111",
            customer_name="Nuclear Research Lab",
            location_name="Restricted Zone",
            region="WEST_ZONE",
            latitude=12.9100,
            longitude=77.5000,
            required_skills=["NUCLEAR_CERTIFIED"],
            min_expertise=5,
            priority=PriorityEnum.CRITICAL,
            estimated_duration_hours=4.0,
            preferred_start="09:00",
            preferred_end="17:00",
            status=RequestStatusEnum.UNASSIGNED,
        ),
    ]

    for req in requests:
        db.add(req)

    db.commit()
    print(f"Database seeded successfully with {len(technicians)} technicians and {len(requests)} service requests.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
