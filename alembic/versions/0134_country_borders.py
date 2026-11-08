"""country: add border polygon

Revision ID: 0134_country_borders
Revises: 0126_postgis_dem
Create Date: 2026-11-02 23:28:50.539751

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2 as ga


# revision identifiers, used by Alembic.
revision: str = '0134_country_borders'
down_revision: Union[str, Sequence[str], None] = '0126_postgis_dem'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "country_border",
        sa.Column("country_id", sa.SMALLINT, sa.ForeignKey("country.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("border_polygon", ga.Geometry("MULTIPOLYGON", srid=4326, spatial_index=False), nullable=False),
        sa.Column("source", sa.VARCHAR(255), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_table_comment(
        "country_border",
        "Source border polygon, country_border_part is rebuilt from it"
    )

    op.create_table(
        "country_border_part",
        sa.Column("id", sa.BIGINT, primary_key=True),
        sa.Column("country_id", sa.SMALLINT, sa.ForeignKey("country.id", ondelete="CASCADE"), nullable=False),
        sa.Column("geom", ga.Geometry("MULTIPOLYGON", srid=4326, spatial_index=False), nullable=False)
    )
    op.create_table_comment(
        "country_border_part",
        'Country border cut into small parts with ST_Subdivide, for fast point lookup'
    )

    op.execute("CREATE INDEX idx_country_border_part_geom ON country_border_part USING gist (geom);")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("country_border")
    op.drop_table("country_border_part")
