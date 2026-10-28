CREATE TABLE dem (
    id      bigserial PRIMARY KEY,

    tile    character varying(16) NOT NULL,
    rast    raster NOT NULL
);

COMMENT ON TABLE  public.dem IS 'Ground elevation model (Copernicus DEM GLO-90): 1° tiles cut into rasters of 100 x 100 pixels';
COMMENT ON COLUMN public.dem.tile IS 'Source tile named after its south-west corner, e.g. N52_00_E016_00; a tile is stored whole';
COMMENT ON COLUMN public.dem.rast IS 'Heights in metres above mean sea level, about 90 m per pixel';
