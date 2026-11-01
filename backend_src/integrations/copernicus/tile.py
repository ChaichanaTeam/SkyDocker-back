from dataclasses import dataclass


@dataclass(frozen=True)
class TileCell:
    """1° x 1° cell of the DEM grid, named after its south-west corner."""

    lat: int
    lon: int

    @property
    def name(self) -> str:
        # e.g. N52_00_E016_00 for the cell 52–53°N, 16–17°E
        lat = f"{'N' if self.lat >= 0 else 'S'}{abs(self.lat):02d}_00"
        lon = f"{'E' if self.lon >= 0 else 'W'}{abs(self.lon):03d}_00"
        return f"{lat}_{lon}"

    @property
    def path(self) -> str:
        key = f"Copernicus_DSM_COG_30_{self.name}_DEM"
        return f"/{key}/{key}.tif"
