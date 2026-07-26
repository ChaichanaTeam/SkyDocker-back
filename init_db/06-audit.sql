CREATE TABLE audit.admin_actions_log (
    id              bigserial,
    admin_id        integer NOT NULL,
    admin_type      varchar(50) NOT NULL,
    action          varchar(50) NOT NULL,
    target_table    varchar(50) NOT NULL,
    target_id       bigint NOT NULL,
    old_data        jsonb,
    new_data        jsonb,
    created_at      timestamptz(0) DEFAULT now() NOT NULL,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);


CREATE TABLE audit.admin_actions_log_default 
PARTITION OF audit.admin_actions_log DEFAULT;


CREATE OR REPLACE FUNCTION audit.create_next_month_partition()
RETURNS void AS $$
DECLARE
    v_next_month date;
    v_month_after date;
    v_partition_name text;
    v_sql text;
BEGIN
    v_next_month := date_trunc('month', NOW() + interval '1 month')::date;
    v_month_after := v_next_month + interval '1 month';
    
    v_partition_name := 'audit.admin_actions_log_' || to_char(v_next_month, 'YYYY_MM');

    v_sql := format(
        'CREATE TABLE IF NOT EXISTS %s PARTITION OF audit.admin_actions_log FOR VALUES FROM (%L) TO (%L);',
        v_partition_name, v_next_month, v_month_after
    );
    
    EXECUTE v_sql;
END;
$$ LANGUAGE plpgsql;

SELECT cron.schedule('create_audit_partition', '0 0 28 * *', 'SELECT audit.create_next_month_partition()');


CREATE OR REPLACE FUNCTION anonymize_pilot(p_pilot_id bigint)
RETURNS void AS $$
BEGIN
    UPDATE pilot
    SET 
        first_name = 'Deleted',
        last_name = 'User',
        email = 'anonymized_' || id || '@deleted.local',
        phone_number = '0000000000',
        pilot_number = NULL,
        password_hash = 'deleted',
        dronepark_hash = NULL,
        verification_code_hash = NULL,
        show_to_public = false,
        verified = false
    WHERE id = p_pilot_id;

    UPDATE mission
    SET 
        spotter_first_name = 'Anonymized',
        spotter_last_name = 'Anonymized',
        spotter_phone = '0000000000'
    WHERE pilot_id = p_pilot_id AND spotter_first_name IS NOT NULL;

    UPDATE audit.admin_actions_log
    SET 
        new_data = new_data - 'email' - 'phone_number' - 'first_name' - 'last_name',
        old_data = old_data - 'email' - 'phone_number' - 'first_name' - 'last_name'
    WHERE target_table = 'pilot' AND target_id = p_pilot_id;

    DELETE FROM verification_document 
    WHERE request_id IN (SELECT id FROM verification_request WHERE pilot_id = p_pilot_id);

END;
$$ LANGUAGE plpgsql;