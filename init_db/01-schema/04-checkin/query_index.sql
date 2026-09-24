CREATE INDEX idx_checkin_h3_country ON checkin (h3_index, country_id);


CREATE INDEX idx_checkin_home_point ON checkin USING GIST (home_point);


CREATE UNIQUE INDEX idx_checkin_one_active_per_pilot
    ON checkin (pilot_id)
    WHERE status IN ('active', 'late');


CREATE INDEX idx_checkin_drone ON checkin (drone_id);
