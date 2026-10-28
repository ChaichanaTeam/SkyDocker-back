CREATE TABLE geo_zone (
    id                  bigserial PRIMARY KEY,
    country_id          smallint NOT NULL,
    parent_id           bigint,

    external_id         uuid NOT NULL,
    type                geo_zone_type NOT NULL,
    source_type         character varying(16) NOT NULL,
    activity_mode       geo_zone_activity_mode NOT NULL,
    tag                 character varying(255) NOT NULL,
    zone_polygon        GEOMETRY(Polygon, 4326) NOT NULL,

    lower_limit_ft      integer NOT NULL,
    upper_limit_ft      integer NOT NULL,
    terrain_max_m       real,

    valid_from          timestamptz,
    valid_to            timestamptz,

    description_pl      text,
    description_en      text,
    contact             character varying(255),

    source_modified_at  timestamptz NOT NULL,
    updated_at          timestamptz NOT NULL DEFAULT now(),

    FOREIGN KEY (country_id) REFERENCES country(id),
    FOREIGN KEY (parent_id) REFERENCES geo_zone(id) ON DELETE SET NULL,

    CONSTRAINT geo_zone_external_id_unique UNIQUE (country_id, external_id),
    CONSTRAINT geo_zone_limits_order CHECK (lower_limit_ft <= upper_limit_ft)
);

COMMENT ON TABLE  public.geo_zone IS 'Table describing geo zones with information crutial for drone operators';
COMMENT ON COLUMN public.geo_zone.parent_id IS 'Enclosing zone, e.g. ATZ for its 1 km and 6 km rings. Inherited zones take activity from it';
COMMENT ON COLUMN public.geo_zone.external_id IS 'Zone id in the source system (PANSA DroneMap uid)';
COMMENT ON COLUMN public.geo_zone.type IS 'Geo zone type specified in 2019/947/UE';
COMMENT ON COLUMN public.geo_zone.source_type IS 'Zone type in the source system, e.g. TRA, CTR6KM, DRAR';
COMMENT ON COLUMN public.geo_zone.activity_mode IS 'How to decide whether the zone is active, see geo_zone_activity_mode';
COMMENT ON COLUMN public.geo_zone.tag IS 'Geo zone name, e.g. EPTR4H or DRA-RL 1840';
COMMENT ON COLUMN public.geo_zone.zone_polygon IS 'PostGIS data type describing zone polygon';
COMMENT ON COLUMN public.geo_zone.lower_limit_ft IS 'Lower limit in feet AMSL, 0 means ground';
COMMENT ON COLUMN public.geo_zone.upper_limit_ft IS 'Upper limit in feet AMSL';
COMMENT ON COLUMN public.geo_zone.terrain_max_m IS 'Highest ground inside the zone, metres AMSL from the DEM. Measured only for zones starting above ground or with activity windows, NULL means not measured';
COMMENT ON COLUMN public.geo_zone.valid_from IS 'Start of the zone validity, NULL means already valid';
COMMENT ON COLUMN public.geo_zone.valid_to IS 'End of the zone validity, NULL means valid until further notice';
COMMENT ON COLUMN public.geo_zone.description_pl IS 'Flight conditions published by the source, in Polish';
COMMENT ON COLUMN public.geo_zone.description_en IS 'Flight conditions published by the source, in English';
COMMENT ON COLUMN public.geo_zone.contact IS 'Zone manager contact';
COMMENT ON COLUMN public.geo_zone.source_modified_at IS 'Last modification time in the source system, used to skip unchanged zones on sync';
COMMENT ON COLUMN public.geo_zone.updated_at IS 'Last time the row was inserted or changed by sync';


create table geo_zone_h3 (
	id                  bigserial PRIMARY KEY,

	geo_zone_id         bigint NOT NULL,
    h3_index h3index    NOT NULL,

	FOREIGN KEY (geo_zone_id) REFERENCES geo_zone(id) ON DELETE CASCADE
);

COMMENT ON TABLE public.geo_zone_h3 IS 'Many-to-Many relation. Used for selection only needed zones calculated with Uber H3 index';


CREATE TABLE activity_time (
    id              bigserial PRIMARY KEY,
    geo_zone_id     bigint NOT NULL,

    source          geo_zone_activity_source NOT NULL,
    source_ref      character varying(64),

    start_at        timestamptz(0) NOT NULL,
    ends_at         timestamptz(0) NOT NULL,

    lower_limit_ft  integer,
    upper_limit_ft  integer,

    FOREIGN KEY (geo_zone_id) REFERENCES geo_zone(id) ON DELETE CASCADE,

    CONSTRAINT activity_time_order CHECK (start_at < ends_at)
);

COMMENT ON TABLE  public.activity_time IS 'Activity windows of scheduled geo zones. A scheduled zone with no current window is inactive.
                                           Repeating schedules (e.g. NOTAM weekdays) are stored expanded into separate windows';
COMMENT ON COLUMN public.activity_time.source_ref IS 'Id of the window in its source: NOTAM series (e.g. D7750/26) or AUP/UUP reservation id';
COMMENT ON COLUMN public.activity_time.lower_limit_ft IS 'Reserved lower limit in feet AMSL when it differs from the zone, NULL means the zone limit';
COMMENT ON COLUMN public.activity_time.upper_limit_ft IS 'Reserved upper limit in feet AMSL when it differs from the zone, NULL means the zone limit';
