__all__ = [ "MainAPIRouter", "DemoAPIRouter" ]


from .version_router import VersionRouter
from . import v1, demo

MainAPIRouter = VersionRouter(v1)
DemoAPIRouter = VersionRouter(demo)