CREATE TABLE geo_zone (
    id              bigserial PRIMARY KEY,
    country_id      smallint NOT NULL,
    
    type            geo_zone_type NOT NULL,
    tag             character varying(255) NOT NULL,
    strength        integer NOT NULL,
    zone_polygon    GEOMETRY(Polygon, 4326) NOT NULL,
    height_agl      integer,
    height_amsl     integer,
    
    FOREIGN KEY (country_id) REFERENCES country(id)
);

COMMENT ON TABLE  public.geo_zone IS 'Table describing geo zones with information crutial for drone operators';
COMMENT ON COLUMN public.geo_zone.type IS 'Geo zone type specified in 2019/947/UE';
COMMENT ON COLUMN public.geo_zone.tag IS 'Geo zone short unique identifier';
COMMENT ON COLUMN public.geo_zone.strength IS 'Describing the priority of zone, which needed if they are nested and one of them is excluded from nesting';
COMMENT ON COLUMN public.geo_zone.zone_polygon IS 'PostGIS data type describing zone polygon';
COMMENT ON COLUMN public.geo_zone.height_agl IS 'Height Above Ground Level in meters';
COMMENT ON COLUMN public.geo_zone.height_amsl IS 'Height Above Mean Sea Level in meters';


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

    start_at        timestamptz(0) NOT NULL,
    ends_at         timestamptz(0) NOT NULL,

    FOREIGN KEY (geo_zone_id) REFERENCES geo_zone(id)
);

COMMENT ON TABLE public.activity_time IS 'Some of geo zones can have limited time and not consistent in period.';
