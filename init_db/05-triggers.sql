CREATE OR REPLACE FUNCTION sync_pilot_verification()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'approved' AND (OLD.status IS NULL OR OLD.status != 'approved') THEN
        UPDATE pilot
        SET verified = TRUE
        WHERE id = NEW.pilot_id;
        
        NEW.verified_at := COALESCE(NEW.verified_at, NOW());

    ELSIF NEW.status = 'rejected' THEN
        UPDATE pilot
        SET verified = FALSE
        WHERE id = NEW.pilot_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_pilot_verification
BEFORE INSERT OR UPDATE OF status ON verification_request
FOR EACH ROW
EXECUTE FUNCTION sync_pilot_verification();


CREATE OR REPLACE FUNCTION auto_calc_homepoint_h3()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.home_point IS NOT NULL AND (TG_OP = 'INSERT' OR NEW.home_point IS DISTINCT FROM OLD.home_point) THEN
        NEW.h3_index := h3_lat_lng_to_cell(ST_Y(NEW.home_point), ST_X(NEW.home_point), 8);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auto_calc_homepoint_mission_h3
BEFORE INSERT OR UPDATE OF home_point ON mission
FOR EACH ROW
EXECUTE FUNCTION auto_calc_homepoint_h3();

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


CREATE OR REPLACE FUNCTION handle_atc_revoke()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_revoked = TRUE AND (OLD.is_revoked = FALSE OR OLD.is_revoked IS NULL) THEN
        IF NEW.revoked_at IS NULL THEN
            NEW.revoked_at := NOW();
        END IF;
        
        IF NEW.revoke_reason IS NULL OR TRIM(NEW.revoke_reason) = '' THEN
            NEW.revoke_reason := 'Revoked by administration';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_handle_atc_revoke
BEFORE INSERT OR UPDATE OF is_revoked ON atc_admin
FOR EACH ROW
EXECUTE FUNCTION handle_atc_revoke();


CREATE OR REPLACE FUNCTION revoke_expired_atc_keys()
RETURNS integer AS $$
DECLARE
    v_updated_count integer;
BEGIN
    UPDATE atc_admin
    SET 
        is_revoked = true,
        revoked_at = NOW(),
        revoke_reason = COALESCE(revoke_reason, 'API key expired automatically by system')
    WHERE 
        is_revoked = false 
        AND expires_at <= NOW();

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    
    IF v_updated_count > 0 THEN
        RAISE NOTICE 'Auto-revoked % expired ATC API keys', v_updated_count;
    END IF;

    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

SELECT cron.schedule(
    'auto-revoke-atc-keys',
    '*/30 * * * *',
    'SELECT revoke_expired_atc_keys()'
);


CREATE OR REPLACE FUNCTION set_atc_approval_time()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status AND NEW.status IN ('approved', 'rejected') THEN
        NEW.decided_at := NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_set_atc_approval_time
BEFORE UPDATE ON mission_atc_approval
FOR EACH ROW
EXECUTE FUNCTION set_atc_approval_time();


CREATE OR REPLACE FUNCTION aggregate_mission_status()
RETURNS TRIGGER AS $$
DECLARE
    v_total integer;
    v_approved integer;
    v_rejected integer;
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        
        SELECT 
            COUNT(*),
            COUNT(*) FILTER (WHERE status = 'approved'),
            COUNT(*) FILTER (WHERE status = 'rejected')
        INTO v_total, v_approved, v_rejected
        FROM mission_atc_approval
        WHERE mission_id = NEW.mission_id;

        IF v_rejected > 0 THEN
            UPDATE mission SET status = 'cancelled' WHERE id = NEW.mission_id;
            
        ELSIF v_approved = v_total AND v_total > 0 THEN
            UPDATE mission SET status = 'accepted' WHERE id = NEW.mission_id;
            
        ELSE
            UPDATE mission SET status = 'pending' WHERE id = NEW.mission_id;
        END IF;
        
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_aggregate_mission_status
AFTER UPDATE ON mission_atc_approval
FOR EACH ROW
EXECUTE FUNCTION aggregate_mission_status();


