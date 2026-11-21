__all__ = [ "BaseRouter", "BusinessRouters" ]


from .base import BaseRouter
from .country import CountryRouter
from .redis import RedisRouter
from .checkin import CheckinRouter
from .mission import MissionRouter
from .privilege import PrivilegeRouter
from .dronepark import DroneparkRouter
from .dronemodel import DroneModelRouter
from .verification import VerificationRouter

BusinessRouters = (CountryRouter, RedisRouter, VerificationRouter, CheckinRouter, MissionRouter, PrivilegeRouter, DroneparkRouter, DroneModelRouter)
