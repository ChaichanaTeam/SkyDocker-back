-- Schema created by the scripts above matches Alembic revision 0001_baseline.
-- Later schema changes live in alembic/versions: run `alembic upgrade head`.
CREATE TABLE alembic_version (
    version_num                     character varying(32) NOT NULL PRIMARY KEY
);

INSERT INTO alembic_version (version_num) VALUES ('0001_baseline');
