HEALTH = {
    "summary": "Healthcheck",
    "description": "Used for Docker to verify readiness of containter or aknowledge developer of server status.\n\n"
                   "Also shows whether the sync worker is `up` and the last run of every sync in `syncs`: "
                   "`status` (running, ok, skipped, retrying, failed), `trigger` (schedule, retry, startup, admin, cli) "
                   "and its times. The worker never changes the status or the code of the response.",
    "response_description": "Status string and response code",
    "responses": {
        200: { "description": "No errors on startup" },
        501: { "description": "Server verified crucial settings and refused to start up" },
        503: { "description": "Server can\'t reach crucial services" },
    }
}