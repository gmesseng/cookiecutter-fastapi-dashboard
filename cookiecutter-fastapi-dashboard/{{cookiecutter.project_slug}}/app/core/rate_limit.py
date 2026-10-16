"""Rate limiting par IP via slowapi (60 req/min par défaut)."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
