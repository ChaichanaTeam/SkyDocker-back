HEALTH = {
    "summary": "Healthcheck",
    "description": "Used for Docker to verify readiness of containter or aknowledge developer of server status",
    "response_description": "Status string and response code",
    "responses": {
        200: { "description": "No errors on startup" },
        501: { "description": "Server verified crucial settings and refused to start up" },
        503: { "description": "Server can\'t reach crucial services" },
    }
}