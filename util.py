import calendar
import re
from datetime import timedelta, datetime, timezone
from typing import Optional, Tuple

from console_colors import CYAN, GREEN, RESET
from db import set_user


def update_users(bot, target=None):
    import disnake

    def process_user(u):
        if not u.bot:
            avatar = u.avatar.url if u.avatar else f"https://cdn.discordapp.com/embed/avatars/{u.id % 5}.png"
            set_user(u.id, u.display_name, avatar)

    if isinstance(target, (disnake.User, disnake.Member)):
        process_user(target)
        print(f"{CYAN}Scanning user {GREEN}@{target.name}{RESET}")

    elif isinstance(target, disnake.Guild):
        for member in target.members:
            process_user(member)
        print(f"{CYAN}Scanning {GREEN}{len(target.members)}{CYAN} user{'s' if len(target.members) != 1 else ''} in {target.name}{RESET}")

    else:
        for u in bot.users:
            process_user(u)
        print(f"{CYAN}Scanning {GREEN}{len(bot.users)}{CYAN} user{'s' if len(bot.users) != 1 else ''}{RESET}")
            
            
UTC = timezone.utc

def _as_aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def normalize_frequency(selected: str) -> str:
    s = (selected or "").strip().lower()
    s = re.sub(r"\s+", " ", s)

    # exact phrases
    if s == "hourly":
        return "HOURLY:1"
    if s == "daily":
        return "DAILY:1"
    if s == "weekly":
        return "WEEKLY"
    if s == "monthly":
        return "MONTHLY"
    if s == "every other week":
        return "BIWEEKLY"
    if s == "every other month":
        return "BIMONTHLY"

    _NUM = r"(\d+(?:\.\d+)?)"

    # "X times per day/week/month"
    m = re.fullmatch(_NUM + r" times per hour", s)
    if m:
        n = int(float(m.group(1)))
        return f"HOURLY:{max(1, n)}"

    m = re.fullmatch(_NUM + r" times per day", s)
    if m:
        n = int(float(m.group(1)))
        return f"DAILY:{max(1, n)}"

    m = re.fullmatch(_NUM + r" times per week", s)
    if m:
        n = int(float(m.group(1)))
        return f"WEEKLY:{max(1, n)}"

    m = re.fullmatch(_NUM + r" times per month", s)
    if m:
        n = int(float(m.group(1)))
        return f"MONTHLY:{max(1, n)}"

    # "every X days/weeks"
    m = re.fullmatch(r"every " + _NUM + r" hours?", s)
    if m:
        n = int(float(m.group(1)))
        return f"EVERY_HOURS:{max(1, n)}"

    m = re.fullmatch(r"every " + _NUM + r" days?", s)
    if m:
        n = int(float(m.group(1)))
        return f"EVERY_DAYS:{max(1, n)}"

    m = re.fullmatch(r"every " + _NUM + r" weeks?", s)
    if m:
        n = int(float(m.group(1)))
        return f"EVERY_WEEKS:{max(1, n)}"

    raise ValueError(f"Unrecognized frequency: {selected!r}")


def _add_months(dt: datetime, months: int) -> datetime:
    dt = _as_aware_utc(dt)
    y = dt.year
    m = dt.month + months
    while m > 12:
        y += 1
        m -= 12
    while m < 1:
        y -= 1
        m += 12

    last_day = calendar.monthrange(y, m)[1]
    day = min(dt.day, last_day)
    return dt.replace(year=y, month=m, day=day)


def _parse_frequency(freq: str) -> Tuple[str, Optional[int]]:
    # returns (kind, n)
    f = (freq or "").strip().upper()

    if f.startswith("HOURLY:"):
        try:
            n = int(f.split(":", 1)[1])
            return ("HOURLY", max(1, n))
        except ValueError:
            return ("HOURLY", 1)

    if f.startswith("DAILY:"):
        try:
            n = int(f.split(":", 1)[1])
            return ("DAILY", max(1, n))
        except ValueError:
            return ("DAILY", 1)

    if f.startswith("EVERY_HOURS:"):
        try:
            n = int(f.split(":", 1)[1])
            return ("EVERY_HOURS", max(1, n))
        except ValueError:
            return ("EVERY_HOURS", 24)

    if f.startswith("EVERY_DAYS:"):
        try:
            n = int(f.split(":", 1)[1])
            return ("EVERY_DAYS", max(1, n))
        except ValueError:
            return ("EVERY_DAYS", 1)

    if f.startswith("WEEKLY:"):
        try:
            n = int(f.split(":", 1)[1])
            return ("WEEKLY_N", max(1, n))
        except ValueError:
            return ("WEEKLY_N", 1)

    if f.startswith("MONTHLY:"):
        try:
            n = int(f.split(":", 1)[1])
            return ("MONTHLY_N_CAL", max(1, n))
        except ValueError:
            return ("MONTHLY_N_CAL", 1)

    if f in {"WEEKLY", "BIWEEKLY", "MONTHLY", "BIMONTHLY"}:
        return (f, None)

    # fallback
    return ("WEEKLY", None)


