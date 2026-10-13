CREATE TRIGGER trg_auto_calc_homepoint_mission_h3
BEFORE INSERT OR UPDATE OF home_point ON mission
FOR EACH ROW
EXECUTE FUNCTION auto_calc_homepoint_h3();
