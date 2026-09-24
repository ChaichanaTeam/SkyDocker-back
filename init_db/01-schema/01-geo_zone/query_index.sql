CREATE INDEX idx_geo_zone_polygon ON geo_zone USING GIST (zone_polygon);


CREATE INDEX idx_geo_zone_h3_index ON geo_zone_h3 (h3_index);


CREATE INDEX idx_activity_time_geo_zone ON activity_time (geo_zone_id);
