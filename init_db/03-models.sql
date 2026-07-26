CREATE TABLE country (
    id              smallserial PRIMARY KEY,
    
    name            character varying(50) NOT NULL,
    country_tag     character varying(2) NOT NULL
);

COMMENT ON TABLE  public.country             IS 'Table discrabing country implemented by application';
COMMENT ON COLUMN public.country.name        IS 'Country name normalized';
COMMENT ON COLUMN public.country.country_tag IS '2 symbol country code standardized with ISO 3166-1 alpha-2';


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


CREATE TABLE afd_moderator (
    id              serial PRIMARY KEY,

    first_name      character varying(255) NOT NULL,
    last_name       character varying(255) NOT NULL,
    email           character varying(255) NOT NULL,
    password_hash   character varying(255) NOT NULL,
    
    created_at      timestamptz(0) DEFAULT now() NOT NULL
);

COMMENT ON TABLE public.afd_moderator IS 'Table containing credentials of admins responsible for document verification and adding new drone manufacturers';


CREATE TABLE atc_admin (
    id              serial PRIMARY KEY,
    country_id      smallint NOT NULL,

    email           character varying(255) NOT NULL,
    affiliation     character varying(4) NOT NULL,
    api_key         character varying(255) NOT NULL,
    
    is_revoked      boolean DEFAULT false NOT NULL,
    revoke_reason   text,
    expires_at      timestamptz(0) NOT NULL,
    revoked_at      timestamptz(0),
    
    created_at      timestamptz(0) DEFAULT now() NOT NULL,

    FOREIGN KEY (country_id) REFERENCES country(id)
);

COMMENT ON TABLE  public.atc_admin IS 'Table containing credentials and contact information of ATC operators responsible maintaining their geozones';
COMMENT ON COLUMN public.atc_admin.email IS 'Method of contact with ATC';
COMMENT ON COLUMN public.atc_admin.affiliation IS 'ICAO';
COMMENT ON COLUMN public.atc_admin.api_key IS 'Hashed API key used for gaining access to geozones and missions/check-ins';
COMMENT ON COLUMN public.atc_admin.revoke_reason IS 'Reason for revoking API key';
COMMENT ON COLUMN public.atc_admin.expires_at IS 'After expiring - API key revokes automatically. Automatically refreshes if ATC performed operation within time period';


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


