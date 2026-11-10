from backend_src.api.v1.pilot.schema import DroneModelRead


ROUTER = {
    "tags": ["drone-models"],
    "responses": {
        401: { "description": "Invalid or expired access token | Dev: forgot Authorization header or invalid" }
    }
}


GET_CATALOG = {
    "summary": "List the drone model catalog",
    "description": "Checked drone models, sorted by manufacturer and model name, so the app can offer "
                    "a manufacturer and then its model. A drone that is not listed is added with its own model.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "Drone models",
    "response_model": list[DroneModelRead],
}
