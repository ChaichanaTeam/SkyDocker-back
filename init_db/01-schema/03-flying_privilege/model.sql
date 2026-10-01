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
