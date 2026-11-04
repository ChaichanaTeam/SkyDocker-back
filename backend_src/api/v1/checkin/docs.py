# Additional instruments:
# https://geojson.io/
# https://clupasq.github.io/h3-viewer/

from backend_src.api.shared_schemas import GeoJson, GeoFeature
from .schema import CheckinTokenResponse


ROUTER = {
    "tags": ["check-in"],
    "responses": {
        401: { "description": "Invalid or expired access token | Dev: forgot Authorization header or invalid" }
    }
}


CHECKIN_BBOX = {
    "name": "Get Check-in from Bounding Box",
    "summary": "Get Check-in from Bounding Box",
    "description": "Fetches all check-ins that are within the bounding box provided by the user.\n\n"
                    "The bounding box is defined by two coordinates: the southwest corner and the northeast corner.\n\n"
                    "The response is a GeoJSON collection of check-ins.\n\n"
                    "Authorization header REQUIRED!",
    "response_model": GeoJson,
    "responses": {
        200: { "description": "GeoJSON collection of check-ins in the bounding box" },
        404: { "description": "No check-in found in the bounding box" }
    }
}


CHECKIN_PREVIEW = {
    "summary": "Verify a planned flight",
    "description": "Checks the planned flight against the pilot privileges, drone and the geo-zones "
                    "it reaches while it lasts, and issues a short-lived check-in token for POST /check-in.\n\n"
                    "Pass either `mission_id` (the flight properties are taken from the mission) "
                    "or all of `category`, `height`, `range` and `duration`.\n\n"
                    "`country_tag` must be one of GET /geo-zone/country/supported, and the home point must lie "
                    "inside its border synced from GADM. GET /geo-zone/country tells the country at the home point.\n\n"
                    "Business-rule errors come in the same shape as validation errors: "
                    "`detail[].loc`, `detail[].msg`, `detail[].type` (`checkin.*`), `detail[].input`.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "Check-in token",
    "response_model": CheckinTokenResponse,
    "responses": {
        200: { "description": "Flight verified, check-in token returned" },
        404: { "description": "Cannot verify fly zone: unsupported country, home point outside its border "
                              "or no ground elevation data" },
        409: { "description": "Check-in already started. End it to start a new one" },
        422: { "description": "Invalid request or the flight breaks a rule, see detail" },
        502: { "description": "Ground elevation is unavailable" }
    }
}


CHECKIN_CREATE = {
    "summary": "Start a check-in",
    "description": "Starts the check-in verified by POST /check-in/preview.\n\n"
                    "The check-in token is valid for a minute, after it expires run the preview again.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "GeoJSON feature of the started check-in",
    "response_model": GeoFeature,
    "responses": {
        201: { "description": "Check-in started" },
        404: { "description": "No verified check-in: the token is invalid, expired or issued to another pilot" },
        409: { "description": "Check-in already started. End it to start a new one" },
        422: { "description": "Invalid request body" }
    }
}


CHECKIN_END = {
    "summary": "End the check-in",
    "description": "Ends the check-in in progress, as ended in time or late.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "GeoJSON feature of the ended check-in",
    "response_model": GeoFeature,
    "responses": {
        200: { "description": "Check-in ended" },
        404: { "description": "No check-in in progress" }
    }
}
