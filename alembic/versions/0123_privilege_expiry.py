"""privilege: add expiry date and daily removal of expired privileges

Revision ID: 0123_privilege_expiry
Revises: 0123_verification_requests
Create Date: 2026-11-08 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0123_privilege_expiry'
down_revision: Union[str, Sequence[str], None] = '0123_verification_requests'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'pilot_to_flying_privileges',
        sa.Column('expires_at', sa.Date, comment="Last day the privilege is valid, set by the moderator on approval. NULL means no expiry")
    )

    op.execute("""
        CREATE OR REPLACE FUNCTION process_expired_privileges()
        RETURNS integer AS $$
        DECLARE
            v_expired_count integer;
        BEGIN
            DELETE FROM pilot_to_flying_privileges
            WHERE expires_at < CURRENT_DATE;

            GET DIAGNOSTICS v_expired_count = ROW_COUNT;

            IF v_expired_count > 0 THEN
                RAISE NOTICE 'Expired privileges removed: %', v_expired_count;
            END IF;

            RETURN v_expired_count;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("SELECT cron.schedule('process-expired-privileges', '0 3 * * *', 'SELECT process_expired_privileges()')")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("SELECT cron.unschedule('process-expired-privileges')")
    op.execute("DROP FUNCTION process_expired_privileges()")
    op.drop_column('pilot_to_flying_privileges', 'expires_at')
