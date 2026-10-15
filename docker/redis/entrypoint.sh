#!/bin/sh
set -e

: "${REDIS_SUPASSWORD:?REDIS_SUPASSWORD is not set, add it to .env}"
: "${REDIS_USER:?REDIS_USER is not set, add it to .env}"
: "${REDIS_UPASSWORD:?REDIS_UPASSWORD is not set, add it to .env}"

envsubst '${REDIS_SUPASSWORD} ${REDIS_USER} ${REDIS_UPASSWORD}' \
    < /etc/redis/init.acl.template > /etc/redis/users.acl
chown redis:redis /etc/redis/users.acl
chmod 600 /etc/redis/users.acl

exec docker-entrypoint.sh "$@"
