# Additional instruments:
# https://geojson.io/
# https://clupasq.github.io/h3-viewer/

from backend_src.api.shared_schemas import GeoJson

CHECKIN_BBOX = {
    "name": "Get Check-in from Bounding Box",
    "summary": "Get Check-in from Bounding Box",
    "description": "Fetches all check-ins that are within the bounding box provided by the user.\n\n"
                    "The bounding box is defined by two coordinates: the southwest corner and the northeast corner.\n\n"
                    "The response is a GeoJSON collection of check-ins.",
    "response_model": GeoJson,
    "responses": {
        200: { "description": "GeoJSON collection of check-ins in the bounding box" },
        404: { "description": "No check-in found in the bounding box" }
    }
}