#!/bin/bash
set -e

INIT_DIR="/docker-entrypoint-initdb.d"

echo "==> Starting database initialization..."

for sh_file in $(find "$INIT_DIR/00-init" -type f -name "*.sh" | sort); do
    echo "==> Executing Shell Script: $sh_file"
    bash "$sh_file"
done

find "$INIT_DIR" -mindepth 2 -type f -name "*.sql" | sort | while read -r sql_file; do
    echo "==> Executing SQL: $sql_file"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f "$sql_file"
done

echo "==> Database initialization complete!"