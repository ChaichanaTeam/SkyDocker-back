CREATE TABLE pilot (
    id                              bigserial PRIMARY KEY,
    
    first_name                      character varying(255) NOT NULL,
    last_name                       character varying(255) NOT NULL,
    
    email                           character varying(255) NOT NULL,
    phone_number                    character varying(15) NOT NULL,
    pilot_number                    character varying(255) NULL,
    
    password_hash                   character varying(255) NOT NULL,
    
    country_id                      smallint,
    show_to_public                  boolean DEFAULT false NOT NULL,
    activity                        user_activity,
    flight_time                     integer DEFAULT 0 NOT NULL,
    dronepark_hash                  character varying(255),
    
    verified                        boolean DEFAULT false NOT NULL,
    
    created_at                      timestamptz(0) DEFAULT now() NOT NULL,

    FOREIGN KEY (country_id) REFERENCES country(id)
);

COMMENT ON TABLE  public.pilot IS 'Pilots are the main users of application';
COMMENT ON COLUMN public.pilot.pilot_number IS 'Unique personal indentification number, given by National Aviation Authority of users country. Described by EASA';
COMMENT ON COLUMN public.pilot.show_to_public IS 'Could have feature';
COMMENT ON COLUMN public.pilot.activity IS 'Could have feature';
COMMENT ON COLUMN public.pilot.flight_time IS 'Telemetry. Could have feature';
COMMENT ON COLUMN public.pilot.dronepark_hash IS 'Used to synchronization local and cloud drone park for efficiency';
COMMENT ON COLUMN public.pilot.verified IS 'Verification of pilot status';
