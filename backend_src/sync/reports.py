from pydantic import BaseModel, Field


class CatalogSyncReport(BaseModel):
    fetched: int = Field(description="Zones returned by PANSA")
    inserted: int
    updated: int
    unchanged: int
    deleted: int = Field(description="Zones no longer published by PANSA")
    skipped: int = Field(description="Zones with invalid data, see errors")
    parents_linked: int = Field(description="Zones whose parent zone was set or changed")
    terrain_measured: int = Field(description="New or changed zones whose highest ground was measured, needs the terrain sync")
    errors: list[str]


class ActivitySyncReport(BaseModel):
    activations: int = Field(description="AUP/UUP reservations returned by PANSA")
    notams: int = Field(description="NOTAMs returned by PANSA")
    windows: int = Field(description="Activity windows stored after the sync")
    inserted: int
    deleted: int = Field(description="Windows that ended or are no longer published")
    unchanged: int
    zones_with_windows: int
    ignored: int = Field(description="Windows of zones that are not scheduled, e.g. CTR hours of service")
    unmatched: list[str] = Field(description="Designators missing from the zone catalog, e.g. reserved sub-sectors")


class TerrainSyncReport(BaseModel):
    cells: int = Field(description="1° x 1° DEM cells that intersect geo-zones")
    stored: int = Field(description="Tiles that were already stored and were not downloaded again")
    loaded: int = Field(description="Tiles downloaded and stored by this sync")
    sea: list[str] = Field(description="Cells without a DEM tile, open sea")
    terrain_measured: int = Field(description="Zones whose highest ground was measured, e.g. all of them on the first run")
    attribution: str = Field(description="Credit line required by the Copernicus DEM licence")


class BorderSyncReport(BaseModel):
    country_tag: str
    source: str = Field(description="GADM file the border was loaded from")
    polygons: int = Field(description="Separate land areas of the country, e.g. islands and exclaves")
    parts: int = Field(description="Pieces the border was cut into for the point lookup")
    attribution: str = Field(description="Credit line required by the GADM licence")
