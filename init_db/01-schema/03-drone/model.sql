CREATE TABLE model (
    id                      serial PRIMARY KEY,
    
    manufacturer            character varying(255) NOT NULL,
    model_name              character varying(255) NOT NULL,

    is_model_verified       boolean DEFAULT false NOT NULL,
    created_at              timestamptz(0) DEFAULT now() NOT NULL,
    
    speed                   integer NOT NULL,
    weight                  integer NOT NULL,
    max_height              integer NOT NULL,
    max_range               integer NOT NULL
);

COMMENT ON TABLE  public.model              IS 'Table discrabing models which pilots can use to describe their drone';
COMMENT ON COLUMN public.model.model_name   IS 'Normalized model full name';
COMMENT ON COLUMN public.model.speed        IS 'Speed of drone in m/s';
COMMENT ON COLUMN public.model.weight       IS 'Weight of drone in grams';
COMMENT ON COLUMN public.model.max_height   IS 'Maximum height of drone in meters';
COMMENT ON COLUMN public.model.max_range    IS 'Maximum range of drone in meters';


CREATE TABLE drone (
    id                  bigserial PRIMARY KEY,
    pilot_id            bigint NOT NULL,

    model_id            integer NOT NULL,
    serial_number       character varying(255) NOT NULL,

    FOREIGN KEY (model_id) REFERENCES model(id),
    FOREIGN KEY (pilot_id) REFERENCES pilot(id)
);

COMMENT ON TABLE public.drone IS 'Drones created by user for his dronepark';