CREATE TABLE pilot (
    id                              bigserial PRIMARY KEY,
    
    first_name                      character varying(255) NOT NULL,
    last_name                       character varying(255) NOT NULL,
    
    email                           character varying(255) NOT NULL,
    phone_number                    character varying(15) NOT NULL,
    pilot_number                    character varying(255) NULL,
    
    password_hash                   character varying(255) NOT NULL,
    verification_code_hash          character varying(255),
    verification_code_created_at    timestamptz(0),
    
    country_id                      smallint NOT NULL,
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
COMMENT ON COLUMN public.pilot.verification_code_hash IS 'Backend returning hashed 6 digit code and sending its code to selected method by user';
COMMENT ON COLUMN public.pilot.verification_code_created_at IS 'Used to calculate code expiration';
COMMENT ON COLUMN public.pilot.show_to_public IS 'Could have feature';
COMMENT ON COLUMN public.pilot.activity IS 'Could have feature';
COMMENT ON COLUMN public.pilot.flight_time IS 'Telemetry. Could have feature';
COMMENT ON COLUMN public.pilot.dronepark_hash IS 'Used to synchronization local and cloud drone park for efficiency';
COMMENT ON COLUMN public.pilot.verified IS 'Verification of pilot status';


CREATE TABLE drone (
    id                  bigserial PRIMARY KEY,
    pilot_id            bigint NOT NULL,

    model_id            integer NOT NULL,
    serial_number       character varying(255) NOT NULL,

    FOREIGN KEY (model_id) REFERENCES model(id),
    FOREIGN KEY (pilot_id) REFERENCES pilot(id)
);

COMMENT ON TABLE public.drone IS 'Drones created by user for his dronepark';


CREATE TABLE geo_zone_to_atc (
    id              bigserial PRIMARY KEY,
    
    geo_zone_id     bigint NOT NULL,
    atc_admin_id    integer NOT NULL,

    FOREIGN KEY (atc_admin_id) REFERENCES atc_admin(id),
    FOREIGN KEY (geo_zone_id) REFERENCES geo_zone(id)
);

COMMENT ON TABLE public.drone IS 'Many-to-Many relation. Used to bind ATC responsibility to zones';


CREATE TABLE user_to_flying_privileges (
    id                  bigserial PRIMARY KEY,
    
    pilot_id            bigint NOT NULL,
    flying_privilege    flying_privileges NOT NULL,

    FOREIGN KEY (pilot_id) REFERENCES pilot(id)
);

COMMENT ON TABLE  public.user_to_flying_privileges IS 'Many-to-Many relation. Pilots can have many privileges';
COMMENT ON COLUMN public.user_to_flying_privileges.flying_privilege IS 'Type of privelege which pilot gained through his training';


CREATE TABLE verification_request (
    id              bigserial PRIMARY KEY,
    pilot_id        bigint NOT NULL,

    status          verification_request_status DEFAULT 'pending' NOT NULL,
    
    reason          TEXT,
    verified_by     integer,
    verified_at     timestamptz(0),
    
    created_at      timestamptz(0) DEFAULT now() NOT NULL,

    FOREIGN KEY (pilot_id) REFERENCES pilot(id),
    FOREIGN KEY (verified_by) REFERENCES afd_moderator(id)
);

COMMENT ON TABLE  public.verification_request IS 'Request which pilot submitting to get verification and privileges.
                                            If status is verified, user becomes full-fledged pilot with appropriate priveleges and access';
COMMENT ON COLUMN public.verification_request.status IS 'If status is in complete state [rejected, apporoved] the request will be deleted with associated documents';
COMMENT ON COLUMN public.verification_request.reason IS 'Optional field. If status is obligated to be precised, like _rejected_, so will be a reason';


CREATE TABLE verification_document (
    id                  bigserial PRIMARY KEY,
    request_id          bigint NOT NULL,

    document_path       character varying(255) NOT NULL,
    document_type       verification_document_type NOT NULL,
    
    created_at          timestamptz(0) DEFAULT now() NOT NULL,

    FOREIGN KEY (request_id) REFERENCES verification_request(id)
);

COMMENT ON TABLE  public.verification_document IS 'Temporary table for documents which confirms user privileges to be verified pilot';
COMMENT ON COLUMN public.verification_document.document_path IS 'Path for document to which admin need to get access in CDN';
COMMENT ON COLUMN public.verification_document.document_type IS 'Enum to identify document, such as _drone pilot exam_ and _drone operator registration_';


CREATE TABLE mission (
    id                      bigserial PRIMARY KEY,
    pilot_id                bigint NOT NULL,
    
    -- operation_type          mission_operation_type NOT NULL,
    drone_id                bigint NOT NULL,
    category                mission_category NOT NULL,
    flight_goal             mission_flight_goal,
    description             TEXT,
    flying_privilege        flying_privileges NOT NULL,
    
    h3_index                h3index NOT NULL,
    country_id              smallint NOT NULL,
    home_point              GEOMETRY(Point, 4326) NOT NULL,
    height                  integer NOT NULL,
    range                   integer NOT NULL,
    starts_at               timestamptz(0) NOT NULL,
    ends_at                 timestamptz(0) NOT NULL,
    time                    integer NOT NULL,
    
    spotter_first_name      character varying(255),
    spotter_last_name       character varying(255),
    spotter_phone           character varying(15),

    created_at              timestamptz(0) DEFAULT now() NOT NULL,

    FOREIGN KEY (pilot_id) REFERENCES pilot(id),
    FOREIGN KEY (drone_id) REFERENCES drone(id),
    FOREIGN KEY (country_id) REFERENCES country(id)
);

COMMENT ON TABLE  public.mission IS 'Table for creation and pre-verification flying mission which summbitted to ATC';
-- COMMENT ON COLUMN public.mission.operation_type IS '';
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


CREATE TABLE mission_atc_approval (
    id                  bigserial PRIMARY KEY,

    mission_id          bigint NOT NULL,
    atc_admin_id        integer NOT NULL,
    
    status              mission_status DEFAULT 'created' NOT NULL,
    decided_at          timestamptz(0),

    FOREIGN KEY (mission_id) REFERENCES mission(id),
    FOREIGN KEY (atc_admin_id) REFERENCES atc_admin(id)
);

COMMENT ON TABLE public.mission_atc_approval IS 'More than one ATC must approve, if more than one ATC are affiliated with geo-zone';