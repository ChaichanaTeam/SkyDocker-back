CREATE INDEX idx_checkin_h3_country ON checkin (h3_index, country_id);


CREATE INDEX idx_checkin_home_point ON checkin USING GIST (home_point);