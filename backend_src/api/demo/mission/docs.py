# Additional instruments:
# https://geojson.io/
# https://clupasq.github.io/h3-viewer/

from backend_src.api.shared_schemas import GeoJson


IMPORT_MISSIONS = {
    "summary": "Import missions from file",
    "description": "Imports missions from an uploaded GeoJSON FeatureCollection of Point features "
                    "(multipart/form-data, field `file`).\n\n"
                    "Required properties: `category`, `flying_privilege`, `height`, `range`. "
                    "starts_at defaults to now, ends_at defaults to starts_at + 2h. "
                    "Invalid features are skipped and reported in `errors` (first 20).\n\n"
                    "Status is always forced to `created` - ATC changes it later. "
                    "Pass `?reset=true` to first delete all missions and their ATC approvals "
                    "(linked check-ins are kept, only unlinked).",
    "response_description": "Imported and skipped mission counts with skip reasons",
    "responses": {
        200: { "description": "Missions imported" },
        400: { "description": "Invalid JSON, not a FeatureCollection, no features or no valid missions" }
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
