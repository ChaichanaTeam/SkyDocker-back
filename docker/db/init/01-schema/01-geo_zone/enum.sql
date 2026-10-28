create type geo_zone_type as enum (
    'dra_p',
    'dra_r',
    'dra_rh',
    'dra_rm',
    'dra_rl',
    'dra_t',
    'dra_u',
    'dra_i'
);

COMMENT ON TYPE geo_zone_type IS 'PANSA drone geographical zones (ULC guidelines 4/2025). dra_p - prohibited;
                                  dra_r - restricted, flights with the zone manager consent;
                                  dra_rh/dra_rm/dra_rl - restricted with high/medium/low chance of getting the consent;
                                  dra_t - extra technical requirements, dra_u - U-space services required, dra_i - informational';


create type geo_zone_activity_mode as enum (
    'permanent',
    'scheduled',
    'inherited'
);

COMMENT ON TYPE geo_zone_activity_mode IS 'permanent - active during the whole validity period;
                                           scheduled - active only within its activity_time windows;
                                           inherited - active while its parent zone is active';


create type geo_zone_activity_source as enum (
    'aup',
    'uup',
    'notam'
);

COMMENT ON TYPE geo_zone_activity_source IS 'Origin of an activity window: AUP/UUP airspace reservation or NOTAM';
