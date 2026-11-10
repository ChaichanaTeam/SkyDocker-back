"""afd_moderator: unique email

Revision ID: 0145_moderator_email_unique
Revises: 0134_country_borders
Create Date: 2026-11-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0145_moderator_email_unique'
down_revision: Union[str, Sequence[str], None] = '0134_country_borders'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Login and seeding match the email ignoring the case, so the case-insensitive value is unique
    op.execute("CREATE UNIQUE INDEX afd_moderator_email_lower_key ON afd_moderator (lower(email));")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX afd_moderator_email_lower_key;")
