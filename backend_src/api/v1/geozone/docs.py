# Additional instruments:
# https://geojson.io/
# https://clupasq.github.io/h3-viewer/

from backend_src.api.shared_schemas import GeoJson
from .schema import CatalogSyncReport

GEOZONE_BBOX = {
    "name": "Get GeoZone from Bounding Box",
    "summary": "Get GeoZone from Bounding Box",
    "description": "Fetches all geo-zones that are within the bounding box provided by the user.\n\n"
                    "The bounding box is defined by two coordinates: the southwest corner and the northeast corner.\n\n"
                    "The response is a GeoJSON collection of geo-zones.",
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
