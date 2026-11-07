WORKER_LOG_FILE = "logs/worker.log"

# A scheduled run up to this late still happens, e.g. after the worker was restarted at 03:10
MISFIRE_GRACE_SECONDS = 60 * 60

# The worker refreshes its heartbeat key this often, /health and the container healthcheck read it
HEARTBEAT_INTERVAL_SECONDS = 60
# A worker that missed a few beats counts as down
HEARTBEAT_TTL_SECONDS = 180

# How long a stopping worker waits for cancelled syncs to release their locks, below the docker stop timeout
STOP_TIMEOUT_SECONDS = 5
