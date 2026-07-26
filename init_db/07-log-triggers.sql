CREATE OR REPLACE FUNCTION audit.log_atc_approval_action()
RETURNS TRIGGER
SECURITY DEFINER
AS $$
BEGIN
    INSERT INTO audit.admin_actions_log (
        admin_id,
        admin_type,
        action,
        target_table,
        target_id,
        old_data,
        new_data
    ) VALUES (
        NEW.atc_admin_id,
        'atc_admin',
        TG_OP,
        TG_TABLE_NAME,
        NEW.id,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) ELSE NULL END
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_atc_approval
AFTER INSERT OR UPDATE ON mission_atc_approval
FOR EACH ROW
EXECUTE FUNCTION audit.log_atc_approval_action();


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


CREATE OR REPLACE FUNCTION audit.log_atc_admin_action()
RETURNS TRIGGER 
SECURITY DEFINER 
AS $$
BEGIN
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND NEW.is_revoked IS DISTINCT FROM OLD.is_revoked) THEN
        INSERT INTO audit.admin_actions_log (
            admin_id,
            admin_type,
            action,
            target_table,
            target_id,
            old_data,
            new_data
        ) VALUES (
            NEW.id, 
            'system_or_superadmin',
            CASE 
                WHEN TG_OP = 'INSERT' THEN 'CREATE_ATC_ACCOUNT'
                WHEN NEW.is_revoked = true THEN 'REVOKE_ATC_KEY'
                ELSE 'RESTORE_ATC_KEY'
            END,
            TG_TABLE_NAME,
            NEW.id,
            CASE WHEN TG_OP = 'UPDATE' THEN to_jsonb(OLD) ELSE NULL END,
            to_jsonb(NEW)
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_atc_admin
AFTER INSERT OR UPDATE ON atc_admin
FOR EACH ROW
EXECUTE FUNCTION audit.log_atc_admin_action();


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

CREATE TRIGGER trg_audit_geo_zone_to_atc
AFTER INSERT OR UPDATE OR DELETE ON geo_zone_to_atc
FOR EACH ROW
EXECUTE FUNCTION audit.log_geozone_related_action();

CREATE TRIGGER trg_audit_activity_time
AFTER INSERT OR UPDATE OR DELETE ON activity_time
FOR EACH ROW
EXECUTE FUNCTION audit.log_geozone_related_action();