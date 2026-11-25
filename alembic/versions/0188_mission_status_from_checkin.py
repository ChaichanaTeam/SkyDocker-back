"""mission: follow the status of its check-in

Revision ID: 0188_mission_status_from_checkin
Revises: 0185_mission_decision
Create Date: 2026-11-22 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0188_mission_status_from_checkin'
down_revision: Union[str, Sequence[str], None] = '0185_mission_decision'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # One flight per mission: the mission shows how its check-in goes, whoever changes the check-in,
    # the API or the cron job that marks overdue check-ins. A cancelled check-in was no flight, the mission waits again
    op.execute("""
        CREATE OR REPLACE FUNCTION mirror_checkin_status_on_mission()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.mission_id IS NULL THEN
                RETURN NEW;
            END IF;

            IF TG_OP = 'UPDATE' AND NEW.status IS NOT DISTINCT FROM OLD.status THEN
                RETURN NEW;
            END IF;

            UPDATE mission
            SET status = CASE NEW.status
                WHEN 'created' THEN 'active'
                WHEN 'cancelled' THEN 'accepted'
                ELSE NEW.status
            END
            WHERE id = NEW.mission_id;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_mirror_checkin_status_on_mission
        AFTER INSERT OR UPDATE OF status ON checkin
        FOR EACH ROW EXECUTE FUNCTION mirror_checkin_status_on_mission()
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER trg_mirror_checkin_status_on_mission ON checkin")
    op.execute("DROP FUNCTION mirror_checkin_status_on_mission()")
