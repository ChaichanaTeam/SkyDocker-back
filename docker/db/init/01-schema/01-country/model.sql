CREATE TABLE country (
    id              smallserial PRIMARY KEY,
    
    name            character varying(50) NOT NULL,
    country_tag     character varying(2) NOT NULL
);

COMMENT ON TABLE  public.country             IS 'Table discrabing country implemented by application';
COMMENT ON COLUMN public.country.name        IS 'Country name normalized';
COMMENT ON COLUMN public.country.country_tag IS '2 symbol country code standardized with ISO 3166-1 alpha-2';
