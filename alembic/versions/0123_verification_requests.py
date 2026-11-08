"""verification: store request contact, document types and keep flag

Revision ID: 0123_verification_requests
Revises: 0134_country_borders
Create Date: 2026-11-08 12:00:00.000000

Fails on purpose if verification tables already have rows: old requests have no
contact data and old document types have no equivalent in the new enum.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0123_verification_requests'
down_revision: Union[str, Sequence[str], None] = '0134_country_borders'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _replace_enum(type_name: str, table: str, column: str, values: Sequence[str]) -> None:
    labels = ", ".join(f"'{value}'" for value in values)

    op.execute(f"ALTER TYPE {type_name} RENAME TO {type_name}_old")
    op.execute(f"CREATE TYPE {type_name} AS ENUM ({labels})")
    op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {type_name} USING {column}::text::{type_name}")
    op.execute(f"DROP TYPE {type_name}_old")


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE verification_request_status ADD VALUE IF NOT EXISTS 'approved'")
    op.execute("ALTER TYPE verification_request_status ADD VALUE IF NOT EXISTS 'withdrawn'")

    _replace_enum(
        "verification_document_type", "verification_document", "document_type",
        ("privilege_a1", "privilege_a2", "privilege_a3", "privilege_sts01", "privilege_sts02", "operator_number"),
    )

    op.add_column('verification_request', sa.Column('first_name', sa.VARCHAR(255), nullable=False, comment="Identity data snapshot at submission"))
    op.add_column('verification_request', sa.Column('last_name', sa.VARCHAR(255), nullable=False))
    op.add_column('verification_request', sa.Column('phone_number', sa.VARCHAR(15), nullable=False, comment="Written to pilot profile on approval"))
    op.add_column('verification_request', sa.Column('pilot_number', sa.VARCHAR(255), nullable=False, comment="Pilot number from the operator registration document. Written to pilot profile on approval"))
    op.add_column('verification_request', sa.Column('keep_documents', sa.BOOLEAN, server_default=sa.false(), nullable=False, comment="Pilot consent to keep documents in the organizer after approval. When false they are deleted"))

    op.create_index(
        "verification_request_one_pending_per_pilot", "verification_request", ["pilot_id"],
        unique=True, postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_unique_constraint(
        "verification_document_request_id_document_type_key", "verification_document", ["request_id", "document_type"]
    )

    op.alter_column(
        'verification_request', 'status',
        comment="Only one pending request per pilot. Closed requests lose their documents: approved ones may first copy them to the organizer"
    )
    op.alter_column(
        'verification_document', 'document_path',
        comment="Object key in the verification bucket of storage, without bucket name"
    )
    op.alter_column(
        'verification_document', 'document_type',
        comment="One document per type: privilege_* training certificates and operator_number registration document"
    )

    op.execute("""
        CREATE OR REPLACE FUNCTION sync_pilot_verification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status = 'approved' AND (TG_OP = 'INSERT' OR OLD.status != 'approved') THEN
                NEW.verified_at := COALESCE(NEW.verified_at, NOW());
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Downgrade schema. Fails if requests or documents use values missing from the old enums."""
    op.execute("""
        CREATE OR REPLACE FUNCTION sync_pilot_verification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status = 'approved' AND (OLD.status IS NULL OR OLD.status != 'approved') THEN
                UPDATE pilot
                SET verified = TRUE
                WHERE id = NEW.pilot_id;

                NEW.verified_at := COALESCE(NEW.verified_at, NOW());

            ELSIF NEW.status = 'rejected' THEN
                UPDATE pilot
                SET verified = FALSE
                WHERE id = NEW.pilot_id;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.alter_column(
        'verification_document', 'document_type',
        comment="Enum to identify document, such as _drone pilot exam_ and _drone operator registration_"
    )
    op.alter_column(
        'verification_document', 'document_path',
        comment="Path for document to which admin need to get access in CDN"
    )
    op.alter_column(
        'verification_request', 'status',
        comment="If status is in complete state [rejected, apporoved] the request will be deleted with associated documents"
    )

    op.drop_constraint("verification_document_request_id_document_type_key", "verification_document", type_="unique")
    op.drop_index("verification_request_one_pending_per_pilot", table_name="verification_request")

    op.drop_column('verification_request', 'keep_documents')
    op.drop_column('verification_request', 'pilot_number')
    op.drop_column('verification_request', 'phone_number')
    op.drop_column('verification_request', 'last_name')
    op.drop_column('verification_request', 'first_name')

    _replace_enum("verification_document_type", "verification_document", "document_type", ("operator_registration", "certificate"))

    # The trigger is declared on UPDATE OF status and blocks changing the column type
    op.execute("DROP TRIGGER trg_sync_pilot_verification ON verification_request")
    op.execute("ALTER TABLE verification_request ALTER COLUMN status DROP DEFAULT")
    _replace_enum("verification_request_status", "verification_request", "status", ("pending", "rejected"))
    op.execute("ALTER TABLE verification_request ALTER COLUMN status SET DEFAULT 'pending'")
    op.execute("""
        CREATE TRIGGER trg_sync_pilot_verification
        BEFORE INSERT OR UPDATE OF status ON verification_request
        FOR EACH ROW
        EXECUTE FUNCTION sync_pilot_verification();
    """)
