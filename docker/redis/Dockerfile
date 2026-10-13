FROM redis:7.2-alpine

RUN apk add --no-cache \
    gettext

COPY ./init.acl.template /etc/redis/init.acl.template
COPY --chmod=755 ./entrypoint.sh /usr/local/bin/skydocker-entrypoint.sh

ENTRYPOINT ["skydocker-entrypoint.sh"]

CMD [\
    "redis-server", \
    "--maxmemory", "2gb", "--maxmemory-policy", "allkeys-lru", \
    "--aclfile", "/etc/redis/users.acl", \
    "--save", "60", "1", "--loglevel", "notice" \
]
