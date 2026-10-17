CREATE OR REPLACE FUNCTION audit.log_verification_request_action()
RETURNS TRIGGER 
SECURITY DEFINER 
AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO audit.admin_actions_log (
            admin_id,
            admin_type,
            action,
            target_table,
            target_id,
            old_data,
            new_data
        ) VALUES (
            COALESCE(NEW.verified_by, 0),
            'afd_moderator',
            'STATUS_CHANGED_TO_' || UPPER(NEW.status::text),
            TG_TABLE_NAME,
            NEW.id,
            to_jsonb(OLD),
            to_jsonb(NEW)
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_verification_request
AFTER UPDATE ON verification_request
FOR EACH ROW
EXECUTE FUNCTION audit.log_verification_request_action();


CREATE OR REPLACE FUNCTION audit.log_geozone_related_action()
RETURNS TRIGGER
SECURITY DEFINER
AS $$
DECLARE
    v_current_admin_id integer;
BEGIN
    v_current_admin_id := current_setting('app.current_admin_id', true)::integer;

    INSERT INTO audit.admin_actions_log (
        admin_id,
        admin_type,
        action,
        target_table,
        target_id,
        old_data,
        new_data
    ) VALUES (
        COALESCE(v_current_admin_id, 0),
        'system_admin',
        UPPER(TG_TABLE_NAME) || '_' || TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) ELSE NULL END
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_geo_zone
AFTER INSERT OR UPDATE OR DELETE ON geo_zone
FOR EACH ROW
EXECUTE FUNCTION audit.log_geozone_related_action();

CREATE TRIGGER trg_audit_activity_time
AFTER INSERT OR UPDATE OR DELETE ON activity_time
FOR EACH ROW
EXECUTE FUNCTION audit.log_geozone_related_action();