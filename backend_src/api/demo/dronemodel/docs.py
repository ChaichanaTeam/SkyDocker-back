from .schema import ModelReview, UnverifiedModelRead


LIST_UNVERIFIED = {
    "summary": "List drone models pilots typed in",
    "description": "Moderator simulation. Models added with `custom_model` that are not in the catalog yet, the oldest first, "
                    "each with the drones that use it and their pilots. "
                    "A model is approved into the catalog or replaced with a catalog model",
    "response_model": list[UnverifiedModelRead],
}

APPROVE = {
    "summary": "Approve a typed-in drone model into the catalog",
    "description": "Moderator simulation. Fixes the passed values, e.g. the model name to the catalog spelling, "
                    "and adds the model to the catalog. The drones that use it get the fixed values.\n\n"
                    "A new mass can make the class mark of a drone wrong, such drones are listed in `class_conflicts` "
                    "and stay as they are",
    "response_model": ModelReview,
    "responses": {
        200: { "description": "Model added to the catalog" },
        404: { "description": "Drone model not found" },
        409: { "description": "The model is in the catalog already, or after the fix it matches a catalog model: "
                              "`detail.model_id` is the model to replace it with" },
        422: { "description": "Invalid values" }
    }
}

DELETE = {
    "summary": "Delete a drone model",
    "description": "Cleanup for tests and demos. Removes the model, verified or not, together with its drones "
                    "that pilots already deleted, when no drone in a drone park and no check-in or mission uses it",
    "responses": {
        200: { "description": "Drone model deleted" },
        404: { "description": "Drone model not found" },
        409: { "description": "The drone model is still in use" }
    }
}

REPLACE = {
    "summary": "Replace a typed-in drone model with a catalog model",
    "description": "Moderator simulation. For a model that is in the catalog already under another spelling: "
                    "every drone that uses the typed-in model gets the catalog model, and the typed-in model is removed.\n\n"
                    "The catalog mass can make the class mark of a moved drone wrong, such drones are listed in "
                    "`class_conflicts` and stay as they are",
    "response_model": ModelReview,
    "responses": {
        200: { "description": "Drones moved to the catalog model" },
        404: { "description": "Typed-in model or catalog model not found" },
        409: { "description": "The model to replace is in the catalog already" },
        422: { "description": "Invalid request" }
    }
}
