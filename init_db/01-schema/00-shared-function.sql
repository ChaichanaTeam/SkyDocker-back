CREATE OR REPLACE FUNCTION auto_calc_homepoint_h3()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.home_point IS NOT NULL AND (TG_OP = 'INSERT' OR NEW.home_point IS DISTINCT FROM OLD.home_point) THEN
        NEW.h3_index := h3_lat_lng_to_cell(NEW.home_point, current_setting('settings.h3_resolution')::integer);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
