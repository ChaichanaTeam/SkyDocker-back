CREATE TABLE mission (
    id                      bigserial PRIMARY KEY,
    pilot_id                bigint NOT NULL,
    drone_id                bigint NOT NULL,
    
    category                operational_category NOT NULL,
    flight_goal             mission_flight_goal,
    description             TEXT,
    flying_privilege        flying_privileges NOT NULL,
    
    country_id              smallint NOT NULL,
    h3_index                h3index NOT NULL,
    home_point              GEOMETRY(Point, 4326) NOT NULL,
    height                  integer NOT NULL,
    range                   integer NOT NULL,
    starts_at               timestamptz(0) NOT NULL,
    ends_at                 timestamptz(0) NOT NULL,
    time                    integer NOT NULL,
    
    status                  mission_status DEFAULT 'created' NOT NULL,

    spotter_first_name      character varying(255),
    spotter_last_name       character varying(255),
    spotter_phone           character varying(15),

    created_at              timestamptz(0) DEFAULT now() NOT NULL,

    FOREIGN KEY (pilot_id) REFERENCES pilot(id),
    FOREIGN KEY (drone_id) REFERENCES drone(id),
    FOREIGN KEY (country_id) REFERENCES country(id)
);

COMMENT ON TABLE  public.mission IS 'Table for creation and pre-verification flying mission which summbitted to ATC';
COMMENT ON COLUMN public.mission.category IS 'Category of flight (open/special)';
COMMENT ON COLUMN public.mission.description IS 'Descrition of mission, will be sended to ATC';
COMMENT ON COLUMN public.mission.drone_id IS 'Identification of which drone pilot used for flight';
COMMENT ON COLUMN public.mission.flying_privilege IS 'Privileges which pilots uses for flight';
COMMENT ON COLUMN public.mission.h3_index IS 'Uber H3 index used for efficiency';
COMMENT ON COLUMN public.mission.country_id IS 'Filter column. Used for efficiency';
COMMENT ON COLUMN public.mission.home_point IS 'Center of mission position circle. Only position of drones take off and land';
COMMENT ON COLUMN public.mission.height IS 'Maximum documented height in mission in meters';
COMMENT ON COLUMN public.mission.range IS 'Maximum documented range in mission in meters';
COMMENT ON COLUMN public.mission.time IS 'Telemetry. Could have feature';
COMMENT ON COLUMN public.mission.spotter_first_name IS 'The person who is obligated to have drone in their field of view during mission';
COMMENT ON COLUMN public.mission.spotter_last_name IS 'The person who is obligated to have drone in their field of view during mission';
COMMENT ON COLUMN public.mission.spotter_phone IS 'Contact of the person who is obligated to have drone in their field of view during mission';
COMMENT ON COLUMN public.mission.status IS 'If mission is in controversial zone it needs to be verified by authorities';
