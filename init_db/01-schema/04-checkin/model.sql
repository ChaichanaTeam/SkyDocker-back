CREATE TABLE checkin (
    id                      bigserial PRIMARY KEY,
    pilot_id                bigint NOT NULL,
    mission_id              bigint,
    
    flying_privilege        flying_privileges NOT NULL,
    flight_goal             mission_flight_goal,
    description             TEXT,
    
    home_point              GEOMETRY(Point, 4326) NOT NULL,
    h3_index                h3index NOT NULL,
    country_id              smallint NOT NULL,
    height                  integer NOT NULL,
    range                   integer NOT NULL,
    starts_at               timestamptz(0) NOT NULL,
    ends_at                 timestamptz(0) NOT NULL,
    time                    integer NOT NULL,

    status                  mission_status DEFAULT 'created' NOT NULL,

    created_at              timestamptz(0) DEFAULT now() NOT NULL,

    FOREIGN KEY (pilot_id) REFERENCES pilot(id),
    FOREIGN KEY (mission_id) REFERENCES mission(id),
    FOREIGN KEY (country_id) REFERENCES country(id)
);

COMMENT ON TABLE  public.checkin IS 'The pilot must notify if he wants to take off. Check-in is the method of notification on-time, especially if zone is open';
COMMENT ON COLUMN public.checkin.flying_privilege IS 'Privileges which pilots uses for flight';
COMMENT ON COLUMN public.checkin.h3_index IS 'Uber H3 index used for efficiency';
COMMENT ON COLUMN public.checkin.country_id IS 'Filter column. Used for efficiency';
COMMENT ON COLUMN public.checkin.home_point IS 'Center of check-in position circle. Only position of drones take off and land';
COMMENT ON COLUMN public.checkin.height IS 'Maximum documented height in check-in in meters';
COMMENT ON COLUMN public.checkin.range IS 'Maximum documented range in check-in in meters';
COMMENT ON COLUMN public.checkin.time IS 'Telemetry. Could have feature';
COMMENT ON COLUMN public.checkin.status IS 'If check-in is in controversial zone it needs to be verified by authorities';
