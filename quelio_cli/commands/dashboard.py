"""`dashboard` command: interactive TUI using Textual and Rich."""

from __future__ import annotations

import math
import os
from datetime import datetime
from typing import Dict, List

# Rich/Textual are imported lazily inside `run()` to allow using
# non-TUI commands without these optional dependencies installed.

from ..api import BadgeApi
from ..config import Config
from ..constants import CONFIG_PATH, KEYRING_SERVICE, PAUSE_PAID_MINUTES
from ..utils_time import (
    current_week_dates,
    day_total_from_points,
    day_total_from_points_dynamic,
    hhmm_to_minutes,
    minutes_to_hhmm,
)


def _resolve_password(username: str, api_url: str) -> str:
    """Resolve password from keychain, env vars, or prompt interactively."""
    import getpass
    import sys
    import keyring

    key = f"{username}@{api_url}"
    pwd = None
    try:
        pwd = keyring.get_password(KEYRING_SERVICE, key)
    except Exception:
        pwd = None
    if not pwd:
        import os

        pwd = os.environ.get("BADGECLI_PASSWORD") or os.environ.get("BADGECLI_PWD")
    if not pwd:
        print("Mot de passe introuvable (keychain/env). Saisissez-le (non stocké):", file=sys.stderr)
        pwd = getpass.getpass("Mot de passe: ")
    return pwd


