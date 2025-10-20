from slowapi import Limiter
from slowapi.util import get_remote_address


def get_limiter() -> Limiter:
    # Create and configure rate limiter
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100/minute"]
    )
    return limiter

