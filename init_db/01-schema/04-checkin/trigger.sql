CREATE TRIGGER trg_auto_calc_homepoint_checkin_h3
BEFORE INSERT OR UPDATE OF home_point ON checkin
FOR EACH ROW
EXECUTE FUNCTION auto_calc_homepoint_h3();


CREATE OR REPLACE FUNCTION accumulate_pilot_flight_time()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE pilot
    SET flight_time = flight_time + NEW.time
    WHERE id = NEW.pilot_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_accumulate_pilot_flight_time
AFTER INSERT ON checkin
FOR EACH ROW
EXECUTE FUNCTION accumulate_pilot_flight_time();
