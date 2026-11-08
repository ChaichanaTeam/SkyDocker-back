create type verification_request_status as enum (
    'pending',
    'rejected'
);


create type verification_document_type as enum (
    'operator_registration',
    'certificate'
);
