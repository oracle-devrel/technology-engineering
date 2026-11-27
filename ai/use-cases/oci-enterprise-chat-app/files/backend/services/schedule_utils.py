"""UTC schedules with standard cron weekday numbering (Sunday = 0/7)."""

from datetime import UTC

from apscheduler.triggers.cron import CronTrigger


def as_utc(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def cron_trigger(expression):
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError("Cron expression must have exactly 5 fields")
    weekday = parts[4].lower()
    if weekday != "*" and any(char.isdigit() for char in weekday):
        days = set()
        for item in weekday.split(","):
            interval, _, step_text = item.partition("/")
            step = int(step_text) if step_text else 1
            if step < 1:
                raise ValueError("Cron step must be positive")
            if interval == "*":
                start, end = 0, 6
            elif "-" in interval:
                start, end = map(int, interval.split("-"))
            else:
                start = end = int(interval)
            if not 0 <= start <= end <= 7:
                raise ValueError("Cron weekday must be between 0 and 7")
            days.update((day - 1) % 7 for day in range(start, end + 1, step))
        weekday = ",".join(str(day) for day in sorted(days))
    return CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=weekday,
        timezone=UTC,
    )
