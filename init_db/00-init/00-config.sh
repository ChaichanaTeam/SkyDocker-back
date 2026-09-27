#!/bin/bash
set -e

: "${H3_RESOLUTION:?H3_RESOLUTION is not set, add it to .env}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    ALTER DATABASE $POSTGRES_DB SET settings.h3_resolution = '$H3_RESOLUTION';
EOSQL