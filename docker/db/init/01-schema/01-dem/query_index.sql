CREATE INDEX idx_dem_rast ON dem USING GIST (ST_ConvexHull(rast));

CREATE INDEX idx_dem_tile ON dem (tile);
