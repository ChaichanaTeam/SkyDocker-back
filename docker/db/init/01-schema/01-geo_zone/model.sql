CREATE TABLE geo_zone (
    id              bigserial PRIMARY KEY,
    country_id      smallint NOT NULL,
    
    type            geo_zone_type NOT NULL,
    tag             character varying(255) NOT NULL,
    strength        integer NOT NULL,
    zone_polygon    GEOMETRY(Polygon, 4326) NOT NULL,
    height_agl      integer,
    
    FOREIGN KEY (country_id) REFERENCES country(id)
);

COMMENT ON TABLE  public.geo_zone IS 'Table describing geo zones with information crutial for drone operators';
COMMENT ON COLUMN public.geo_zone.type IS 'Geo zone type specified in 2019/947/UE';
COMMENT ON COLUMN public.geo_zone.tag IS 'Geo zone short unique identifier';
COMMENT ON COLUMN public.geo_zone.strength IS 'Describing the priority of zone, which needed if they are nested and one of them is excluded from nesting';
COMMENT ON COLUMN public.geo_zone.zone_polygon IS 'PostGIS data type describing zone polygon';
COMMENT ON COLUMN public.geo_zone.height_agl IS 'Height Above Ground Level in meters';


create table geo_zone_h3 (
	id                  bigserial PRIMARY KEY,
	
	geo_zone_id         bigint NOT NULL,
    h3_index h3index    NOT NULL,

	FOREIGN KEY (geo_zone_id) REFERENCES geo_zone(id)
);

COMMENT ON TABLE public.geo_zone_h3 IS 'Many-to-Many relation. Used for selection only needed zones calculated with Uber H3 index';


CREATE TABLE activity_time (
    id              bigserial PRIMARY KEY,
    geo_zone_id     bigint NOT NULL,

    start_at        timestamptz(0),
    ends_at         timestamptz(0),

    daily_start     time,
    daily_end       time,

    FOREIGN KEY (geo_zone_id) REFERENCES geo_zone(id),

    CONSTRAINT activity_time_one_mode CHECK (
        (start_at IS NOT NULL AND ends_at IS NOT NULL AND daily_start IS NULL AND daily_end IS NULL)
        OR
        (daily_start IS NOT NULL AND daily_end IS NOT NULL AND start_at IS NULL AND ends_at IS NULL)
    )
);

COMMENT ON TABLE  public.activity_time IS 'Activity windows of a geo zone. A zone with no rows here is permanently active.
                                           A row is either an absolute window (start_at/ends_at) or a daily one (daily_start/daily_end), never both';
COMMENT ON COLUMN public.activity_time.daily_start IS 'UTC time of day. daily_start > daily_end means the window crosses midnight';
COMMENT ON COLUMN public.activity_time.daily_end   IS 'UTC time of day. Clients convert to their own timezone';
