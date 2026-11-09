FROM chrislusf/seaweedfs:4.50

RUN apk add --no-cache \
    gettext

COPY ./s3.json.template /etc/seaweedfs/s3.json.template
COPY --chmod=755 ./entrypoint.sh /usr/local/bin/skydocker-entrypoint.sh
COPY --chmod=755 ./init.sh /usr/local/bin/skydocker-storage-init.sh

ENTRYPOINT ["skydocker-entrypoint.sh"]

CMD [\
    "server", "-s3", \
    "-ip=storage", "-ip.bind=0.0.0.0", \
    "-s3.config=/etc/seaweedfs/s3.json", \
    "-dir=/data" \
]
