create type model_manufacturer as enum (
    'dm1',
    'dm2',
    'dm3'
);

create type geo_zone_type as enum (
    'gzt1',
    'gzt2',
    'gzt3'
);

create type user_activity as enum (
    'ua1',
    'ua2',
    'ua3'
);

create type flying_privileges as enum (
    'fp1',
    'fp2',
    'fp3'
);

create type verification_request_status as enum (
    'pending',
    'vrs1',
    'vrs2',
    'vrs3'
);

create type verification_document_type as enum (
    'vdt1',
    'vdt2',
    'vdt3'
);

-- create type mission_operation_type as enum (
--     'mot1',
--     'mot2',
--     'mot3'
-- );

create type mission_category as enum (
    'open',
    'specific',
    'certified'
);

create type mission_flight_goal as enum (
    'mfg1',
    'mfg2',
    'mfg3'
);

create type mission_status as enum (
    'created',
    'cancelled',
    'pending',
    'accepted',
    'active',
    'late',
    'loss_of_control',
    'ended_intime',
    'late_end'
);

create type atc_decision as enum (
    'pending',
    'approved',
    'rejected'
);