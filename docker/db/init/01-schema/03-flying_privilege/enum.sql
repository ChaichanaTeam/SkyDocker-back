create type verification_request_status as enum (
    'pending',
    'approved',
    'rejected',
    'withdrawn'
);


create type verification_document_type as enum (
    'privilege_a1',
    'privilege_a2',
    'privilege_a3',
    'privilege_sts01',
    'privilege_sts02',
    'operator_number'
);
