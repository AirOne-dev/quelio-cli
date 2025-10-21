"""Time utilities for parsing and formatting work durations."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from .constants import WEEKDAY_FR


def hhmm_to_minutes(hhmm: str) -> int:
    """Convert HH:MM string to total minutes."""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def minutes_to_hhmm(total: int) -> str:
    """Convert a number of minutes to HH:MM string, keeping sign."""
    sign = "-" if total < 0 else ""
    total = abs(total)
    h = total // 60
    m = total % 60
    return f"{sign}{h:02d}:{m:02d}"


def day_total_from_points(points: List[str]) -> int:
    """Sum pairwise durations (in/out). Ignores a trailing unmatched punch."""
    mins = [hhmm_to_minutes(p) for p in points]
    total = 0
    for i in range(0, len(mins) - 1, 2):
        total += mins[i + 1] - mins[i]
    return total


def day_total_from_points_dynamic(points: List[str], now_min: int | None = None) -> int:
    """Compute total like `day_total_from_points`, but if an odd number of
    punches is present, extend the last one to current time (in minutes)."""
    mins = [hhmm_to_minutes(p) for p in points]
    total = 0
    for i in range(0, len(mins) - 1, 2):
        total += mins[i + 1] - mins[i]
    if len(mins) % 2 == 1:
        if now_min is None:
            now = datetime.now()
            now_min = now.hour * 60 + now.minute
        total += max(0, int(now_min) - mins[-1])
    return total


def format_week_summary(hours: Dict[str, List[str]]) -> List[Tuple[str, str, int]]:
    """Return [(date_key, weekday_label_fr, minutes_total), ...] sorted by date desc."""
    rows: List[Tuple[str, str, int]] = []
    for d, points in hours.items():
        # d is 'dd-mm-YYYY' or 'dd-mm-YY'
        try:
            dt = datetime.strptime(d, "%d-%m-%Y")
        except ValueError:
            dt = datetime.strptime(d, "%d-%m-%y")
        wd = WEEKDAY_FR[dt.weekday()]
        rows.append((d, wd, day_total_from_points(points)))
    rows.sort(key=lambda r: datetime.strptime(r[0], "%d-%m-%Y"), reverse=True)
    return rows


def current_week_dates() -> List[Tuple[str, str, datetime]]:
    """Return current week dates Monday..Sunday.
    Each entry: (date_key 'dd-mm-YYYY', weekday_label_fr, datetime).
    """
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    days: List[Tuple[str, str, datetime]] = []
    for i in range(7):
        d = monday + timedelta(days=i)
        key = d.strftime("%d-%m-%Y")
        wd = WEEKDAY_FR[d.weekday()]
        days.append((key, wd, d))
    return days

