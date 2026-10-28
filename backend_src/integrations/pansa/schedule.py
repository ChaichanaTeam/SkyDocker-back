from datetime import date, datetime, time, timedelta, timezone

from .schema import Notam, NotamSchedule


Window = tuple[datetime, datetime]

_CANCEL = "NOTAMC"
_REPLACE = "NOTAMR"


def current_notams(notams: list[Notam]) -> list[Notam]:
    """Drops NOTAMs replaced by a NOTAMR from the same list, PANSA still returns them as active."""
    replaced = {notam.replaces for notam in notams if notam.type == _REPLACE and notam.replaces}

    return [notam for notam in notams if notam.series not in replaced]


def notam_windows(notam: Notam, since: datetime, until: datetime) -> list[Window]:
    """Activity windows of a NOTAM that end after ``since``, merged and rounded down to seconds.

    Repeating rules are expanded day by day up to ``until``; continuous periods keep their real end,
    so the result does not change between syncs.
    """
    if notam.type == _CANCEL or not notam.active:
        return []

    period = (notam.starts_at, notam.ends_at)
    if not notam.schedule:
        windows = [period]
    else:
        windows = [window for rule in notam.schedule for window in _rule_windows(rule, period, since, until)]

    clipped = [(max(start, period[0]), min(end, period[1])) for start, end in windows]
    return _merge([(_seconds(start), _seconds(end)) for start, end in clipped if start < end and end > since])


def _rule_windows(rule: NotamSchedule, period: Window, since: datetime, until: datetime) -> list[Window]:
    if rule.period_mode == "single":
        return [(rule.begin or period[0], rule.end or period[1])]

    if rule.repeat_mode not in ("weekdays", "days"):
        # "non-stop" and anything unknown: active for the whole NOTAM period
        return [period]

    windows = []
    # start a day earlier for slots that cross midnight
    day = max(since, period[0]).date() - timedelta(days=1)
    last = min(until, period[1]).date()
    while day <= last:
        if _day_matches(rule, day):
            windows.extend(_day_windows(rule, day))
        day += timedelta(days=1)

    return windows


def _day_matches(rule: NotamSchedule, day: date) -> bool:
    # months and weekdays are numbered like JavaScript Date: January = 0, Sunday = 0
    if rule.months and day.month - 1 not in rule.months:
        return False

    if rule.repeat_mode == "weekdays":
        return day.isoweekday() % 7 in rule.weekdays

    return day.day in rule.days


def _day_windows(rule: NotamSchedule, day: date) -> list[Window]:
    midnight = datetime.combine(day, time(), timezone.utc)

    if rule.slot_mode != "slots" or not rule.hour_slots:
        return [(midnight, midnight + timedelta(days=1))]

    windows = []
    for slot in rule.hour_slots:
        start = midnight + timedelta(hours=slot.begin.hour, minutes=slot.begin.minute)
        end = midnight + timedelta(hours=slot.end.hour, minutes=slot.end.minute)
        if end <= start:
            end += timedelta(days=1)
        windows.append((start, end))

    return windows


def _merge(windows: list[Window]) -> list[Window]:
    merged: list[Window] = []
    for start, end in sorted(windows):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged


def _seconds(moment: datetime) -> datetime:
    # activity_time keeps whole seconds, compare the same values on the next sync
    return moment.replace(microsecond=0)
