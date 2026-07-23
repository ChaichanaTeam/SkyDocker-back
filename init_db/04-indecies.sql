CREATE INDEX idx_geo_zone_h3_index ON geo_zone_h3 (h3_index);

CREATE INDEX idx_checkin_h3_country ON checkin (h3_index, country_id);

CREATE INDEX idx_geo_zone_polygon ON geo_zone USING GIST (zone_polygon);

CREATE INDEX idx_checkin_home_point ON checkin USING GIST (home_point);