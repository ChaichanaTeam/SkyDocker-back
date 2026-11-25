"""mission: add external id, rejected status and decision reason

Revision ID: 0185_mission_decision
Revises: 0145_moderator_email_unique
Create Date: 2026-11-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0185_mission_decision'
down_revision: Union[str, Sequence[str], None] = '0145_moderator_email_unique'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE mission_status ADD VALUE IF NOT EXISTS 'rejected'")

    op.add_column(
        'mission',
        sa.Column(
            'external_id', sa.VARCHAR(255),
            comment="Number of the mission at PANSA, set by the import. A repeated import updates the mission with it",
        )
    )
    op.create_unique_constraint('mission_external_id_key', 'mission', ['external_id'])

    op.add_column(
        'mission',
        sa.Column('decision_reason', sa.TEXT, comment="Why PANSA rejected the mission, shown to the pilot")
    )


def downgrade() -> None:
    """Downgrade schema. Rejected missions become cancelled; the enum keeps the 'rejected' label,
    Postgres drops enum labels only by rebuilding the type that check-ins use as well."""
    op.execute("UPDATE mission SET status = 'cancelled' WHERE status = 'rejected'")

    op.drop_column('mission', 'decision_reason')
    op.drop_constraint('mission_external_id_key', 'mission', type_='unique')
    op.drop_column('mission', 'external_id')
