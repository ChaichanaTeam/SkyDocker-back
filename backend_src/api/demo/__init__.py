__all__ = [ "BaseRouter", "BusinessRouters" ]


from .base import BaseRouter
from .country import CountryRouter
from .redis import RedisRouter
from .geozone import GeoZoneRouter
from .checkin import CheckinRouter
from .mission import MissionRouter
from .privilege import PrivilegeRouter


BusinessRouters = (CountryRouter, RedisRouter, GeoZoneRouter, CheckinRouter, MissionRouter, PrivilegeRouter)