def _interval_for(anchor_utc: datetime, frequency: str) -> timedelta:
    anchor_utc = _as_aware_utc(anchor_utc)
    kind, n = _parse_frequency(frequency)

    if kind == "DAILY":
        return timedelta(days=1) / n

    if kind == "EVERY_HOURS":
        return timedelta(hours=n)

    if kind == "EVERY_DAYS":
        return timedelta(days=n)

    if kind == "WEEKLY_N":
        return timedelta(days=7) / n

    if kind == "WEEKLY":
        return timedelta(days=7)

    if kind == "BIWEEKLY":
        return timedelta(days=14)

    if kind == "MONTHLY_N_CAL":
        dim = calendar.monthrange(anchor_utc.year, anchor_utc.month)[1]
        return timedelta(days=dim / n)

    # MONTHLY/BIMONTHLY aren't fixed timedeltas; return a rough "staleness" threshold
    if kind == "MONTHLY":
        dim = calendar.monthrange(anchor_utc.year, anchor_utc.month)[1]
        return timedelta(days=dim)

    if kind == "BIMONTHLY":
        dim = calendar.monthrange(anchor_utc.year, anchor_utc.month)[1]
        return timedelta(days=dim * 2)

    return timedelta(days=7)


def _effective_base(now_utc: datetime, last_taken_utc: Optional[datetime], frequency: str) -> datetime:
    now_utc = _as_aware_utc(now_utc)
    if not last_taken_utc:
        return now_utc

    last_taken_utc = _as_aware_utc(last_taken_utc)
    interval = _interval_for(last_taken_utc, frequency)

    # If they're overdue (haven't taken within the interval), reset the anchor to "now"
    if now_utc - last_taken_utc > interval:
        return now_utc

    return last_taken_utc


def compute_next_due(
    now_utc: datetime,
    last_reminded_utc: Optional[datetime],
    frequency: str,
) -> datetime:
    now_utc = _as_aware_utc(now_utc)
    base = _effective_base(now_utc, last_reminded_utc, frequency)

    kind, n = _parse_frequency(frequency)
    print(f"frequency: {frequency} -> {kind} {n}")

    if kind == "HOURLY":
        interval = timedelta(hours=1) / n
        due = base + interval
        while due <= now_utc:
            due += interval
        return due

    if kind == "DAILY":
        interval = timedelta(days=1) / n
        due = base + interval
        while due <= now_utc:
            due += interval
        return due

    if kind == "EVERY_HOURS":
        interval = timedelta(hours=n)
        due = base + interval
        while due <= now_utc:
            due += interval
        return due

    if kind == "EVERY_DAYS":
        interval = timedelta(days=n)
        due = base + interval
        while due <= now_utc:
            due += interval
        return due

    if kind == "WEEKLY_N":
        interval = timedelta(days=7) / n
        due = base + interval
        while due <= now_utc:
            due += interval
        return due

    if kind == "WEEKLY":
        interval = timedelta(days=7)
        due = base + interval
        while due <= now_utc:
            due += interval
        return due

    if kind == "BIWEEKLY":
        interval = timedelta(days=14)
        due = base + interval
        while due <= now_utc:
            due += interval
        return due

    if kind == "MONTHLY_N_CAL":
        # interval depends on month; recompute as you advance
        due = base + _interval_for(base, frequency)
        while due <= now_utc:
            due = due + _interval_for(due, frequency)
        return due

    if kind == "MONTHLY":
        due = _add_months(base, 1)
        while due <= now_utc:
            due = _add_months(due, 1)
        return due

    if kind == "BIMONTHLY":
        due = _add_months(base, 2)
        while due <= now_utc:
            due = _add_months(due, 2)
        return due

    # fallback weekly
    interval = timedelta(days=7)
    due = base + interval
    while due <= now_utc:
        due += interval
    return due