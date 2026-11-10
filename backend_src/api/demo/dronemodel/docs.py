from .schema import UnverifiedModelRead


LIST_UNVERIFIED = {
    "summary": "List drone models pilots typed in",
    "description": "Moderator simulation. Models added with `custom_model` that are not in the catalog yet, the oldest first, "
                    "each with the drones that use it and their pilots. "
                    "A model is approved into the catalog or replaced with a catalog model",
    "response_model": list[UnverifiedModelRead],
}
