class SyncError(Exception):
    """A sync that stopped without storing its result, the message says why."""

    # Whether running the same sync again later can succeed
    retryable = False


class UpstreamUnavailable(SyncError):
    """The data source did not answer or answered with an HTTP error."""

    retryable = True


class SyncAborted(SyncError):
    """The data source answered with data that cannot be stored, e.g. a much shorter zone list."""


class NothingToSync(SyncError):
    """What the sync builds on is missing, e.g. terrain without stored geo-zones."""


class NotPublished(SyncError):
    """The data source has nothing for the request, e.g. GADM has no border for the country."""
