import secrets
import time

def make_token() -> str:
    # короткий, но криптостойкий токен
    return secrets.token_urlsafe(16).replace("-", "").replace("_", "")

def expires_in_hours(hours: int) -> int:
    return int(time.time()) + hours * 3600