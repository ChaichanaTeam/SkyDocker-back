__all__ = [ "BaseRouter", "AuthRouter", "PilotRouter" ]

from .routes.auth import router as AuthRouter
from .routes.pilot import router as PilotRouter
from .routes.base import router as BaseRouter