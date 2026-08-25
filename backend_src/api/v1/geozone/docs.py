# Additional instruments:
# https://geojson.io/
# https://clupasq.github.io/h3-viewer/

from backend_src.api.shared_schemas import GeoJson

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