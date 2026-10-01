# Additional instruments:
# https://geojson.io/
# https://clupasq.github.io/h3-viewer/

from backend_src.api.shared_schemas import GeoJson


CREATE_CHECKIN = {
    "summary": "Create a check-in",
    "description": "Creates one check-in from the request body, attached to the demo pilot and its demo drone.\n\n"
                    "The demo pilot, its drone (with a demo model) and the demo country (Poland) "
                    "are created on first use.\n\n"
                    "A pilot may have only one active/late check-in, so the demo pilot's open check-ins "
                    "are cancelled first - their count is returned in `cancelled`.\n\n"
                    "starts_at defaults to now and the window ends at starts_at + `time` seconds - "
                    "ends_at is not accepted. "
                    "h3_index is filled by a database trigger.",
    "response_description": "Created check-in id, its point and h3 index",
    "responses": {
        200: { "description": "Check-in created" }
    }
}

CREATE_RANDOM_CHECKINS = {
    "summary": "Create random check-ins",
    "description": "Creates `count` check-ins with random position, height, range and time "
                    "inside the Warsaw bounding box, attached to the demo pilot and its demo drone.\n\n"
                    "Each window ends at starts_at + the generated `time`.\n\n"
                    "The demo pilot's open check-ins are cancelled first. "
                    "Pass `?reset=true` to delete them instead "
                    "(the pilot row and its flight_time are kept).\n\n"
                    "Caveat: with `count` > 1 the new check-ins are all open on one pilot. "
                    "Once two of them expire, the overdue-check-in cron job hits the "
                    "one-active-per-pilot index and fails until they are ended or reset.",
    "response_description": "Created check-ins with their points and h3 indexes",
    "responses": {
        200: { "description": "Check-ins created" }
    }
}

END_CHECKIN = {
    "summary": "End a check-in",
    "description": "Ends a check-in by id.\n\n"
                    "The status becomes `ended_intime` if ended before ends_at, otherwise `late_end`.\n\n"
                    "A check-in left open past ends_at is marked `late` by a scheduled job and stays "
                    "`late` until it is ended; once it has been overdue for more than 3 hours "
                    "the job ends it as `late_end`.",
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
