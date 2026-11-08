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
