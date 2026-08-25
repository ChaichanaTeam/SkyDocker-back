__all__ = [ "BaseRouter", "BusinessRouters" ]


from .base import BaseRouter
from .auth import AuthRouter
# from .pilot import PilotRouter
from .geozone import GeoZoneRouter
from .checkin import CheckinRouter


BusinessRouters = (AuthRouter, GeoZoneRouter, CheckinRouter)