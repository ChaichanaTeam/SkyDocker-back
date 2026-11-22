# Additional instruments:
# https://geojson.io/
# https://clupasq.github.io/h3-viewer/

from backend_src.api.shared_schemas import GeoJson
from .schema import MissionImportReport


IMPORT_MISSIONS = {
    "summary": "Import missions with the PANSA decision",
    "description": "PANSA simulation. Imports missions from an uploaded GeoJSON FeatureCollection of Point features "
                    "(multipart/form-data, field `file`), the point is the home point. "
                    "See `data/missions/example.geojson`.\n\n"
                    "Properties: `external_id` (number of the mission at PANSA), `pilot_email`, "
                    "`drone_serial` (a drone in that pilot's drone park), `flying_privilege` (a1, a2, a3, sts01, sts02), "
                    "`status` (pending, accepted or rejected), `decision_reason` (only and always for rejected), "
                    "`height` (5–120 m), `range` (5–2000 m), `starts_at` and `ends_at` with a time zone, "
                    "`duration` (minutes of flight, at least 5, fits the window); optional `flight_goal`, `description`, "
                    "`spotter_first_name`, `spotter_last_name`, `spotter_phone`. "
                    "The country comes from the point, a1–a3 missions are in the open category, sts ones in the specific.\n\n"
                    "A mission imported before under the same `external_id` is updated, e.g. from pending to accepted, "
                    "unless it was flown. Either every mission of the file is stored or none: "
                    "a wrong one fails the import with all errors, `loc` names the mission by its `external_id`.",
    "response_description": "Created and updated missions",
    "response_model": MissionImportReport,
    "responses": {
        200: { "description": "Missions imported" },
        400: { "description": "Invalid JSON, not a FeatureCollection or no features" },
        422: { "description": "A mission is wrong, nothing was imported: `mission.*` errors for every one" }
    }
}

LIST_MISSIONS = {
    "summary": "List missions",
    "description": "Returns imported missions ordered by id, paginated with `limit` and `offset`.",
    "response_description": "Missions count and list",
    "responses": {
        200: { "description": "Missions returned" }
    }
}

MISSION_BBOX = {
    "name": "Get Mission from Bounding Box",
    "summary": "Get Mission from Bounding Box",
    "description": "Fetches all missions whose home point is within the bounding box.\n\n"
                    "The body is just the bounding box - no user_pos needed.\n\n"
                    "The response is a GeoJSON collection of missions.",
    "response_model": GeoJson,
    "responses": {
        200: { "description": "GeoJSON collection of missions in the bounding box, empty if none" }
    }
}
