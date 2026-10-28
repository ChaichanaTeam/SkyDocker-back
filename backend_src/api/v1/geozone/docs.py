# Additional instruments:
# https://geojson.io/
# https://clupasq.github.io/h3-viewer/

from backend_src.api.shared_schemas import GeoJson
from .schema import ActivitySyncReport, CatalogSyncReport

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

GEOZONE_SYNC = {
    "name": "Sync GeoZone catalog from PANSA",
    "summary": "Sync GeoZone catalog from PANSA",
    "description": "Downloads all geo-zones from the PANSA DroneMap API and updates the stored catalog.\n\n"
                    "New zones are added, zones changed in PANSA or by the classifier are updated, "
                    "zones PANSA no longer publishes are removed together with their activity windows.\n\n"
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
