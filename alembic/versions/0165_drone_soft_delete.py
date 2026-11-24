"""drone: add soft delete and unique serial number

Revision ID: 0165_drone_soft_delete
Revises: 0123_privilege_expiry
Create Date: 2026-11-10 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0165_drone_soft_delete'
down_revision: Union[str, Sequence[str], None] = '0123_privilege_expiry'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'drone',
        sa.Column(
            'is_deleted', sa.Boolean, server_default=sa.false(), nullable=False,
            comment="Removed from the drone park by the pilot, kept for the check-ins and missions that refer to it",
        )
    )

    # One physical drone per serial number, compared without case and edge spaces.
    # Fails when the stored drones already repeat a serial number, those have to be fixed by hand first
    op.execute("""
        CREATE UNIQUE INDEX drone_serial_number_unique
        ON drone (lower(btrim(serial_number)))
        WHERE NOT is_deleted
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX drone_serial_number_unique")
    op.drop_column('drone', 'is_deleted')