def run() -> None:
    # Lazy imports to avoid requiring Rich/Textual for non-TUI commands
    from rich.panel import Panel
    from rich.text import Text
    from textual.app import App, ComposeResult
    from textual.containers import Center, VerticalScroll
    from textual.reactive import reactive
    from textual.widgets import Static

    conf = Config.load()
    if not conf:
        print("Pas encore configuré. Lancez: quelio setup")
        raise SystemExit(1)

    pwd = _resolve_password(conf.username, conf.api_url)
    api = BadgeApi(conf.api_url, conf.username, pwd)

    class State:
        hours: Dict[str, List[str]] = {}
        total_effective: str = "--:--"
        total_paid: str = "--:--"

    def _day_paid_bonus(points: list[str], dt: datetime, now: datetime) -> int:
        """Return additional paid minutes for the given day.
        Business rule: +7 min at 10:30 and +7 min at 15:30 if the day has work.
        For past days, both bonuses are applied. For today, apply each bonus
        only once its time has passed. For future days, none.
        """
        # If no work that day, no bonus
        eff_static = day_total_from_points(points)
        if eff_static <= 0:
            return 0
        bonus = 0
        # Compare day with now to decide if break times have occurred
        if dt.date() < now.date():
            # Past day: both bonuses apply
            return PAUSE_PAID_MINUTES * 2
        if dt.date() > now.date():
            return 0
        # Today: check current time against 10:30 and 15:30
        if (now.hour, now.minute) >= (10, 30):
            bonus += PAUSE_PAID_MINUTES
        if (now.hour, now.minute) >= (15, 30):
            bonus += PAUSE_PAID_MINUTES
        return bonus

    class Totals(Static):
        total_effective = reactive("--:--")
        total_paid = reactive("--:--")
        weekly_minutes: int = 38 * 60

        def render(self):
            # Remaining time = weekly target - paid
            def to_min(txt: str) -> int | None:
                try:
                    h, m = txt.split(":")
                    return int(h) * 60 + int(m)
                except Exception:
                    return None

            paid_m = to_min(self.total_paid)
            remaining = None
            if paid_m is not None:
                remaining = int(self.weekly_minutes) - paid_m
                if remaining < 0:
                    remaining = 0

            remain_str = minutes_to_hhmm(remaining) if isinstance(remaining, int) else "--:--"

            body = (
                f"[b]Total effectif[/b]: [green]{self.total_effective}[/green]\n"
                f"[b]Total payé[/b]: [cyan]{self.total_paid}[/cyan]\n"
                f"[b]Temps restant[/b]: [red]{remain_str}[/red]"
            )
            return Panel(
                body,
                title="Ma semaine",
                border_style="#1F2937",
                padding=(0, 1),
                style="on #1F2937",
                expand=True,
            )

    class BreakLine(Static):
        def __init__(self, total_spaces: int) -> None:
            super().__init__()
            self.total_spaces = total_spaces

        def render(self):
            return Text("\n" * self.total_spaces)

    class CustomFooter(Static):
        def render(self):
            # Minimalistic help bar with app palette
            help_txt = Text()
            help_txt.append(" q ", style="bold #111827 on #9CA3AF")
            help_txt.append(" Quitter  ", style="#9CA3AF")
            help_txt.append(" r ", style="bold #111827 on #9CA3AF")
            help_txt.append(" Rafraîchir  ", style="#9CA3AF")
            help_txt.append(" d ", style="bold #111827 on #9CA3AF")
            help_txt.append(" Déconnexion  ", style="#9CA3AF")
            return help_txt

    class DayItem(Static):
        can_focus = True
        expanded = reactive(False)

        def __init__(self, title: str, points: list[str], total_str: str, date_key: str, is_today: bool) -> None:
            super().__init__()
            self.title = title
            self.points = points
            self.total_str = total_str
            self.date_key = date_key
            self.is_today = is_today
            self.empty = len(points) == 0
            try:
                if self.empty:
                    self.can_focus = False
            except Exception:
                pass

        def _timeline(self) -> Text:
            # Render a time bar from 08:00 to 18:00 with half-column precision
            start_day = 8 * 60
            end_day = 18 * 60
            width = 40

            def t_to_x2(hhmm: str) -> int:
                # position in half-columns [0, width*2]
                m = hhmm_to_minutes(hhmm)
                ratio = (m - start_day) / (end_day - start_day)
                x2 = int(ratio * (width * 2))
                return max(0, min(width * 2, x2))

            halves = [False] * (width * 2)
            for i in range(0, len(self.points) - 1, 2):
                s2 = t_to_x2(self.points[i])
                e2 = t_to_x2(self.points[i + 1])
                if e2 <= s2:
                    e2 = min(s2 + 1, width * 2)
                for h in range(s2, min(e2, width * 2)):
                    halves[h] = True
            # If last punch is open, extend to 'now' and store live segment indices
            live_range = None  # type: tuple[int, int] | None
            if len(self.points) % 2 == 1:
                now = datetime.now()
                now_hhmm = f"{now.hour:02d}:{now.minute:02d}"
                s2 = t_to_x2(self.points[-1])
                e2 = t_to_x2(now_hhmm)
                if e2 <= s2:
                    e2 = min(s2 + 1, width * 2)
                for h in range(s2, min(e2, width * 2)):
                    halves[h] = True
                live_range = (s2, min(e2, width * 2))

            text = Text()
            text.append(" ")  # left margin
            base_bg = (0x1F, 0x29, 0x37)
            base_purple = (0x7C, 0x3A, 0xED)
            for col in range(width):
                left = halves[col * 2]
                right = halves[col * 2 + 1]
                if left or right:
                    in_live = self.is_today and live_range is not None and (
                        (col * 2 >= live_range[0] and col * 2 < live_range[1]) or
                        (col * 2 + 1 >= live_range[0] and col * 2 + 1 < live_range[1])
                    )
                    if in_live:
                        tnow = datetime.now().timestamp()
                        period = 3.5
                        ph = (math.sin(tnow * math.tau / period) + 1) / 2
                        min_alpha = 0.35
                        alpha = min_alpha + (1.0 - min_alpha) * ph
                        r = int(base_bg[0] * (1 - alpha) + base_purple[0] * alpha)
                        g = int(base_bg[1] * (1 - alpha) + base_purple[1] * alpha)
                        b = int(base_bg[2] * (1 - alpha) + base_purple[2] * alpha)
                        style = f"#{r:02X}{g:02X}{b:02X}"
                    else:
                        style = "#7C3AED"
                    if left and right:
                        ch = "█"
                    elif left and not right:
                        ch = "▌"
                    elif right and not left:
                        ch = "▐"
                    else:
                        ch = " "
                else:
                    ch = "─"
                    style = "#4B5563"
                text.append(ch, style=style)
            return text

        def render(self):
            # Header line (chevron, day name, date, total)
            chev = ("▾" if self.expanded else "▸") if not self.empty else ""
            space = self.title.find(" ")
            if space != -1:
                day_name = self.title[:space]
                date_str = self.title[space + 1 :]
            else:
                day_name = self.title
                date_str = ""
            head = Text()
            if chev:
                head.append(f"{chev} ", style="#E5E7EB")
            else:
                head.append("  ")
            head.append(day_name, style="bold #E5E7EB")
            if date_str:
                head.append(f" {date_str}", style="#9CA3AF")
            head.append("  ")
            # Show dynamic total (accounts for an open interval)
            dyn_minutes = day_total_from_points_dynamic(self.points)
            head.append(minutes_to_hhmm(dyn_minutes), style="#9CA3AF")

            if not self.empty:
                head.append("\n")

            # Compose main body content
            body = Text.assemble(head)
            if not self.empty:
                timeline = self._timeline()
                ticks = Text("08  09  10  11  12  13  14  15  16  17  18", style="dim")
                body.append("\n")
                body.append(timeline)
                body.append("\n")
                body.append(ticks)

            # Expanded details
            if self.expanded and self.points:
                tbl = Text()
                tbl.append("\n\n")
                tbl.append(" Entrées/Sorties:\n\n", style="#9CA3AF")
                for i in range(0, len(self.points), 2):
                    if i + 1 < len(self.points):
                        a, b = self.points[i], self.points[i + 1]
                        tbl.append(f"  - {a}  →  {b}\n")
                    else:
                        a = self.points[i]
                        now = datetime.now()
                        now_str = f"{now.hour:02d}:{now.minute:02d}"
                        tbl.append(f"  - {a}  →  {now_str} (en cours)\n", style="#7C3AED")

                # dynamic day total if open interval
                mins = day_total_from_points_dynamic(self.points)
                tbl.append(f"\n Total: {minutes_to_hhmm(mins)}", style="#9CA3AF")
                body.append(tbl)

            # Wrap in a Panel to restore background for day sections
            return Panel(
                body,
                border_style="#1F2937",
                padding=(0, 1),
                style="on #1F2937",
                expand=True,
            )

        def on_click(self, event) -> None:
            if self.empty:
                return
            self.expanded = not self.expanded
            self.refresh(layout=True)

        def on_key(self, event) -> None:
            key = getattr(event, "key", "")
            if self.empty:
                return
            if key in ("enter", "space"):
                self.expanded = not self.expanded
                self.refresh(layout=True)
                try:
                    event.stop()
                except Exception:
                    pass

    class QuelioCLI(App):
        CSS = """
        Screen { layout: vertical; background: #111827; color: #E5E7EB; overflow-y: hidden }
        #totals { padding: 1 2; align-horizontal: center; max-width: 51; width: 100%; }
        #daylist { padding: 1 2; align-horizontal: center; max-width: 51; width: 100%; background: transparent; scrollbar-size-vertical: 1; scrollbar-size-horizontal: 1; }
        .day-card { padding: 0; border: none; background: transparent; margin: 0 0 1 0; }
        .empty-day { opacity: 0.5; }
        #footer { dock: bottom; padding: 1 2; color: #9CA3AF; }
        """

        BINDINGS = [
            ("q", "quit", "Quitter"),
            ("r", "refresh", "Rafraîchir"),
            ("d", "logout", "Déconnexion"),
            ("ctrl+q", "quit"),
            ("ctrl+c", "quit"),
            ("ctrl+r", "refresh"),
            ("ctrl+d", "logout"),
        ]

        def __init__(self):
            super().__init__()
            self.totals = Totals(id="totals")
            # Configure weekly target from saved config
            try:
                self.totals.weekly_minutes = int(getattr(conf, "weekly_hours", 38)) * 60
            except Exception:
                self.totals.weekly_minutes = 38 * 60
            self.list = VerticalScroll(id="daylist")

        def compose(self) -> ComposeResult:
            yield Center(self.totals)
            yield Center(self.list)
            yield CustomFooter(id="footer")

        def on_mount(self) -> None:
            self.refresh_data()
            try:
                self.set_interval(1.0, self._tick_update)
                self.set_interval(0.10, self._tick_visual)
            except Exception:
                pass

        def action_refresh(self) -> None:
            self.refresh_data()

        def action_quit(self) -> None:
            self.exit()

        def action_logout(self) -> None:
            # Delete credentials + config and exit
            try:
                keyring.delete_password(KEYRING_SERVICE, f"{conf.username}@{conf.api_url}")
            except Exception:
                pass
            try:
                os.remove(CONFIG_PATH)
            except Exception:
                pass
            self.exit(message="Déconnecté. Relancez `setup`.\n")

        def refresh_data(self) -> None:
            try:
                data = api.fetch()
            except Exception as e:
                self.bell()
                self.totals.update(f"Erreur de chargement: {e}")
                return

            State.hours = data.get("hours", {})
            State.total_effective = data.get("total_effective", "--:--")
            State.total_paid = data.get("total_paid", "--:--")

            # Instant dynamic calculation after first load
            self._update_totals_dynamic()

            # Rebuild list
            try:
                self.list.remove_children()
            except Exception:
                try:
                    for child in list(self.list.children):
                        try:
                            child.remove()
                        except Exception:
                            pass
                except Exception:
                    pass
            widgets: list[DayItem] = []
            for key, wd, dt in current_week_dates():
                points = [p.strip() for p in State.hours.get(key, [])]
                minutes_ = day_total_from_points(points)
                title = f"{wd.capitalize()} {dt.strftime('%d/%m/%Y')}"
                total_str = minutes_to_hhmm(minutes_)
                is_today = dt.date() == datetime.now().date()
                w = DayItem(title, points, total_str, key, is_today)
                w.add_class("day-card")
                if len(points) == 0:
                    w.add_class("empty-day")
                widgets.append(w)
            if widgets:
                self.list.mount(*widgets)
                self.list.mount(BreakLine(total_spaces=5))

        def _week_minutes_pair(self) -> tuple[int, int]:
            """Return (effective_minutes, paid_minutes) for the current week.
            Effective uses dynamic minutes for today and static for past days.
            Paid = effective + break bonuses (7' at 10:30, 7' at 15:30 when applicable).
            """
            eff_total = 0
            paid_total = 0
            now = datetime.now()
            for key, _wd, dt in current_week_dates():
                points = [p.strip() for p in State.hours.get(key, [])]
                if dt.date() == now.date():
                    eff_day = day_total_from_points_dynamic(points, now.hour * 60 + now.minute)
                else:
                    eff_day = day_total_from_points(points)
                bonus = _day_paid_bonus(points, dt, now)
                eff_total += eff_day
                paid_total += eff_day + bonus
            return eff_total, paid_total

        def _update_totals_dynamic(self) -> None:
            # Always compute current effective/paid with bonuses to match API
            eff_min, paid_min = self._week_minutes_pair()
            self.totals.total_effective = minutes_to_hhmm(eff_min)
            self.totals.total_paid = minutes_to_hhmm(paid_min)
            # If anything is open or today progresses, refresh visuals
            try:
                for child in list(self.list.children):
                    try:
                        if hasattr(child, "refresh"):
                            child.refresh()
                    except Exception:
                        pass
                self.list.refresh(layout=True)
            except Exception:
                pass

        def _tick_update(self) -> None:
            self._update_totals_dynamic()
            try:
                for child in list(self.list.children):
                    try:
                        if hasattr(child, "refresh"):
                            child.refresh()
                    except Exception:
                        pass
            except Exception:
                pass

        def _tick_visual(self) -> None:
            try:
                for child in list(self.list.children):
                    try:
                        if hasattr(child, "refresh"):
                            child.refresh()
                    except Exception:
                        pass
            except Exception:
                pass

    app = QuelioCLI()
    app.run()
