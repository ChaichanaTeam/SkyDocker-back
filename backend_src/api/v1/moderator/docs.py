from .schema import ModeratorAccessToken, ModeratorProfile


ROUTER = {
    "tags": ["moderator"],
    "responses": {
        429: { "description": "Rate limit exceeded" }
    }
}


LOGIN = {
    "summary": "Moderator login",
    "description":
        "Authenticates a moderator using email and password.\n\n"
        "On success, returns a short-lived access token in the body and sets "
        "the refresh token as an HttpOnly cookie, scoped to /api/v1/moderator/auth.\n\n"
        "Pilot tokens are not accepted by moderator endpoints and vice versa.",
    "response_description": "Access token and its lifetime in seconds",
    "response_model": ModeratorAccessToken,
    "responses": {
        200: { "description": "Login successful, access token returned, refresh cookie set" },
        401: { "description": "Invalid email or password" }
    }
}

REFRESH = {
    "summary": "Refresh the moderator session",
    "description":
        "Exchanges the refresh cookie for a new access token and rotates the cookie.\n\n"
        "Each refresh token is single-use. The dashboard calls this while the moderator is active, "
        "so the cookie lifetime works as the idle timeout. On failure the cookie is cleared.",
    "response_description": "New access token",
    "response_model": ModeratorAccessToken,
    "responses": {
        200: { "description": "Session refreshed, refresh cookie rotated" },
        401: { "description": "Cookie missing, invalid, expired, already used or moderator not found" }
    }
}

LOGOUT = {
    "summary": "Moderator logout",
    "description": "Revokes the refresh session from the cookie and clears the cookie.",
    "response_description": "Logout confirmation message",
    "responses": {
        200: { "description": "Logout successful" }
    }
}

GET_ME = {
    "summary": "Current moderator",
    "description": "Returns the profile of the moderator the access token belongs to.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "Moderator profile",
    "response_model": ModeratorProfile,
    "responses": {
        200: { "description": "Moderator profile returned" },
        401: { "description": "Invalid, expired or non-moderator access token" }
    }
}
