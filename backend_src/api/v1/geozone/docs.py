# Additional instruments:
# https://geojson.io/
# https://clupasq.github.io/h3-viewer/

from backend_src.api.shared_schemas import GeoJson
from .schema import ActivitySyncReport, CatalogSyncReport, GeozonePointCollection, TerrainSyncReport

GEOZONE_BBOX = {
    "name": "Get GeoZone from Bounding Box",
    "summary": "Get GeoZone from Bounding Box",
    "description": "Fetches all geo-zones that are within the bounding box provided by the user.\n\n"
                    "The bounding box is defined by two coordinates: the southwest corner and the northeast corner.\n\n"
                    "The response is a GeoJSON collection of geo-zones. Each zone carries:\n\n"
                    "- `active_now`: whether the zone restricts flights right now. Permanent zones are active "
                    "within their validity dates, scheduled ones only in an activity window, "
                    "inherited ones (e.g. ATZ 1 km and 6 km rings) in a window of their parent zone.\n"
                    "- `activity_time`: current and upcoming windows from AUP/UUP and NOTAMs, "
                    "empty for permanent zones.\n"
                    "- `height_rule`: heights above ground for the open category while the zone is active. "
                    "Up to `free_m` a check-in is enough, up to `max_m` the zone manager consent "
                    "or a mission plan is needed.\n\n"
                    "Zone and window limits are in feet above mean sea level, `height_rule` is in metres above ground.",
    "response_model": GeoJson,
    "responses": {
        200: { "description": "GeoJSON collection of geo-zones in the bounding box" },
        404: { "description": "No geo-zone found in the bounding box" }
    }
}

GEOZONE_POINT = {
    "name": "Get GeoZone at a point for the flight height",
    "summary": "Get GeoZone at a point for the flight height",
    "description": "Fetches the geo-zones over the point that a drone flying up to `height_m` above ground can enter.\n\n"
                    "Zone limits are above mean sea level, so the ground elevation at the point is added "
                    "to the flight height. The elevation comes from the Copernicus DEM stored by the terrain sync, "
                    "or from PANSA SRTM where the DEM has no data. Zones starting at or above the top of the flight are left out, "
                    "as well as activity windows reserved only above it, so `active_now` already tells "
                    "whether the zone restricts this flight.\n\n"
                    "The properties of each zone are the same as in the bounding box request. "
                    "An empty collection means no zone restricts the flight.",
    "response_model": GeozonePointCollection,
    "responses": {
        200: { "description": "GeoJSON collection of geo-zones that apply to the flight" },
        404: { "description": "Neither the DEM nor PANSA SRTM has elevation data for the point, e.g. open sea" },
        502: { "description": "PANSA SRTM is needed but unavailable" }
    }
}

GEOZONE_SYNC = {
    "name": "Sync GeoZone catalog from PANSA",
    "summary": "Sync GeoZone catalog from PANSA",
    "description": "Downloads all geo-zones from the PANSA DroneMap API and updates the stored catalog.\n\n"
                    "New zones are added, zones changed in PANSA or by the classifier are updated, "
                    "zones PANSA no longer publishes are removed together with their activity windows. "
                    "Once the terrain sync has stored the DEM, new and changed zones also get their highest ground measured.\n\n"
                    "Requires the `X-Admin-Key` header.",
    "response_model": CatalogSyncReport,
    "responses": {
        200: { "description": "Sync report" },
        401: { "description": "Missing or invalid admin key" },
        502: { "description": "PANSA is unavailable or returned a suspiciously short zone list, nothing was changed" }
    }
}


GEOZONE_ACTIVITY_SYNC = {
    "name": "Sync GeoZone activity from PANSA",
    "summary": "Sync GeoZone activity from PANSA",
    "description": "Downloads AUP/UUP airspace reservations and NOTAMs from the PANSA DroneMap API "
                    "and stores them as activity windows of scheduled zones (TRA, TSA, MRT, D, R, ATZ).\n\n"
                    "Repeating NOTAM schedules are expanded for the next days, ended windows are removed. "
                    "A scheduled zone without a current window is inactive, so run it at least daily: "
                    "AUP/UUP cover only the current day.\n\n"
                    "Run the catalog sync first. Requires the `X-Admin-Key` header.",
    "response_model": ActivitySyncReport,
    "responses": {
        200: { "description": "Sync report" },
        401: { "description": "Missing or invalid admin key" },
        502: { "description": "PANSA is unavailable, nothing was changed" }
    }
}


GEOZONE_TERRAIN_SYNC = {
    "name": "Sync terrain elevation for GeoZone",
    "summary": "Sync terrain elevation for GeoZone",
    "description": "Downloads Copernicus DEM GLO-90 tiles (about 90 m per pixel) for every 1° x 1° cell "
                    "that intersects a stored geo-zone and stores them in PostGIS.\n\n"
                    "Tiles that are already stored are skipped, so after the first run it only adds tiles "
                    "for cells new zones reach into. The first run downloads about 215 MB and takes a minute or two; "
                    "each tile is committed on its own, so an interrupted sync can simply be run again.\n\n"
                    "Afterwards it measures the highest ground of zones that start above ground or have activity windows "
                    "and have no value yet. The catalog sync does the same for new and changed zones once the tiles are stored.\n\n"
                    "Run the catalog sync first. Requires the `X-Admin-Key` header.",
    "response_model": TerrainSyncReport,
    "responses": {
        200: { "description": "Sync report" },
        401: { "description": "Missing or invalid admin key" },
        409: { "description": "No geo-zones stored yet" },
        502: { "description": "Copernicus DEM is unavailable, tiles loaded before the error are kept" }
    }
}
