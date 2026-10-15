create type geo_zone_type as enum (
    'dra_p',
    'dra_rh',
    'dra_rm',
    'dra_rl',
    'dra_t',
    'dra_u',
    'dra_i'
);

COMMENT ON TYPE geo_zone_type IS 'PAZP drone geographical zones. dra_p - flights only with the zone manager consent;
                                  dra_rh/dra_rm/dra_rl - restricted, height allowance depends on drone mass;
                                  dra_t - extra technical requirements, dra_u - U-space services required, dra_i - informational';
