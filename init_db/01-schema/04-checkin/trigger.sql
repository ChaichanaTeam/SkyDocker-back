CREATE TRIGGER trg_auto_calc_homepoint_checkin_h3
BEFORE INSERT OR UPDATE OF home_point ON checkin
FOR EACH ROW
EXECUTE FUNCTION auto_calc_homepoint_h3();


CREATE OR REPLACE FUNCTION accumulate_flight_time()
RETURNS TRIGGER AS $$
DECLARE
    v_seconds integer;
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status
       AND NEW.status IN ('ended_intime', 'late_end', 'loss_of_control') THEN

        v_seconds := GREATEST(0, EXTRACT(EPOCH FROM (NOW() - NEW.starts_at))::integer);

        UPDATE pilot
        SET flight_time = flight_time + v_seconds
        WHERE id = NEW.pilot_id;

        UPDATE drone
        SET flight_time = flight_time + v_seconds
        WHERE id = NEW.drone_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_accumulate_flight_time
AFTER UPDATE OF status ON checkin
FOR EACH ROW
EXECUTE FUNCTION accumulate_flight_time();


CREATE OR REPLACE FUNCTION process_overdue_checkins()
RETURNS integer AS $$
DECLARE
    v_late_count integer;
    v_ended_count integer;
BEGIN
    UPDATE checkin
    SET status = 'late'
    WHERE
        status NOT IN ('cancelled', 'loss_of_control', 'ended_intime', 'late_end', 'late')
        AND ends_at <= NOW();

    GET DIAGNOSTICS v_late_count = ROW_COUNT;

    UPDATE checkin
    SET status = 'late_end'
    WHERE
        status = 'late'
        AND ends_at <= NOW() - interval '3 hours';

    GET DIAGNOSTICS v_ended_count = ROW_COUNT;

    IF v_late_count > 0 OR v_ended_count > 0 THEN
        RAISE NOTICE 'Check-ins marked late: %, auto-ended: %', v_late_count, v_ended_count;
    END IF;

    RETURN v_late_count + v_ended_count;
END;
$$ LANGUAGE plpgsql;

SELECT cron.schedule(
    'process-overdue-checkins',
    '* * * * *',
    'SELECT process_overdue_checkins()'
);