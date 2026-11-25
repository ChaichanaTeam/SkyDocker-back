from backend_src.api.v1.moderator.docs import MODERATOR_AUTH, MODERATOR_401
from backend_src.api.v1.pilot.schema import DroneModelRead
from .schema import ModelReview, UnverifiedModelRead


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

LIST_UNVERIFIED = {
    "summary": "List drone models pilots typed in",
    "description": "Models added with `custom_model` that are not in the catalog yet, the oldest first, "
                    "each with the drones that use it and their pilots. "
                    "A model is approved into the catalog or replaced with a catalog model.\n\n" + MODERATOR_AUTH,
    "response_model": list[UnverifiedModelRead],
    "responses": {
        200: { "description": "Models waiting for review" },
        401: MODERATOR_401
    }
}

APPROVE = {
    "summary": "Approve a typed-in drone model into the catalog",
    "description": "Fixes the passed values, e.g. the model name to the catalog spelling, "
                    "and adds the model to the catalog. The drones that use it get the fixed values.\n\n"
                    "A new mass can make the class mark of a drone wrong, such drones are listed in `class_conflicts` "
                    "and stay as they are.\n\n" + MODERATOR_AUTH,
    "response_model": ModelReview,
    "responses": {
        200: { "description": "Model added to the catalog" },
        401: MODERATOR_401,
        404: { "description": "Drone model not found" },
        409: { "description": "The model is in the catalog already, or after the fix it matches a catalog model: "
                              "`detail.model_id` is the model to replace it with" },
        422: { "description": "Invalid values" }
    }
}

REPLACE = {
    "summary": "Replace a typed-in drone model with a catalog model",
    "description": "For a model that is in the catalog already under another spelling: "
                    "every drone that uses the typed-in model gets the catalog model, and the typed-in model is removed.\n\n"
                    "The catalog mass can make the class mark of a moved drone wrong, such drones are listed in "
                    "`class_conflicts` and stay as they are.\n\n" + MODERATOR_AUTH,
    "response_model": ModelReview,
    "responses": {
        200: { "description": "Drones moved to the catalog model" },
        401: MODERATOR_401,
        404: { "description": "Typed-in model or catalog model not found" },
        409: { "description": "The model to replace is in the catalog already" },
        422: { "description": "Invalid request" }
    }
}

DELETE = {
    "summary": "Delete a drone model",
    "description": "Removes the model, verified or not, together with its drones that pilots already deleted, "
                    "when no drone in a drone park and no check-in or mission uses it.\n\n" + MODERATOR_AUTH,
    "responses": {
        200: { "description": "Drone model deleted" },
        401: MODERATOR_401,
        404: { "description": "Drone model not found" },
        409: { "description": "The drone model is still in use" }
    }
}
