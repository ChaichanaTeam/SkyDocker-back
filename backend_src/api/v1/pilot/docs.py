from backend_src.api.shared_schemas import GeoFeature, GeoJson
from .schema import DroneRead, OrganizerDocumentRead, PilotPublicRead, PilotRead, PrivilegeRead


ROUTER = {
    "tags": ["pilots"],
    "responses": {
        401: { "description": "Invalid or expired access token | Dev: forgot Authorization header or invalid" }
    }
}


GET_ME = {
    "summary": "Get own profile",
    "description": "Name, phone and pilot number stay null until the pilot passes the verification.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "Profile of the pilot",
    "response_model": PilotRead,
}


UPDATE_ME = {
    "summary": "Update own profile",
    "description": "Changes only the fields that are passed, a field cannot be set to null.\n\n"
                    "Name and pilot number come from the approved verification request and cannot be changed here.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "Updated profile of the pilot",
    "response_model": PilotRead,
    "responses": {
        200: { "description": "Profile updated" },
        422: { "description": "Invalid phone number or a field set to null" }
    }
}


GET_PUBLIC = {
    "summary": "Get public profile of a pilot",
    "description": "Shows a profile with `show_to_public` enabled. The pilot's own profile is always visible.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "Public part of the profile",
    "response_model": PilotPublicRead,
    "responses": {
        200: { "description": "Public profile" },
        404: { "description": "Pilot does not exist or the profile is hidden" }
    }
}


GET_PRIVILEGES = {
    "summary": "List own flying privileges",
    "description": "Only privileges that have not expired. `expires_at` is the last valid day, null means no expiry.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "Privileges of the pilot",
    "response_model": list[PrivilegeRead],
}


GET_DOCUMENTS = {
    "summary": "List own documents from the organizer",
    "description": "Documents kept after an approved verification request with `keep_documents`, the newest first.\n\n"
                    "Every `url` is a download link valid for 5 minutes, request the list again for fresh links.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "Documents of the pilot with download links",
    "response_model": list[OrganizerDocumentRead],
}


GET_DRONES = {
    "summary": "List own drones",
    "description": "Drones of the pilot with their model. `id` is the `drone_id` of POST /check-in/preview.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "Drones of the pilot",
    "response_model": list[DroneRead],
}


GET_DRONE = {
    "summary": "Get own drone",
    "description": "Authorization header REQUIRED!",
    "response_description": "Drone with its model",
    "response_model": DroneRead,
    "responses": {
        200: { "description": "Drone of the pilot" },
        404: { "description": "Drone does not exist or belongs to another pilot" }
    }
}


GET_MISSIONS = {
    "summary": "List own missions",
    "description": "GeoJSON collection of the pilot's missions, the latest start first. "
                    "`properties.id` is the `mission_id` of POST /check-in/preview.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "GeoJSON collection of missions",
    "response_model": GeoJson,
}


GET_MISSION = {
    "summary": "Get own mission",
    "description": "Authorization header REQUIRED!",
    "response_description": "GeoJSON feature of the mission",
    "response_model": GeoFeature,
    "responses": {
        200: { "description": "Mission of the pilot" },
        404: { "description": "Mission does not exist or belongs to another pilot" }
    }
}


GET_CHECKINS = {
    "summary": "List own check-ins",
    "description": "GeoJSON collection of all the pilot's check-ins, ended ones included, the latest start first.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "GeoJSON collection of check-ins",
    "response_model": GeoJson,
}


GET_ACTIVE_CHECKIN = {
    "summary": "Get own check-in in progress",
    "description": "Authorization header REQUIRED!",
    "response_description": "GeoJSON feature of the check-in",
    "response_model": GeoFeature,
    "responses": {
        200: { "description": "Check-in in progress" },
        404: { "description": "No check-in in progress" }
    }
}
