__all__ = [ "BaseRouter", "BusinessRouters" ]


from .base import BaseRouter
from .auth import AuthRouter
# from .pilot import PilotRouter
from .geozone import GeoZoneRouter
from .checkin import CheckinRouter
from .verification import VerificationRouter


BusinessRouters = (AuthRouter, CheckinRouter, GeoZoneRouter, VerificationRouter)
