CREATE OR REPLACE FUNCTION sync_pilot_verification()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'approved' AND (TG_OP = 'INSERT' OR OLD.status != 'approved') THEN
        NEW.verified_at := COALESCE(NEW.verified_at, NOW());
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_pilot_verification
BEFORE INSERT OR UPDATE OF status ON verification_request
FOR EACH ROW
EXECUTE FUNCTION sync_pilot_verification();
