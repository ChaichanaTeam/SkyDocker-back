"""pilot: make name and phone nullable

Revision ID: 0002_pilot_optional_fields
Revises: 0001_baseline
Create Date: 2026-10-30 18:46:44.039929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_pilot_optional_fields'
down_revision: Union[str, Sequence[str], None] = '0001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('pilot', 'first_name', existing_type=sa.VARCHAR(255), nullable=True)
    op.alter_column('pilot', 'last_name', existing_type=sa.VARCHAR(255), nullable=True)
    op.alter_column('pilot', 'phone_number', existing_type=sa.VARCHAR(15), nullable=True)


def downgrade() -> None:
    """Downgrade schema. Fails if any pilot already has these fields empty."""
    op.alter_column('pilot', 'phone_number', existing_type=sa.VARCHAR(15), nullable=False)
    op.alter_column('pilot', 'last_name', existing_type=sa.VARCHAR(255), nullable=False)
    op.alter_column('pilot', 'first_name', existing_type=sa.VARCHAR(255), nullable=False)
