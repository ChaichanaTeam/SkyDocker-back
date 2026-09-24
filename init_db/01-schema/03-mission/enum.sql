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
    'recreational',
    'photography',
    'inspection',
    'commercial',
    'survey'
);
