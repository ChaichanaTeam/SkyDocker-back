FROM postgis/postgis:17-3.5

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-17-cron \
        postgresql-17-h3 && \
        apt-get clean && \
    rm -rf /var/lib/apt/lists/*