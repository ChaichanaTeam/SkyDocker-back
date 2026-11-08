def refresh_key(pilot_id: str, jti: str) -> str:
    return f"refresh:{pilot_id}:{jti}"


def otp_key(purpose: str, subject: str) -> str:
    return f"otp:{purpose}:{subject}"


def session_gen_key(pilot_id: str) -> str:
    return f"session_gen:{pilot_id}"


def verification_token_key(jti: str) -> str:
    return f"verification_token_used:{jti}"
