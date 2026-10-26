CREATE TABLE pilot_to_flying_privileges (
    id                  bigserial PRIMARY KEY,
    
    pilot_id            bigint NOT NULL,
    flying_privilege    flying_privileges NOT NULL,

    FOREIGN KEY (pilot_id) REFERENCES pilot(id)
);

COMMENT ON TABLE  public.pilot_to_flying_privileges IS 'Many-to-Many relation. Pilots can have many privileges';
COMMENT ON COLUMN public.pilot_to_flying_privileges.flying_privilege IS 'Type of privelege which pilot gained through his training';


CREATE TABLE verification_request (
    id              bigserial PRIMARY KEY,
    pilot_id        bigint NOT NULL,

    status          verification_request_status DEFAULT 'pending' NOT NULL,

    first_name      character varying(255) NOT NULL,
    last_name       character varying(255) NOT NULL,
    email           character varying(255) NOT NULL,
    phone_number    character varying(15),
    pilot_number    character varying(255) NOT NULL,
    
    reason          TEXT,
    verified_by     integer,
    verified_at     timestamptz(0),
    
    created_at      timestamptz(0) DEFAULT now() NOT NULL,

    FOREIGN KEY (pilot_id) REFERENCES pilot(id),
    FOREIGN KEY (verified_by) REFERENCES afd_moderator(id)
);

CREATE UNIQUE INDEX verification_request_one_pending_per_pilot
    ON verification_request (pilot_id)
    WHERE status = 'pending';

COMMENT ON TABLE  public.verification_request IS 'Request which pilot submitting to get verification and privileges.
                                            If status is verified, user becomes full-fledged pilot with appropriate priveleges and access';
COMMENT ON COLUMN public.verification_request.status IS 'Only one pending request per pilot. Rejected and withdrawn requests lose their documents, approved ones keep them until the pilot moves them to the organizer';
COMMENT ON COLUMN public.verification_request.first_name IS 'Contact data snapshot at submission. Filled from pilot profile when not provided';
COMMENT ON COLUMN public.verification_request.pilot_number IS 'Pilot number from the operator registration document. Copied to pilot on approval';
COMMENT ON COLUMN public.verification_request.reason IS 'Optional field. If status is obligated to be precised, like _rejected_, so will be a reason';


CREATE TABLE verification_document (
    id                  bigserial PRIMARY KEY,
    request_id          bigint NOT NULL,

    document_path       character varying(255) NOT NULL,
    document_type       verification_document_type NOT NULL,
    
    created_at          timestamptz(0) DEFAULT now() NOT NULL,

    FOREIGN KEY (request_id) REFERENCES verification_request(id),
    UNIQUE (request_id, document_type)
);

COMMENT ON TABLE  public.verification_document IS 'Temporary table for documents which confirms user privileges to be verified pilot';
COMMENT ON COLUMN public.verification_document.document_path IS 'Object key in the verification bucket of storage, without bucket name';
COMMENT ON COLUMN public.verification_document.document_type IS 'One document per type: privilege_* training certificates and operator_number registration document';
