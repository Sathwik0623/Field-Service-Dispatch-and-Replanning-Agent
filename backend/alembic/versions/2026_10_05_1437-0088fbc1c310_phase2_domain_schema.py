"""phase2_domain_schema

Revision ID: 0088fbc1c310
Revises: 5d172eb8ff0a
Create Date: 2026-10-05 14:37:21.915127

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0088fbc1c310'
down_revision: Union[str, Sequence[str], None] = '5d172eb8ff0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'technicians',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('skills', sa.JSON(), nullable=False),
        sa.Column('skill_expertise', sa.JSON(), nullable=False),
        sa.Column('region', sa.String(length=50), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('availability_start', sa.String(length=10), nullable=False),
        sa.Column('availability_end', sa.String(length=10), nullable=False),
        sa.Column('max_daily_hours', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_technicians_is_active'), 'technicians', ['is_active'], unique=False)
    op.create_index(op.f('ix_technicians_region'), 'technicians', ['region'], unique=False)

    op.create_table(
        'service_requests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('customer_name', sa.String(length=100), nullable=False),
        sa.Column('location_name', sa.String(length=100), nullable=False),
        sa.Column('region', sa.String(length=50), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('required_skills', sa.JSON(), nullable=False),
        sa.Column('min_expertise', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='priorityenum'), nullable=False),
        sa.Column('estimated_duration_hours', sa.Float(), nullable=False),
        sa.Column('preferred_start', sa.String(length=10), nullable=False),
        sa.Column('preferred_end', sa.String(length=10), nullable=False),
        sa.Column('status', sa.Enum('UNASSIGNED', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='requeststatusenum'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_requests_priority'), 'service_requests', ['priority'], unique=False)
    op.create_index(op.f('ix_service_requests_region'), 'service_requests', ['region'], unique=False)
    op.create_index(op.f('ix_service_requests_status'), 'service_requests', ['status'], unique=False)

    op.create_table(
        'schedule_versions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('parent_version_id', sa.String(), nullable=True),
        sa.Column('trigger_reason', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['parent_version_id'], ['schedule_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_versions_version_number'), 'schedule_versions', ['version_number'], unique=False)

    op.create_table(
        'assignments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('service_request_id', sa.String(), nullable=False),
        sa.Column('technician_id', sa.String(), nullable=False),
        sa.Column('schedule_version_id', sa.String(), nullable=False),
        sa.Column('start_time', sa.String(length=20), nullable=False),
        sa.Column('end_time', sa.String(length=20), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('score_breakdown', sa.JSON(), nullable=False),
        sa.Column('status', sa.Enum('PROPOSED', 'CONFIRMED', 'DECLINED', 'COMPLETED', 'CANCELLED', name='assignmentstatusenum'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['schedule_version_id'], ['schedule_versions.id'], ),
        sa.ForeignKeyConstraint(['service_request_id'], ['service_requests.id'], ),
        sa.ForeignKeyConstraint(['technician_id'], ['technicians.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assignments_schedule_version_id'), 'assignments', ['schedule_version_id'], unique=False)
    op.create_index(op.f('ix_assignments_service_request_id'), 'assignments', ['service_request_id'], unique=False)
    op.create_index(op.f('ix_assignments_status'), 'assignments', ['status'], unique=False)
    op.create_index(op.f('ix_assignments_technician_id'), 'assignments', ['technician_id'], unique=False)

    op.create_table(
        'approvals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('assignment_id', sa.String(), nullable=True),
        sa.Column('schedule_version_id', sa.String(), nullable=True),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('decision', sa.Enum('APPROVED', 'REJECTED', 'MODIFIED', name='approvaldecisionenum'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ),
        sa.ForeignKeyConstraint(['schedule_version_id'], ['schedule_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approvals_assignment_id'), 'approvals', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_approvals_schedule_version_id'), 'approvals', ['schedule_version_id'], unique=False)

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_event_type'), 'audit_logs', ['event_type'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_audit_logs_event_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index(op.f('ix_approvals_schedule_version_id'), table_name='approvals')
    op.drop_index(op.f('ix_approvals_assignment_id'), table_name='approvals')
    op.drop_table('approvals')

    op.drop_index(op.f('ix_assignments_technician_id'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_status'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_service_request_id'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_schedule_version_id'), table_name='assignments')
    op.drop_table('assignments')

    op.drop_index(op.f('ix_schedule_versions_version_number'), table_name='schedule_versions')
    op.drop_table('schedule_versions')

    op.drop_index(op.f('ix_service_requests_status'), table_name='service_requests')
    op.drop_index(op.f('ix_service_requests_region'), table_name='service_requests')
    op.drop_index(op.f('ix_service_requests_priority'), table_name='service_requests')
    op.drop_table('service_requests')

    op.drop_index(op.f('ix_technicians_region'), table_name='technicians')
    op.drop_index(op.f('ix_technicians_is_active'), table_name='technicians')
    op.drop_table('technicians')
