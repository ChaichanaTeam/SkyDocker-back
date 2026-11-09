#!/bin/sh
set -e

: "${STORAGE_ADMIN_KEY:?STORAGE_ADMIN_KEY is not set, add it to .env}"
: "${STORAGE_ADMIN_SECRET:?STORAGE_ADMIN_SECRET is not set, add it to .env}"
: "${STORAGE_APP_KEY:?STORAGE_APP_KEY is not set, add it to .env}"
: "${STORAGE_APP_SECRET:?STORAGE_APP_SECRET is not set, add it to .env}"
: "${WEED_S3_SSE_KEY:?STORAGE_SSE_KEY is not set, add it to .env}"
: "${WEED_JWT_FILER_SIGNING_KEY:?STORAGE_FILER_JWT_KEY is not set, add it to .env}"

envsubst '${STORAGE_ADMIN_KEY} ${STORAGE_ADMIN_SECRET} ${STORAGE_APP_KEY} ${STORAGE_APP_SECRET}' \
    < /etc/seaweedfs/s3.json.template > /etc/seaweedfs/s3.json
chown seaweed:seaweed /etc/seaweedfs/s3.json
chmod 600 /etc/seaweedfs/s3.json

exec /entrypoint.sh "$@"
