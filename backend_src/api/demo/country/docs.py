CREATE_COUNTRIES = {
    "summary": "Seed countries",
    "description": "Creates every country from the built-in list (name + ISO tag).\n\n"
                    "Idempotent - countries whose tag already exists are skipped, "
                    "so it is safe to call repeatedly.",
    "response_description": "Added and skipped country tags",
    "responses": {
        200: { "description": "Countries seeded" }
    }
}
