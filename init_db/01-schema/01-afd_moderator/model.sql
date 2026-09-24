CREATE TABLE afd_moderator (
    id              serial PRIMARY KEY,

    first_name      character varying(255) NOT NULL,
    last_name       character varying(255) NOT NULL,
    email           character varying(255) NOT NULL,
    password_hash   character varying(255) NOT NULL,
    
    created_at      timestamptz(0) DEFAULT now() NOT NULL
);

COMMENT ON TABLE public.afd_moderator IS 'Table containing credentials of admins responsible for document verification and adding new drone manufacturers';
