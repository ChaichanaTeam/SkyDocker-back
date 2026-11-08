"""baseline: schema from docker/db/init

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-30 18:46:43.335220

The schema up to this point is created by the SQL scripts in docker/db/init.
A fresh volume is stamped with this revision by docker/db/init/99-alembic;
an existing database is stamped once with `alembic stamp 0001_baseline`.
"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '0001_baseline'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
