WORKER_LOG_FILE = "logs/worker.log"

# A scheduled run up to this late still happens, e.g. after the worker was restarted at 03:10
MISFIRE_GRACE_SECONDS = 60 * 60
