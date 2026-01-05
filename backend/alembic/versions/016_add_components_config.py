"""add components_config to attestation_settings

Revision ID: 016_add_components_config
Revises: 015_add_work_tables
Create Date: 2024-12-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json

revision: str = '016_add_components_config'
down_revision: Union[str, None] = '015_add_work_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_COMPONENTS_CONFIG = {
    "labs": {
        "enabled": True,
        "weight": 60.0,
        "grading_mode": "graded",
        "grading_scale": 10,
        "required_count": 5,
        "bonus_per_extra": 0.4,
        "soft_deadline_days": 7,
        "soft_deadline_penalty": 0.7,
        "hard_deadline_penalty": 0.5
    },
    "tests": {
        "enabled": False,
        "weight": 0.0,
        "grading_scale": 10,
        "count": 0
    },
    "independent_works": {
        "enabled": False,
        "weight": 0.0,
        "grading_scale": 10,
        "count": 0
    },
    "colloquia": {
        "enabled": False,
        "weight": 0.0,
        "grading_scale": 10,
        "count": 0
    },
    "attendance": {
        "enabled": True,
        "weight": 20.0,
        "present_points": 1.0,
        "late_points": 0.5,
        "excused_points": 0.0,
        "absent_points": -0.1
    },
    "activity": {
        "enabled": True,
        "weight": 20.0,
        "participation_points": 0.5
    },
    "final_project": {
        "enabled": False,
        "weight": 0.0,
        "grading_scale": 10
    }
}


def upgrade() -> None:
    op.add_column(
        'attestation_settings',
        sa.Column(
            'components_config',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Гибкая конфигурация компонентов аттестации'
        )
    )
    
    config_json = json.dumps(DEFAULT_COMPONENTS_CONFIG)
    op.execute(
        f"UPDATE attestation_settings SET components_config = '{config_json}'::jsonb"
    )


def downgrade() -> None:
    op.drop_column('attestation_settings', 'components_config')
