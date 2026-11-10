def refresh_key(subject: str, jti: str, prefix: str = "") -> str:
    return f"{prefix}refresh:{subject}:{jti}"


def otp_key(purpose: str, subject: str) -> str:
    return f"otp:{purpose}:{subject}"


def session_gen_key(subject: str, prefix: str = "") -> str:
    return f"{prefix}session_gen:{subject}"


def verification_token_key(jti: str) -> str:
    return f"verification_token_used:{jti}"
  
 
def sync_lock_key(name: str) -> str:
    return f"sync:lock:{name}"


def sync_status_key() -> str:
    return "sync:status"


def worker_heartbeat_key() -> str:
    return "sync:worker:heartbeat"
