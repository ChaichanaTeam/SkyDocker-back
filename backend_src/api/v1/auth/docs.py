from .schema import TokenPair, BearerToken


ROUTER = {
    "tags": ["auth"],
    "responses": {
        429: { "description": "Rate limit exceeded" }
    }
}


LOGIN = {
    "summary": "Pilot login",
    "description":
        "Authenticates a pilot using email and password.\n\n"
        "On success, returns a pair of tokens (access | refresh).\n\n"
        "The refresh token is stored in Redis as a hash for later validation.",
    "response_description": "Token pair (access_token, refresh_token) "
                            "and the access token's expirition time",
    "response_model": TokenPair,
    "responses": {
        200: { "description": "Login successful, token pair returned" },
        401: { "description": "Invalid email or password | Dev: forgot Authorization header or invalid" }
    }
}

REFRESH = {
    "summary": "Refresh the token pair",
    "description": "Exchanges a valid, unused refresh token for a new access/refresh token pair",
    "response_description": "New access and refresh tokens",
    "response_model": TokenPair,
    "responses": {
        200: { "description": "Token pair refresh successfully" },
        401: { "description": "Token invalid, expired, already used or pilot not found" }
    }
}

LOGOUT = {
    "summary": "Pilot logout",
    "description": "Rervokes the given refresh session.",
    "response_description": "Logout confirmation message",
    "responses": {
        200: { "description": "Logout successful" }
    }
}

REGISTER_REQUEST_OTP = {
    "summary": "Request an OTP for registration",
    "description": "Checks the email is free and sends an OTP code to start pilot registration",
    "response_description": "Temporary verify token for OTP confirmation",
    "response_model": BearerToken,
    "responses": {
        200: { "description": "OTP sent, verify token returned" },
        409: { "description": "Email is already registered" }
    }
}

VERIFY_OTP = {
    "summary": "Confirm registration email with OTP code",
    "description": "Verifies the registration OTP code and on success "
                    "issues a registration token for the final /auth/register step.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "Temporary registration token",
    "response_model": BearerToken,
    "responses": {
        200: { "description": "OTP confirmed, registration token returned" },
        400: { "description": "Invalid or expired confrimation code" },
        401: { "description": "Invalid or expired verify token | Dev: forgot Authorization header or invalid"}
    }
}

REGISTER = {
    "summary": "Complete pilot registration",
    "description": "Creates the pilot account using a validated registration token "
                    "and immediately logs the pilot in. "
                    "Authorization header REQUIRED!",
    "response_description": "Access and refresh tokens",
    "response_model": TokenPair,
    "responses": {
        200: { "description": "Account created, token pair returned" },
        401: { "description": "Invalid or expired registration token | Dev: forgot Authorization header or invalid" },
        409: { "description": "Email is already registered" }
    }
}

FORGOT_PASSWORD = {
    "summary": "Request a password reset",
    "description": "Sends an OTP code to a pilot's email "
                    "to start the password recovery flow",
    "response_description": "Temporary verify token for OTP confirmation",
    "response_model": BearerToken,
    "responses": {
        200: { "description": "OTP sent to the pilot's email" },
        404: { "description": "Pilot with the given email was not found" }
    }
}

VERIFY_RESET_TOKEN = {
    "summary": "Confirm the OTP code for a password reset",
    "description": "Verifies the password-reset OTP code "
                    "and issues a reset token for setting a new password.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "Temporary reset token",
    "response_model": BearerToken,
    "responses": {
        200: { "description": "OTP confirmed, reset token returned" },
        400: { "description": "Invalid or expired confirmation code" },
        401: { "description": "Invalid or expired verify token | Dev: forgot Authorization header or invalid" }
    }
}

RESET_PASSWORD = {
    "summary": "Set a new password",
    "description": "Sets a new passwrod using a valid reset token and "
                    "immediately logs the pilot in.\n\n"
                    "Authorization header REQUIRED!",
    "response_description": "Access and refresh tokens",
    "response_model": TokenPair,
    "responses": {
        200: { "description": "password updated, token pair returned" },
        401: { "description": "Invalid or expired reset token | Dev: forgot Authorization header or invalid" }
    }
}