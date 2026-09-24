CREATE TABLE model (
    id                      serial PRIMARY KEY,
    
    manufacturer            character varying(255) NOT NULL,
    model_name              character varying(255) NOT NULL,
    category                operational_category NOT NULL,

    is_model_verified       boolean DEFAULT false NOT NULL,
    created_at              timestamptz(0) DEFAULT now() NOT NULL,
    
    speed                   integer NOT NULL,
    mtom                    integer NOT NULL,
    max_height              integer NOT NULL,
    max_range               integer NOT NULL
);

COMMENT ON TABLE  public.model              IS 'Table discrabing models which pilots can use to describe their drone';
COMMENT ON COLUMN public.model.model_name   IS 'Normalized model full name';
COMMENT ON COLUMN public.model.speed        IS 'Speed of drone in m/s';
COMMENT ON COLUMN public.model.mtom         IS 'Maximum take off mass in grams. Can be varied because of modifications done';
COMMENT ON COLUMN public.model.max_height   IS 'Maximum height of drone in meters';
COMMENT ON COLUMN public.model.max_range    IS 'Maximum range of drone in meters';


CREATE TABLE drone (
    id                  bigserial PRIMARY KEY,
    pilot_id            bigint NOT NULL,

    is_drone_modified   boolean DEFAULT false NOT NULL,
    category            drone_category NOT NULL,
    model_id            integer NOT NULL,
    serial_number       character varying(255) NOT NULL,

    mtom_override       integer,

    flight_time         integer DEFAULT 0 NOT NULL,

    FOREIGN KEY (model_id) REFERENCES model(id),
    FOREIGN KEY (pilot_id) REFERENCES pilot(id)
);

COMMENT ON TABLE public.drone IS 'Drones created by user for his dronepark';
COMMENT ON COLUMN public.drone.is_drone_modified IS 'If true, will fetch the override parameters over factory';
