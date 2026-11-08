"""postgis: add dem to infrastructure

Revision ID: 0126_postgis_dem
Revises: 0002_pilot_optional_fields
Create Date: 2026-11-01 16:54:15.280731

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2 as ga


# revision identifiers, used by Alembic.
revision: str = '0126_postgis_dem'
down_revision: Union[str, Sequence[str], None] = '0002_pilot_optional_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('geo_zone',sa.Column('terrain_max_m', sa.REAL))
    op.alter_column(
        'geo_zone',
        'terrain_max_m',
        comment="Highest ground inside the zone, metres AMSL from the DEM. Measured only for zones starting above ground or with activity windows, NULL means not measured"
    )

    op.create_table(
        'dem',
        sa.Column('id', sa.BIGINT, primary_key=True),
        sa.Column('tile', sa.VARCHAR(16), nullable=False, comment="Source tile named after its south-west corner, e.g. N52_00_E016_00; a tile is stored whole"),
        sa.Column('rast', ga.Raster(spatial_index=False), nullable=False, comment="Heights in metres above mean sea level, about 90 m per pixel"),
    )

    op.create_table_comment('dem', "Ground elevation model (Copernicus DEM GLO-90): 1° tiles cut into rasters of 100 x 100 pixels")
    op.create_index("idx_dem_tile", "dem", ["tile"])
    op.execute("CREATE INDEX idx_dem_rast ON dem USING GIST (ST_ConvexHull(rast));")



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('geo_zone', 'terrain_max_m')

    op.drop_table("dem")