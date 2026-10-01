create type flying_privileges as enum (
    'a1',
    'a2',
    'a3',
    'sts01',
    'sts02'
);


create type operational_category as enum (
    'open',
    'specific',
    'certified'
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
