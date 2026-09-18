# Additional instruments:
# https://geojson.io/
# https://clupasq.github.io/h3-viewer/

from backend_src.api.shared_schemas import GeoJson


CREATE_CHECKIN = {
    "summary": "Create a check-in",
    "description": "Creates one check-in from the request body, attached to the demo pilot.\n\n"
                    "The demo pilot and the demo country (Poland) are created on first use.\n\n"
                    "starts_at defaults to now, ends_at defaults to starts_at + 1h. "
                    "h3_index is filled by a database trigger.",
    "response_description": "Created check-in id, its point and h3 index",
    "responses": {
        200: { "description": "Check-in created" }
    }
}

CREATE_RANDOM_CHECKINS = {
    "summary": "Create random check-ins",
    "description": "Creates `count` check-ins with random position, height, range and time "
                    "inside the Warsaw bounding box, attached to the demo pilot.\n\n"
                    "Pass `?reset=true` to first delete the demo pilot's existing check-ins "
                    "(the pilot row and its flight_time are kept).",
    "response_description": "Created check-ins with their points and h3 indexes",
    "responses": {
        200: { "description": "Check-ins created" }
    }
}

END_CHECKIN = {
    "summary": "End a check-in",
    "description": "Ends a check-in by id.\n\n"
                    "The status becomes `ended_intime` if ended before ends_at, otherwise `late_end`.",
    "response_description": "Check-in id and its new status",
    "responses": {
        200: { "description": "Check-in ended" },
        404: { "description": "Check-in not found" },
        409: { "description": "Check-in is already in a terminal status" }
    }
}

CHECKIN_BBOX = {
    "name": "Get Check-in from Bounding Box",
    "summary": "Get Check-in from Bounding Box",
    "description": "Fetches all check-ins whose home point is within the bounding box.\n\n"
                    "Unlike /api/v1, the body is just the bounding box - no user_pos needed.\n\n"
                    "The response is a GeoJSON collection of check-ins.",
    "response_model": GeoJson,
    "responses": {
        200: { "description": "GeoJSON collection of check-ins in the bounding box, empty if none" }
    }
}
