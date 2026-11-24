# main.py – مدیریت امور بازرگانی محسنی (نسخه چندکاربره)
# Flet 0.28.2  |  RTL Persian  |  Dark Neon Design  |  PostgreSQL
import flet as ft
import threading, time, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db
import jalali_utils as ju

# ═══════════════════════════════════════════════
#  DESIGN TOKENS
# ═══════════════════════════════════════════════
BG      = "#06060e"
BG_SB   = "#080812"
BG_CARD = "#0c0c1e"
BG_C2   = "#111128"
BG_IN   = "#0a0a1c"

C_CY  = "#00e5ff"
C_PU  = "#9d4edd"
C_GR  = "#00e676"
C_RE  = "#ff1744"
C_OR  = "#ff6d00"
C_YE  = "#ffd600"

C_TX  = "#e0e0f0"
C_TX2 = "#7070a0"
C_DIM = "#303055"
C_BRD = "#1a1a30"

SW = 220   # sidebar width


# ═══════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════

def glow(color, blur=16, spread=1):
    return ft.BoxShadow(blur_radius=blur, spread_radius=spread, color=color + "28")


def neon_card(content, color=C_CY, padding=20, radius=12, expand=False):
    return ft.Container(
        content=content, bgcolor=BG_CARD,
        border=ft.border.all(1, color), border_radius=radius,
        padding=padding, shadow=glow(color), expand=expand,
    )


def tag(text, color, bgcolor=None):
    bg = bgcolor or (color + "22")
    return ft.Container(
        content=ft.Text(text, size=10, color=color, weight=ft.FontWeight.W_500),
        bgcolor=bg, border=ft.border.all(1, color + "66"), border_radius=4,
        padding=ft.padding.symmetric(horizontal=7, vertical=2),
    )


def status_tag(status):
    m = {
        "در حال انجام":  (C_CY, BG_CARD),
        "پیگیری مستمر": (C_OR, BG_CARD),
        "تکمیل":         (C_GR, BG_CARD),
        "منتفی":         (C_DIM, BG_CARD),
    }
    c, bg = m.get(status, (C_TX2, BG_CARD))
    return tag(status, c)


def progress_bar(val, color=C_GR):
    pct = int(val * 100)
    return ft.Row([
        ft.ProgressBar(value=val, color=color, bgcolor=C_DIM, width=90, height=5, border_radius=4),
        ft.Text(f"{pct}%", size=10, color=color),
    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def section_header(title, color=C_CY, icon=None):
    controls = []
    if icon:
        controls.append(ft.Icon(icon, color=color, size=18))
    controls.append(ft.Text(title, color=color, size=15, weight=ft.FontWeight.BOLD))
    return ft.Row(controls, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def neon_btn(text, on_click, color=C_CY, icon=None):
    row = []
    if icon:
        row.append(ft.Icon(icon, size=16, color=BG))
    row.append(ft.Text(text, color=BG, size=13, weight=ft.FontWeight.W_600))
    return ft.Container(
        content=ft.Row(row, spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=color, border_radius=8,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        on_click=on_click, shadow=glow(color, 12),
        animate=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
    )


def ghost_btn(text, on_click, color=C_CY, icon=None):
    row = []
    if icon:
        row.append(ft.Icon(icon, size=15, color=color))
    row.append(ft.Text(text, color=color, size=12))
    return ft.Container(
        content=ft.Row(row, spacing=5, alignment=ft.MainAxisAlignment.CENTER),
        border=ft.border.all(1, color + "88"), border_radius=7,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        on_click=on_click, bgcolor=color + "11",
    )


# ═══════════════════════════════════════════════
#  LOGIN PAGE
# ═══════════════════════════════════════════════

class LoginPage:
    def __init__(self, page: ft.Page, on_login):
        self.page = page
        self.on_login = on_login
        self._build()

    def _build(self):
        username_f = ft.TextField(
            label="نام کاربری", hint_text="admin",
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
            color=C_TX, border_radius=8, label_style=ft.TextStyle(color=C_TX2),
            text_size=13, width=300, text_align=ft.TextAlign.CENTER,
            prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
        )
        password_f = ft.TextField(
            label="رمز عبور", hint_text="رمز عبور خود را وارد کنید",
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
            color=C_TX, border_radius=8, label_style=ft.TextStyle(color=C_TX2),
            text_size=13, width=300, password=True, can_reveal_password=True,
            text_align=ft.TextAlign.CENTER,
            prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
        )
        error_txt = ft.Text("", color=C_RE, size=12, text_align=ft.TextAlign.CENTER)

        def do_login(e):
            user = db.authenticate_user(username_f.value.strip(), password_f.value)
            if user:
                error_txt.value = ""
                self.on_login(user)
            else:
                error_txt.value = "نام کاربری یا رمز عبور اشتباه است"
                self.page.update()

        def on_key(e):
            if e.key == "Enter":
                do_login(e)

        login_btn = neon_btn("ورود", do_login, C_CY, ft.Icons.LOGIN_ROUNDED)

        self.page.on_keyboard_event = on_key

        self.page.controls.clear()
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Container(content=ft.Text("⚡", size=40), alignment=ft.alignment.center),
                            ft.Text("مدیریت امور", color=C_CY, size=24, weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Text("بازرگانی محسنی", color=C_TX2, size=13,
                                    text_align=ft.TextAlign.CENTER),
                        ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.only(bottom=30),
                    ),
                    username_f,
                    password_f,
                    ft.Container(height=8),
                    error_txt,
                    ft.Container(height=12),
                    login_btn,
                    ft.Container(height=20),
                    ft.Text("ورود به سیستم مدیریت امور", color=C_DIM, size=10,
                            text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                alignment=ft.alignment.center,
                expand=True, bgcolor=BG,
            )
        )
        self.page.update()


# ═══════════════════════════════════════════════
#  MAIN APP CLASS
# ═══════════════════════════════════════════════

class TaskManagerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_view = "dashboard"
        self.alarm_running = False
        self.current_user = None
        self._setup_page()
        db.init_db()
        self._show_login()

    def _setup_page(self):
        p = self.page
        p.title = "مدیریت امور – بازرگانی محسنی"
        p.bgcolor = BG
        p.rtl = True
        p.theme_mode = ft.ThemeMode.DARK
        p.padding = 0

    def _show_login(self):
        LoginPage(self.page, self._on_login)

    def _on_login(self, user):
        self.current_user = user
        self.page.on_keyboard_event = None
        self.page.controls.clear()
        self._build()

    def _logout(self, e):
        self.current_user = None
        self.alarm_running = False
        self.page.controls.clear()
        self._show_login()

    def _build(self):
        self._alarm_badge_txt = ft.Text("0", size=9, color=BG, weight=ft.FontWeight.BOLD)
        self._alarm_badge = ft.Container(
            content=self._alarm_badge_txt, bgcolor=C_RE, border_radius=9,
            padding=ft.padding.symmetric(horizontal=4, vertical=1), visible=False,
        )
        self._content = ft.Container(
            content=self._dash_view(), expand=True, bgcolor=BG,
            padding=ft.padding.only(left=24, right=24, top=20, bottom=16),
        )
        self.page.add(ft.Row([self._sidebar(), self._content], expand=True, spacing=0))
        self._refresh_alarm_badge()
        self._start_alarm_thread()

    # ── SIDEBAR ──────────────────────────────────

    def _sidebar(self):
        user = self.current_user
        role = user.get("role", "user")
        full_name = user.get("full_name") or user.get("username", "")

        nav_items = [
            ("dashboard", ft.Icons.DASHBOARD_ROUNDED, "داشبورد", True),
            ("tasks", ft.Icons.ASSIGNMENT_ROUNDED, "کارها", True),
            ("kanban", ft.Icons.VIEW_WEEK_ROUNDED, "کانبان", True),
            ("personnel", ft.Icons.PEOPLE_ROUNDED, "پرسنل", role == "admin"),
            ("sections", ft.Icons.BUSINESS_ROUNDED, "بخش‌ها", role == "admin"),
            ("users", ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED, "کاربران", role == "admin"),
            ("chat", ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED, "چت بخش", True),
            ("daily_report", ft.Icons.TASK_ALT_ROUNDED, "گزارش روزانه", True),
            ("alarms", ft.Icons.NOTIFICATIONS_ROUNDED, "آلارم‌ها", True),
            ("notes", ft.Icons.STICKY_NOTE_2_ROUNDED, "یادداشت‌ها", True),
        ]

        self._nav_btns = {}
        col = ft.Column(spacing=2)
        for vid, icon, label, visible in nav_items:
            if not visible:
                continue
            btn = self._nav_btn(vid, icon, label)
            self._nav_btns[vid] = btn
            col.controls.append(btn)

        # اطلاعات کاربر
        role_labels = {"admin": "ادمین", "manager": "مدیر", "user": "کاربر"}
        user_card = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(full_name[0] if full_name else "?", color=BG, size=14,
                                    weight=ft.FontWeight.BOLD),
                    bgcolor=C_PU, width=32, height=32, border_radius=16,
                    alignment=ft.alignment.center,
                ),
                ft.Text(full_name[:15], color=C_TX, size=11, weight=ft.FontWeight.W_500,
                        text_align=ft.TextAlign.CENTER),
                ft.Text(role_labels.get(role, role), color=C_CY, size=9,
                        text_align=ft.TextAlign.CENTER),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=8),
        )

        logo = ft.Container(
            content=ft.Column([
                ft.Container(content=ft.Text("⚡", size=30), alignment=ft.alignment.center),
                ft.Text("مدیریت امور", color=C_CY, size=15, weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("بازرگانی محسنی", color=C_TX2, size=10,
                        text_align=ft.TextAlign.CENTER),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=20), width=SW,
        )

        line = ft.Container(
            height=1, bgcolor=C_CY + "44",
            shadow=ft.BoxShadow(blur_radius=6, color=C_CY),
            margin=ft.margin.only(left=16, right=16, bottom=8),
        )

        logout_btn = ghost_btn("خروج", self._logout, C_RE, ft.Icons.LOGOUT_ROUNDED)

        jy, jm, jd = ju.today_j()
        today_lbl = ft.Container(
            content=ft.Text(ju.fmt_fa(jy, jm, jd), color=C_TX2, size=10,
                            text_align=ft.TextAlign.CENTER),
            padding=ft.padding.symmetric(vertical=8), width=SW,
            alignment=ft.alignment.center,
        )

        return ft.Container(
            content=ft.Column([
                logo, line, col, ft.Container(expand=True),
                user_card, logout_btn, today_lbl
            ], spacing=0),
            width=SW, bgcolor=BG_SB,
            border=ft.border.only(right=ft.BorderSide(1, C_BRD)),
        )

    def _nav_btn(self, vid, icon, label):
        active = vid == self.current_view

        def click(e, v=vid):
            self._go(v)

        row_ctrls = [
            ft.Icon(icon, color=C_CY if active else C_TX2, size=18),
            ft.Text(label, color=C_CY if active else C_TX2, size=12,
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.NORMAL),
        ]
        if vid == "alarms":
            row_ctrls.append(self._alarm_badge)

        return ft.Container(
            content=ft.Row(row_ctrls, spacing=10,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=14, vertical=11),
            border=ft.border.only(left=ft.BorderSide(3, C_CY if active else "transparent")),
            bgcolor=BG_C2 if active else "transparent",
            on_click=click,
            border_radius=ft.border_radius.only(top_right=8, bottom_right=8),
            width=SW, animate=ft.Animation(120),
        )

    def _go(self, vid):
        if vid == self.current_view:
            self._refresh_view()
            return
        self.current_view = vid
        for v, btn in self._nav_btns.items():
            active = v == vid
            row = btn.content
            row.controls[0].color = C_CY if active else C_TX2
            row.controls[1].color = C_CY if active else C_TX2
            row.controls[1].weight = ft.FontWeight.W_600 if active else ft.FontWeight.NORMAL
            btn.border = ft.border.only(left=ft.BorderSide(3, C_CY if active else "transparent"))
            btn.bgcolor = BG_C2 if active else "transparent"
        self._refresh_view()

    def _refresh_view(self):
        builders = {
            "dashboard": self._dash_view, "tasks": self._tasks_view,
            "kanban": self._kanban_view, "personnel": self._personnel_view,
            "sections": self._sections_view, "users": self._users_view,
            "chat": self._chat_view, "daily_report": self._daily_report_view,
            "alarms": self._alarms_view, "notes": self._notes_view,
        }
        if self.current_view in builders:
            self._content.content = builders[self.current_view]()
        self.page.update()

    def _snack(self, msg, color=C_CY):
        self.page.open(ft.SnackBar(
            content=ft.Text(msg, color=BG, weight=ft.FontWeight.W_500),
            bgcolor=color, duration=3000,
        ))

    def _refresh_alarm_badge(self):
        uid = self.current_user["id"] if self.current_user else None
        n = db.unread_count(uid)
        self._alarm_badge.visible = n > 0
        self._alarm_badge_txt.value = str(n)
        try:
            self.page.update()
        except Exception:
            pass

    # ── DASHBOARD ────────────────────────────────

    def _dash_view(self):
        user = self.current_user
        role = user.get("role", "user")
        section_id = user.get("section_id")
        username = user.get("full_name") or user.get("username", "")

        stats = db.get_task_stats(user_role=role, user_section=section_id, user_name=username)
        overdue = db.get_overdue_tasks(10, user_role=role, user_section=section_id, user_name=username)
        upcoming = db.get_upcoming_tasks(7, 10, user_role=role, user_section=section_id, user_name=username)

        def stat_card(title, val, color, icon):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=ft.Icon(icon, color=color, size=22),
                                     bgcolor=color + "22", border_radius=8, padding=8),
                        ft.Text(str(val), size=38, color=color, weight=ft.FontWeight.BOLD),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(height=6),
                    ft.Text(title, color=C_TX2, size=12),
                    ft.Container(content=ft.Container(height=2, bgcolor=color, border_radius=1,
                                 shadow=ft.BoxShadow(blur_radius=6, color=color)),
                                 margin=ft.margin.only(top=8)),
                ], spacing=0),
                bgcolor=BG_CARD, border=ft.border.all(1, color + "66"),
                border_radius=12, padding=18, expand=True, shadow=glow(color, 20, 1),
            )

        total = stats["total"]
        active = stats["active"]
        completed = stats["completed"]
        cancelled = stats["cancelled"]

        def pie_segment(pct, color, label, count):
            return ft.Row([
                ft.Container(width=int(pct * 120) + 4, height=14, bgcolor=color, border_radius=3,
                             shadow=ft.BoxShadow(blur_radius=8, color=color)),
                ft.Text(f"{label} ({count})", color=color, size=12),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        pct_a = active / total if total else 0
        pct_c = completed / total if total else 0
        pct_x = cancelled / total if total else 0

        person_rows = []
        for p in stats.get("personnel", [])[:8]:
            tot = p["total"] or 1
            act = p["active"]
            com = p["completed"]
            person_rows.append(ft.Row([
                ft.Text((p["assigned_to"] or "")[:10], color=C_TX, size=12, width=90),
                ft.Stack([
                    ft.Container(width=130, height=10, bgcolor=C_DIM, border_radius=4),
                    ft.Container(width=int(130 * com / tot), height=10, bgcolor=C_GR,
                                 border_radius=4),
                    ft.Container(width=int(130 * act / tot), height=10, bgcolor=C_CY,
                                 border_radius=4,
                                 margin=ft.margin.only(left=int(130 * com / tot))),
                ]),
                ft.Text(f"{p['total']}", color=C_TX2, size=11, width=20),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER))

        od_items = []
        for t in overdue[:6]:
            d = t.get("_days", 0)
            od_items.append(ft.Container(
                content=ft.Row([
                    ft.Container(width=3, height=32, bgcolor=C_RE, border_radius=2),
                    ft.Column([
                        ft.Text(t["title"][:40], color=C_TX, size=12),
                        ft.Text(f"{abs(d)} روز عقب | {t['assigned_to'] or '—'}", color=C_RE,
                                size=10),
                    ], spacing=1, expand=True),
                    ft.Container(content=ft.Text(f"{d}d", color=BG, size=9), bgcolor=C_RE,
                                 border_radius=4, padding=3),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=C_RE + "11", border_radius=6, padding=8,
            ))

        up_items = []
        for t in upcoming[:6]:
            d = t.get("_days", 0)
            color = ju.dl_color(d)
            up_items.append(ft.Container(
                content=ft.Row([
                    ft.Container(width=3, height=32, bgcolor=color, border_radius=2),
                    ft.Column([
                        ft.Text(t["title"][:38], color=C_TX, size=12),
                        ft.Text(ju.dl_label(d) + f" | {t['assigned_to'] or '—'}", color=color,
                                size=10),
                    ], spacing=1, expand=True),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=color + "11", border_radius=6, padding=8,
            ))

        return ft.Column([
            ft.Row([
                ft.Text("داشبورد", color=C_TX, size=22, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Row([ft.Icon(ft.Icons.CIRCLE, size=8, color=C_GR),
                                     ft.Text(ju.fmt_fa(*ju.today_j()), color=C_TX2, size=12)],
                                   spacing=6),
                    bgcolor=BG_C2, border_radius=20,
                    padding=ft.padding.symmetric(horizontal=12, vertical=5),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=16),
            ft.Row([
                stat_card("کل کارها", total, C_CY, ft.Icons.LIST_ALT_ROUNDED),
                stat_card("در حال انجام", active, C_OR, ft.Icons.PENDING_ACTIONS),
                stat_card("تکمیل شده", completed, C_GR, ft.Icons.CHECK_CIRCLE_OUTLINE),
                stat_card("منتفی", cancelled, C_DIM, ft.Icons.CANCEL_OUTLINED),
            ], spacing=14),
            ft.Container(height=16),
            ft.Row([
                neon_card(ft.Column([
                    section_header("کارهای پرسنل", C_PU, ft.Icons.PEOPLE_OUTLINE_ROUNDED),
                    ft.Container(height=8),
                    ft.Row([
                        ft.Container(width=12, height=8, bgcolor=C_GR, border_radius=2),
                        ft.Text("تکمیل", color=C_TX2, size=10),
                        ft.Container(width=12, height=8, bgcolor=C_CY, border_radius=2),
                        ft.Text("در حال انجام", color=C_TX2, size=10),
                    ], spacing=6),
                    ft.Container(height=8),
                    ft.Column(person_rows if person_rows else [
                        ft.Text("هنوز پرسنلی با کار ثبت‌شده وجود ندارد", color=C_TX2, size=12)
                    ], spacing=10),
                ]), color=C_PU, expand=True, padding=18),
                ft.Container(width=14),
                neon_card(ft.Column([
                    section_header("توزیع وضعیت", C_CY, ft.Icons.PIE_CHART_OUTLINE_ROUNDED),
                    ft.Container(height=12),
                    ft.Column([
                        pie_segment(pct_a, C_CY, "در حال انجام", active),
                        pie_segment(pct_c, C_GR, "تکمیل شده", completed),
                        pie_segment(pct_x, C_DIM, "منتفی", cancelled),
                    ], spacing=10),
                    ft.Container(height=12),
                    ft.Container(
                        content=ft.Row([ft.Text("تکمیل:", color=C_GR, size=12),
                                         ft.Text(f"{int(pct_c * 100)}%" if total else "0%",
                                                 color=C_GR, size=18,
                                                 weight=ft.FontWeight.BOLD)],
                                        spacing=8,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=C_GR + "11", border_radius=8, padding=12,
                        border=ft.border.all(1, C_GR + "44"),
                    ),
                ]), color=C_CY, expand=True, padding=18),
            ]),
            ft.Container(height=14),
            ft.Row([
                neon_card(ft.Column([
                    section_header("کارهای عقب‌افتاده", C_RE, ft.Icons.WARNING_ROUNDED),
                    ft.Container(height=8),
                    ft.Column(od_items if od_items else [
                        ft.Text("هیچ کاری عقب نیفتاده!", color=C_GR, size=12)
                    ], spacing=6),
                ]), color=C_RE, expand=True, padding=16),
                ft.Container(width=14),
                neon_card(ft.Column([
                    section_header("موعد نزدیک (۷ روز)", C_YE, ft.Icons.UPCOMING_ROUNDED),
                    ft.Container(height=8),
                    ft.Column(up_items if up_items else [
                        ft.Text("هیچ کاری در ۷ روز آینده سررسید نمی‌شود", color=C_TX2, size=12)
                    ], spacing=6),
                ]), color=C_YE, expand=True, padding=16),
            ]),
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

    # ── TASKS VIEW ───────────────────────────────

    def _tasks_view(self, filters=None):
        self._task_filters = filters or {}
        user = self.current_user
        role = user.get("role", "user")
        section_id = user.get("section_id")
        username = user.get("full_name") or user.get("username", "")

        tasks = db.get_all_tasks(filters, user_role=role, user_section=section_id, user_name=username)
        total = len(tasks)
        personnel = [p["name"] for p in db.get_all_personnel()]
        sections = db.get_sections()

        search_field = ft.TextField(
            hint_text="جستجو در عنوان / توضیحات...",
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
            color=C_TX, hint_style=ft.TextStyle(color=C_TX2),
            border_radius=8, expand=True,
            content_padding=ft.padding.symmetric(horizontal=14, vertical=8), text_size=13,
            on_change=lambda e: self._apply_task_filters(
                search=e.control.value, assigned=assign_dd.value,
                status=status_dd.value, priority=prior_dd.value),
        )
        assign_dd = ft.Dropdown(
            options=[ft.dropdown.Option("همه")] + [ft.dropdown.Option(p) for p in personnel],
            value="همه", bgcolor=BG_IN, border_color=C_BRD, color=C_TX,
            focused_border_color=C_CY, border_radius=8, width=140,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=6), text_size=12,
            on_change=lambda e: self._apply_task_filters(
                search=search_field.value, assigned=e.control.value,
                status=status_dd.value, priority=prior_dd.value),
        )
        status_dd = ft.Dropdown(
            options=[ft.dropdown.Option(s) for s in
                     ["همه", "در حال انجام", "پیگیری مستمر", "تکمیل", "منتفی"]],
            value="همه", bgcolor=BG_IN, border_color=C_BRD, color=C_TX,
            focused_border_color=C_CY, border_radius=8, width=140,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=6), text_size=12,
            on_change=lambda e: self._apply_task_filters(
                search=search_field.value, assigned=assign_dd.value,
                status=e.control.value, priority=prior_dd.value),
        )
        prior_dd = ft.Dropdown(
            options=[ft.dropdown.Option(s) for s in ["همه", "مهم", "غیر مهم"]],
            value="همه", bgcolor=BG_IN, border_color=C_BRD, color=C_TX,
            focused_border_color=C_CY, border_radius=8, width=120,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=6), text_size=12,
            on_change=lambda e: self._apply_task_filters(
                search=search_field.value, assigned=assign_dd.value,
                status=status_dd.value, priority=e.control.value),
        )
        filter_row = ft.Row([
            search_field,
            ft.Container(content=ft.Row([
                ft.Text("مسئول:", color=C_TX2, size=11), assign_dd,
                ft.Text("وضعیت:", color=C_TX2, size=11), status_dd,
                ft.Text("اولویت:", color=C_TX2, size=11), prior_dd,
            ], spacing=8)),
        ], spacing=12)

        rows = [self._task_row(t) for t in tasks]
        task_list = ft.Column(rows if rows else [
            ft.Container(content=ft.Text("هنوز کاری ثبت نشده",
                                         color=C_TX2, size=12,
                                         text_align=ft.TextAlign.CENTER),
                         alignment=ft.alignment.center, padding=30)
        ], spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

        can_add = role in ("admin", "manager")
        add_btn = neon_btn("+ افزودن کار", lambda e: self._show_task_form(), C_CY,
                           ft.Icons.ADD_ROUNDED) if can_add else ft.Container()

        return ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("مدیریت کارها", color=C_TX, size=22, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{total} کار", color=C_TX2, size=12),
                ], spacing=2),
                add_btn,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=14),
            neon_card(filter_row, color=C_BRD, padding=14),
            ft.Container(height=12),
            ft.Container(
                content=ft.Row([
                    ft.Text("عنوان کار", color=C_TX2, size=11, weight=ft.FontWeight.W_500,
                            expand=4),
                    ft.Text("مسئول", color=C_TX2, size=11, expand=2),
                    ft.Text("وضعیت", color=C_TX2, size=11, expand=2),
                    ft.Text("پیشرفت", color=C_TX2, size=11, expand=2),
                    ft.Text("موعد تحویل", color=C_TX2, size=11, expand=2),
                    ft.Text("اقدامات", color=C_TX2, size=11, expand=2),
                ], spacing=0),
                padding=ft.padding.symmetric(horizontal=16, vertical=6),
                bgcolor=BG_C2,
                border_radius=ft.border_radius.only(top_left=8, top_right=8),
            ),
            task_list,
        ], expand=True, spacing=0)

    def _task_row(self, t):
        status = t.get("status", "در حال انجام")
        progress = t.get("progress", 0.0)
        deadline = t.get("deadline", "")
        days = ju.days_left(deadline)
        dl_color = ju.dl_color(days)
        pmap = {"مهم": C_RE, "غیر مهم": C_TX2}
        p_color = pmap.get(t.get("priority", ""), C_TX2)
        parsed_dl = ju.parse_date(deadline)

        user = self.current_user
        can_edit = user.get("role") in ("admin", "manager")

        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(width=4, height=28, bgcolor=p_color, border_radius=2),
                    ft.Column([
                        ft.Text(t["title"][:42], color=C_TX, size=12,
                                weight=ft.FontWeight.W_500),
                        ft.Text(t.get("requester", "")[:20], color=C_TX2, size=10),
                    ], spacing=1, expand=True),
                ], spacing=8, expand=4),
                ft.Text((t.get("assigned_to", "") or "—")[:10], color=C_CY, size=12,
                        expand=2),
                ft.Container(content=status_tag(status), expand=2),
                ft.Container(content=progress_bar(progress), expand=2),
                ft.Container(content=ft.Column([
                    ft.Text(ju.fmt_j(*parsed_dl) if parsed_dl else "—", color=dl_color,
                            size=11),
                    ft.Text(ju.dl_label(days), color=dl_color, size=9),
                ], spacing=0), expand=2),
                ft.Row([
                    ft.IconButton(ft.Icons.EDIT_ROUNDED, icon_color=C_CY, icon_size=16,
                                  tooltip="ویرایش",
                                  on_click=lambda e, tid=t["id"]: self._show_task_form(tid),
                                  visible=can_edit),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE_ROUNDED, icon_color=C_RE,
                                  icon_size=16, tooltip="حذف",
                                  on_click=lambda e, tid=t["id"]: self._confirm_delete(tid),
                                  visible=can_edit),
                ], spacing=0, expand=2),
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=BG_C2 if days is not None and days < 0 else BG_CARD,
            border=ft.border.only(
                bottom=ft.BorderSide(1, C_BRD),
                left=ft.BorderSide(2, dl_color if days is not None and days <= 3 else "transparent")),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        )

    def _apply_task_filters(self, search="", assigned="همه", status="همه", priority="همه"):
        f = {}
        if search:
            f["search"] = search
        if assigned and assigned != "همه":
            f["assigned_to"] = assigned
        if status and status != "همه":
            f["status"] = status
        if priority and priority != "همه":
            f["priority"] = priority
        self._content.content = self._tasks_view(f)
        self.page.update()

    def _confirm_delete(self, task_id):
        task = db.get_task(task_id)
        if not task:
            return

        def do_delete(e):
            db.delete_task(task_id)
            self._close_dlg(dlg)
            self._go("tasks")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("حذف کار", color=C_RE, weight=ft.FontWeight.BOLD),
            content=ft.Text(f'آیا از حذف "{task["title"][:40]}" مطمئن هستید؟',
                            color=C_TX),
            actions=[ghost_btn("لغو", lambda e: self._close_dlg(dlg), C_TX2),
                     neon_btn("حذف", do_delete, C_RE)],
            bgcolor=BG_CARD, shape=ft.RoundedRectangleBorder(radius=12),
        )
        self.page.open(dlg)

    def _close_dlg(self, dlg):
        dlg.open = False
        self.page.update()

    # ── TASK FORM ────────────────────────────────

    def _show_task_form(self, task_id=None):
        task = db.get_task(task_id) if task_id else {}
        personnel = [p["name"] for p in db.get_all_personnel()]
        sections = db.get_sections()
        is_edit = bool(task)

        title_f = ft.TextField(value=task.get("title", ""), label="عنوان کار *",
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY, color=C_TX,
            border_radius=8, label_style=ft.TextStyle(color=C_TX2), text_size=13)
        req_f = ft.TextField(value=task.get("requester", ""), label="واحد مرجع",
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY, color=C_TX,
            border_radius=8, label_style=ft.TextStyle(color=C_TX2), text_size=13)
        notes_f = ft.TextField(value=task.get("notes", ""), label="توضیحات",
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY, color=C_TX,
            border_radius=8, label_style=ft.TextStyle(color=C_TX2),
            multiline=True, min_lines=2, max_lines=4, text_size=13)
        today_f = ft.TextField(value=task.get("today_task", ""), label="کار امروز",
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY, color=C_TX,
            border_radius=8, label_style=ft.TextStyle(color=C_TX2), text_size=13)
        deadline_f = ft.TextField(value=task.get("deadline", ""),
            label="تاریخ تحویل (مثال: 14040915)",
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY, color=C_TX,
            border_radius=8, label_style=ft.TextStyle(color=C_TX2), text_size=13)

        assign_dd = ft.Dropdown(
            label="مسئول انجام",
            options=[ft.dropdown.Option("")] + [ft.dropdown.Option(p) for p in personnel],
            value=task.get("assigned_to", ""),
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
            color=C_TX, border_radius=8, label_style=ft.TextStyle(color=C_TX2),
            text_size=13, expand=True,
        )
        collab_dd = ft.Dropdown(
            label="نیاز به همکاری",
            options=[ft.dropdown.Option("")] + [ft.dropdown.Option(p) for p in personnel],
            value=task.get("collaborator", ""),
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
            color=C_TX, border_radius=8, label_style=ft.TextStyle(color=C_TX2),
            text_size=13,
        )
        section_dd = ft.Dropdown(
            label="بخش",
            options=[ft.dropdown.Option("")] + [ft.dropdown.Option(s["name"]) for s in sections],
            value="",
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
            color=C_TX, border_radius=8, label_style=ft.TextStyle(color=C_TX2),
            text_size=13,
        )
        prior_dd = ft.Dropdown(
            label="اولویت",
            options=[ft.dropdown.Option(o) for o in ["مهم", "غیر مهم"]],
            value=task.get("priority", "مهم"),
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
            color=C_TX, border_radius=8, label_style=ft.TextStyle(color=C_TX2),
            text_size=13,
        )
        urg_dd = ft.Dropdown(
            label="فوریت",
            options=[ft.dropdown.Option(o) for o in ["فوری", "غیر فوری"]],
            value=task.get("urgency", "غیر فوری"),
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
            color=C_TX, border_radius=8, label_style=ft.TextStyle(color=C_TX2),
            text_size=13,
        )
        status_dd = ft.Dropdown(
            label="وضعیت",
            options=[ft.dropdown.Option(o) for o in
                     ["در حال انجام", "پیگیری مستمر", "تکمیل", "منتفی"]],
            value=task.get("status", "در حال انجام"),
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
            color=C_TX, border_radius=8, label_style=ft.TextStyle(color=C_TX2),
            text_size=13,
        )
        level_dd = ft.Dropdown(
            label="سطح کار",
            options=[ft.dropdown.Option(str(i)) for i in [1, 2, 3, 4]],
            value=str(task.get("level", 3)),
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
            color=C_TX, border_radius=8, label_style=ft.TextStyle(color=C_TX2),
            text_size=13,
        )
        prog_slider = ft.Slider(min=0, max=1, divisions=10,
                                 value=task.get("progress", 0.0),
                                 active_color=C_GR, thumb_color=C_GR, label="{value}")

        def save(e):
            if not title_f.value.strip():
                title_f.border_color = C_RE
                self.page.update()
                return

            section_id = None
            if section_dd.value:
                for s in sections:
                    if s["name"] == section_dd.value:
                        section_id = s["id"]
                        break

            data = {
                "title": title_f.value.strip(), "requester": req_f.value,
                "assigned_to": assign_dd.value or "",
                "collaborator": collab_dd.value or "",
                "section_id": section_id,
                "priority": prior_dd.value, "urgency": urg_dd.value,
                "status": status_dd.value,
                "level": int(level_dd.value),
                "progress": float(prog_slider.value),
                "deadline": deadline_f.value, "notes": notes_f.value,
                "today_task": today_f.value,
            }
            if is_edit:
                db.update_task(task_id, data)
                self._snack("کار ویرایش شد", C_GR)
            else:
                db.add_task(data)
                self._snack("کار جدید اضافه شد", C_GR)
            self._close_dlg(dlg)
            self._go("tasks")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.EDIT_ROUNDED if is_edit else ft.Icons.ADD_ROUNDED,
                        color=C_CY),
                ft.Text("ویرایش کار" if is_edit else "افزودن کار جدید", color=C_CY,
                        weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    title_f,
                    ft.Row([req_f, deadline_f], spacing=12),
                    ft.Row([assign_dd, collab_dd], spacing=12),
                    ft.Row([section_dd, prior_dd], spacing=12),
                    ft.Row([urg_dd, status_dd, level_dd], spacing=10),
                    ft.Column([ft.Text("میزان پیشرفت", color=C_TX2, size=11),
                               prog_slider], spacing=4),
                    today_f, notes_f,
                ], spacing=12, scroll=ft.ScrollMode.AUTO, width=580),
                bgcolor=BG_CARD, padding=4,
            ),
            actions=[ghost_btn("لغو", lambda e: self._close_dlg(dlg), C_TX2),
                     neon_btn("ذخیره", save, C_CY, ft.Icons.SAVE_ROUNDED)],
            bgcolor=BG_CARD, shape=ft.RoundedRectangleBorder(radius=14),
        )
        self.page.open(dlg)

    # ── KANBAN VIEW ──────────────────────────────

    def _kanban_view(self):
        user = self.current_user
        role = user.get("role", "user")
        section_id = user.get("section_id")
        username = user.get("full_name") or user.get("username", "")

        tasks = db.get_all_tasks(user_role=role, user_section=section_id, user_name=username)
        cols = [
            ("در حال انجام", C_CY, ft.Icons.PENDING_ACTIONS),
            ("پیگیری مستمر", C_OR, ft.Icons.LOOP_ROUNDED),
            ("تکمیل", C_GR, ft.Icons.CHECK_CIRCLE_OUTLINE),
            ("منتفی", C_DIM, ft.Icons.CANCEL_OUTLINED),
        ]

        def kanban_card(t):
            days = ju.days_left(t.get("deadline", ""))
            dl_c = ju.dl_color(days)
            return ft.Container(
                content=ft.Column([
                    ft.Text(t["title"][:38], color=C_TX, size=12,
                            weight=ft.FontWeight.W_500),
                    ft.Container(height=4),
                    ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINE_ROUNDED, color=C_TX2, size=12),
                            ft.Text((t.get("assigned_to", "") or "—")[:12], color=C_TX2,
                                    size=10)], spacing=4),
                    ft.Container(height=4),
                    progress_bar(t.get("progress", 0), C_GR),
                    ft.Container(height=6),
                    ft.Row([
                        ft.Container(content=ft.Text(ju.dl_label(days), color=dl_c, size=9),
                                     bgcolor=dl_c + "22", border_radius=4,
                                     padding=ft.padding.symmetric(horizontal=6, vertical=2)),
                        ft.Container(expand=True),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ], spacing=0),
                bgcolor=BG_C2, border=ft.border.all(1, C_BRD), border_radius=10,
                padding=12,
                shadow=ft.BoxShadow(blur_radius=4, color=C_BRD),
            )

        def kanban_col(status, color, icon):
            col_tasks = [t for t in tasks if t.get("status") == status]
            cards = [kanban_card(t) for t in col_tasks]
            return ft.Container(
                content=ft.Column([
                    ft.Container(content=ft.Row([
                        ft.Icon(icon, color=color, size=16),
                        ft.Text(status, color=color, size=13,
                                weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                        ft.Container(content=ft.Text(str(len(col_tasks)), color=BG,
                                                     size=10, weight=ft.FontWeight.BOLD),
                                     bgcolor=color, border_radius=10,
                                     padding=ft.padding.symmetric(horizontal=7, vertical=2)),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.only(bottom=10)),
                    ft.Container(height=1, bgcolor=color + "44",
                                 shadow=ft.BoxShadow(blur_radius=4, color=color)),
                    ft.Container(height=10),
                    ft.Column(cards if cards else [
                        ft.Container(content=ft.Text("خالی", color=C_TX2, size=11,
                                                     text_align=ft.TextAlign.CENTER),
                                     alignment=ft.alignment.center, height=60)
                    ], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
                ], spacing=0, expand=True),
                bgcolor=BG_C2, border=ft.border.all(1, color + "44"), border_radius=12,
                padding=14, expand=True, shadow=glow(color, 10, 0),
            )

        return ft.Column([
            ft.Row([
                ft.Text("تخته کانبان", color=C_TX, size=22, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=16),
            ft.Row([kanban_col(s, c, i) for s, c, i in cols], spacing=12, expand=True,
                   vertical_alignment=ft.CrossAxisAlignment.START),
        ], expand=True, spacing=0)

    # ── PERSONNEL VIEW ───────────────────────────

    def _personnel_view(self, selected=None):
        counts = db.get_person_task_counts()

        def person_card(p):
            name = p["name"]
            total = p["total"] or 0
            active = p["active"] or 0
            completed = p["completed"] or 0
            cancelled = p["cancelled"] or 0
            pct = completed / total if total else 0
            is_sel = name == selected
            border_c = C_CY if is_sel else C_BRD

            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=ft.Text(name[0] if name else "?", color=BG,
                                                     size=16, weight=ft.FontWeight.BOLD),
                                     bgcolor=C_CY if is_sel else C_PU, width=40, height=40,
                                     border_radius=20, alignment=ft.alignment.center,
                                     shadow=glow(C_CY if is_sel else C_PU, 10)),
                        ft.Column([ft.Text(name, color=C_TX, size=13,
                                           weight=ft.FontWeight.W_600),
                                   ft.Text(f"{total} کار", color=C_TX2, size=10)],
                                  spacing=1, expand=True),
                    ], spacing=10),
                    ft.Container(height=10),
                    ft.Row([
                        ft.Column([ft.Text(str(active), color=C_CY, size=18,
                                           weight=ft.FontWeight.BOLD,
                                           text_align=ft.TextAlign.CENTER),
                                   ft.Text("در حال انجام", color=C_TX2, size=9,
                                           text_align=ft.TextAlign.CENTER)],
                                  horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                  expand=True),
                        ft.Container(width=1, height=30, bgcolor=C_BRD),
                        ft.Column([ft.Text(str(completed), color=C_GR, size=18,
                                           weight=ft.FontWeight.BOLD,
                                           text_align=ft.TextAlign.CENTER),
                                   ft.Text("تکمیل", color=C_TX2, size=9,
                                           text_align=ft.TextAlign.CENTER)],
                                  horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                  expand=True),
                        ft.Container(width=1, height=30, bgcolor=C_BRD),
                        ft.Column([ft.Text(str(cancelled), color=C_DIM, size=18,
                                           weight=ft.FontWeight.BOLD,
                                           text_align=ft.TextAlign.CENTER),
                                   ft.Text("منتفی", color=C_TX2, size=9,
                                           text_align=ft.TextAlign.CENTER)],
                                  horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                  expand=True),
                    ], spacing=0),
                    ft.Container(height=8),
                    ft.Stack([
                        ft.Container(height=6, bgcolor=C_DIM, border_radius=3),
                        ft.Container(height=6, width=int(180 * pct), bgcolor=C_GR,
                                     border_radius=3,
                                     shadow=ft.BoxShadow(blur_radius=6, color=C_GR)),
                    ]),
                    ft.Text(f"{int(pct * 100)}% تکمیل", color=C_GR, size=9,
                            text_align=ft.TextAlign.RIGHT),
                ], spacing=4),
                bgcolor=BG_C2 if is_sel else BG_CARD,
                border=ft.border.all(1 if not is_sel else 2, border_c),
                border_radius=12, padding=16,
                shadow=glow(C_CY, 16) if is_sel else glow(C_BRD, 4),
                on_click=lambda e, n=name: self._person_tasks(n), width=200,
            )

        cards_row = ft.Row(
            [person_card(p) for p in counts] if counts else [
                ft.Text("هنوز پرسنلی ثبت نشده", color=C_TX2, size=12)],
            wrap=True, spacing=14, run_spacing=14,
        )

        selected_panel = ft.Container()
        if selected:
            tasks = db.get_all_tasks({"assigned_to": selected})
            rows = [self._task_row(t) for t in tasks]
            selected_panel = ft.Container(content=ft.Column([
                ft.Container(height=16),
                ft.Row([
                    ft.Icon(ft.Icons.ASSIGNMENT_IND_ROUNDED, color=C_CY, size=18),
                    ft.Text(f"کارهای {selected}", color=C_CY, size=14,
                            weight=ft.FontWeight.W_600),
                    ft.Container(content=ft.Text(str(len(tasks)), color=BG, size=11),
                                 bgcolor=C_CY, border_radius=10,
                                 padding=ft.padding.symmetric(horizontal=8, vertical=2)),
                ], spacing=8),
                ft.Container(height=8),
                ft.Column(rows if rows else [
                    ft.Text("کاری برای این شخص ثبت نشده", color=C_TX2, size=12)],
                    spacing=6),
            ]))

        return ft.Column([
            ft.Row([
                ft.Text("مدیریت پرسنل", color=C_TX, size=22, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=16), cards_row, selected_panel,
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

    def _person_tasks(self, name):
        self._content.content = self._personnel_view(selected=name)
        self.page.update()

    # ── SECTIONS VIEW (فقط ادمین) ────────────────

    def _sections_view(self):
        sections = db.get_sections()
        users = [u for u in db.get_users() if u.get("role") in ("admin", "manager")]

        def section_card(s):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=ft.Text(s["name"][0] if s["name"] else "?",
                                                     color=BG, size=16,
                                                     weight=ft.FontWeight.BOLD),
                                     bgcolor=C_CY, width=40, height=40, border_radius=10,
                                     alignment=ft.alignment.center),
                        ft.Column([
                            ft.Text(s["name"], color=C_TX, size=14,
                                    weight=ft.FontWeight.W_600),
                            ft.Text(f"مدیر: {s.get('manager_name') or 'ندارد'}",
                                    color=C_TX2, size=11),
                        ], spacing=2, expand=True),
                    ], spacing=10),
                    ft.Container(height=8),
                    ft.Text(s.get("description", "")[:80] or "بدون توضیح", color=C_TX2,
                            size=11),
                    ft.Container(height=8),
                    ft.Row([
                        ft.Container(content=ft.Text(f"{s.get('member_count', 0)} عضو",
                                                     color=C_CY, size=10),
                                     bgcolor=C_CY + "22", border_radius=4,
                                     padding=ft.padding.symmetric(horizontal=6, vertical=2)),
                        ft.Container(content=ft.Text(f"{s.get('task_count', 0)} کار",
                                                     color=C_OR, size=10),
                                     bgcolor=C_OR + "22", border_radius=4,
                                     padding=ft.padding.symmetric(horizontal=6, vertical=2)),
                    ], spacing=6),
                    ft.Container(height=6),
                    ft.Row([
                        ghost_btn("ویرایش", lambda e, sid=s["id"]: self._edit_section_dlg(sid),
                                  C_CY, ft.Icons.EDIT_ROUNDED),
                        ghost_btn("حذف", lambda e, sid=s["id"]: self._delete_section(sid),
                                  C_RE, ft.Icons.DELETE_OUTLINE_ROUNDED),
                    ], spacing=6),
                ], spacing=4),
                bgcolor=BG_CARD, border=ft.border.all(1, C_BRD), border_radius=12,
                padding=16, width=280,
            )

        cards = ft.Row([section_card(s) for s in sections] if sections else [
            ft.Text("هنوز بخشی تعریف نشده", color=C_TX2, size=12)],
            wrap=True, spacing=14, run_spacing=14)

        return ft.Column([
            ft.Row([
                ft.Text("مدیریت بخش‌ها", color=C_TX, size=22, weight=ft.FontWeight.BOLD),
                neon_btn("+ بخش جدید", lambda e: self._add_section_dlg(), C_CY),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=16), cards,
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

    def _add_section_dlg(self):
        users = [u for u in db.get_users() if u.get("role") in ("admin", "manager")]
        name_f = ft.TextField(label="نام بخش *", bgcolor=BG_IN, border_color=C_BRD,
                              focused_border_color=C_CY, color=C_TX, border_radius=8,
                              label_style=ft.TextStyle(color=C_TX2), text_size=13)
        desc_f = ft.TextField(label="توضیحات", bgcolor=BG_IN, border_color=C_BRD,
                              focused_border_color=C_CY, color=C_TX, border_radius=8,
                              label_style=ft.TextStyle(color=C_TX2), text_size=13,
                              multiline=True, min_lines=2)
        mgr_dd = ft.Dropdown(
            label="مدیر بخش",
            options=[ft.dropdown.Option("")] + [ft.dropdown.Option(f"{u['full_name']} ({u['username']})") for u in users],
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY, color=C_TX,
            border_radius=8, label_style=ft.TextStyle(color=C_TX2), text_size=13,
        )

        def save(e):
            if not name_f.value.strip():
                return
            manager_id = None
            if mgr_dd.value:
                for u in users:
                    if f"{u['full_name']} ({u['username']})" == mgr_dd.value:
                        manager_id = u["id"]
                        break
            db.create_section(name_f.value.strip(), manager_id, desc_f.value or "")
            self._close_dlg(dlg)
            self._go("sections")
            self._snack("بخش جدید ایجاد شد", C_CY)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("افزودن بخش جدید", color=C_CY, weight=ft.FontWeight.BOLD),
            content=ft.Column([name_f, mgr_dd, desc_f], spacing=12, width=420),
            actions=[ghost_btn("لغو", lambda e: self._close_dlg(dlg), C_TX2),
                     neon_btn("ذخیره", save, C_CY)],
            bgcolor=BG_CARD, shape=ft.RoundedRectangleBorder(radius=12),
        )
        self.page.open(dlg)

    def _edit_section_dlg(self, sid):
        section = db.get_section(sid)
        if not section:
            return
        users = [u for u in db.get_users() if u.get("role") in ("admin", "manager")]

        name_f = ft.TextField(value=section["name"], label="نام بخش *", bgcolor=BG_IN,
                              border_color=C_BRD, focused_border_color=C_CY, color=C_TX,
                              border_radius=8, label_style=ft.TextStyle(color=C_TX2),
                              text_size=13)
        desc_f = ft.TextField(value=section.get("description", ""), label="توضیحات",
                              bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
                              color=C_TX, border_radius=8,
                              label_style=ft.TextStyle(color=C_TX2), text_size=13,
                              multiline=True, min_lines=2)
        mgr_dd = ft.Dropdown(
            label="مدیر بخش",
            options=[ft.dropdown.Option("")] + [ft.dropdown.Option(f"{u['full_name']} ({u['username']})") for u in users],
            value="",
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY, color=C_TX,
            border_radius=8, label_style=ft.TextStyle(color=C_TX2), text_size=13,
        )

        def save(e):
            if not name_f.value.strip():
                return
            manager_id = None
            if mgr_dd.value:
                for u in users:
                    if f"{u['full_name']} ({u['username']})" == mgr_dd.value:
                        manager_id = u["id"]
                        break
            db.update_section(sid, {
                "name": name_f.value.strip(),
                "manager_id": manager_id,
                "description": desc_f.value or "",
            })
            self._close_dlg(dlg)
            self._go("sections")
            self._snack("بخش ویرایش شد", C_GR)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("ویرایش بخش", color=C_CY, weight=ft.FontWeight.BOLD),
            content=ft.Column([name_f, mgr_dd, desc_f], spacing=12, width=420),
            actions=[ghost_btn("لغو", lambda e: self._close_dlg(dlg), C_TX2),
                     neon_btn("ذخیره", save, C_CY)],
            bgcolor=BG_CARD, shape=ft.RoundedRectangleBorder(radius=12),
        )
        self.page.open(dlg)

    def _delete_section(self, sid):
        db.delete_section(sid)
        self._go("sections")
        self._snack("بخش حذف شد", C_OR)

    # ── USERS VIEW (فقط ادمین) ───────────────────

    def _users_view(self):
        users = db.get_users()
        sections = db.get_sections()

        def user_card(u):
            role_labels = {"admin": "ادمین", "manager": "مدیر", "user": "کاربر"}
            role_colors = {"admin": C_RE, "manager": C_CY, "user": C_GR}
            rc = role_colors.get(u.get("role", "user"), C_TX2)

            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=ft.Text((u.get("full_name") or u["username"])[0],
                                                     color=BG, size=16,
                                                     weight=ft.FontWeight.BOLD),
                                     bgcolor=rc, width=40, height=40, border_radius=20,
                                     alignment=ft.alignment.center),
                        ft.Column([
                            ft.Text(u.get("full_name") or u["username"], color=C_TX, size=13,
                                    weight=ft.FontWeight.W_600),
                            ft.Text(f"@{u['username']}", color=C_TX2, size=10),
                        ], spacing=2, expand=True),
                        tag(role_labels.get(u.get("role", "user"), "?"), rc),
                    ], spacing=10),
                    ft.Container(height=6),
                    ft.Text(f"بخش: {u.get('section_name') or 'ندارد'}", color=C_TX2,
                            size=11),
                    ft.Container(height=8),
                    ft.Row([
                        ghost_btn("ویرایش", lambda e, uid=u["id"]: self._edit_user_dlg(uid),
                                  C_CY, ft.Icons.EDIT_ROUNDED),
                        ghost_btn("حذف", lambda e, uid=u["id"]: self._delete_user(uid),
                                  C_RE, ft.Icons.DELETE_OUTLINE_ROUNDED),
                    ], spacing=6),
                ], spacing=4),
                bgcolor=BG_CARD, border=ft.border.all(1, C_BRD), border_radius=12,
                padding=16, width=280,
            )

        cards = ft.Row([user_card(u) for u in users] if users else [],
            wrap=True, spacing=14, run_spacing=14)

        return ft.Column([
            ft.Row([
                ft.Text("مدیریت کاربران", color=C_TX, size=22, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ghost_btn("ایمپورت اکسل", lambda e: self._import_users_dlg(), C_PU,
                              ft.Icons.UPLOAD_FILE_ROUNDED),
                    neon_btn("+ کاربر جدید", lambda e: self._add_user_dlg(), C_CY),
                ], spacing=8),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=16), cards,
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

    def _add_user_dlg(self):
        sections = db.get_sections()
        username_f = ft.TextField(label="نام کاربری *", bgcolor=BG_IN, border_color=C_BRD,
                                  focused_border_color=C_CY, color=C_TX, border_radius=8,
                                  label_style=ft.TextStyle(color=C_TX2), text_size=13)
        password_f = ft.TextField(label="رمز عبور *", bgcolor=BG_IN, border_color=C_BRD,
                                  focused_border_color=C_CY, color=C_TX, border_radius=8,
                                  label_style=ft.TextStyle(color=C_TX2), text_size=13,
                                  password=True)
        name_f = ft.TextField(label="نام کامل", bgcolor=BG_IN, border_color=C_BRD,
                              focused_border_color=C_CY, color=C_TX, border_radius=8,
                              label_style=ft.TextStyle(color=C_TX2), text_size=13)
        role_dd = ft.Dropdown(
            label="نقش",
            options=[ft.dropdown.Option(o) for o in ["user", "manager", "admin"]],
            value="user", bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
            color=C_TX, border_radius=8, label_style=ft.TextStyle(color=C_TX2),
            text_size=13,
        )
        section_dd = ft.Dropdown(
            label="بخش",
            options=[ft.dropdown.Option("")] + [ft.dropdown.Option(s["name"]) for s in sections],
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY, color=C_TX,
            border_radius=8, label_style=ft.TextStyle(color=C_TX2), text_size=13,
        )

        def save(e):
            if not username_f.value.strip() or not password_f.value:
                return
            section_id = None
            if section_dd.value:
                for s in sections:
                    if s["name"] == section_dd.value:
                        section_id = s["id"]
                        break
            uid = db.create_user(username_f.value.strip(), password_f.value,
                                 name_f.value.strip(), role_dd.value, section_id)
            if uid:
                self._close_dlg(dlg)
                self._go("users")
                self._snack("کاربر جدید ایجاد شد", C_GR)
            else:
                self._snack("نام کاربری تکراری است", C_RE)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("افزودن کاربر جدید", color=C_CY, weight=ft.FontWeight.BOLD),
            content=ft.Column([username_f, password_f, name_f, role_dd, section_dd],
                              spacing=12, width=420),
            actions=[ghost_btn("لغو", lambda e: self._close_dlg(dlg), C_TX2),
                     neon_btn("ذخیره", save, C_CY)],
            bgcolor=BG_CARD, shape=ft.RoundedRectangleBorder(radius=12),
        )
        self.page.open(dlg)

    def _edit_user_dlg(self, uid):
        user = db.get_user(uid)
        if not user:
            return
        sections = db.get_sections()

        name_f = ft.TextField(value=user.get("full_name", ""), label="نام کامل",
                              bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
                              color=C_TX, border_radius=8,
                              label_style=ft.TextStyle(color=C_TX2), text_size=13)
        password_f = ft.TextField(label="رمز عبور جدید (خالی = بدون تغییر)", bgcolor=BG_IN,
                                  border_color=C_BRD, focused_border_color=C_CY, color=C_TX,
                                  border_radius=8, label_style=ft.TextStyle(color=C_TX2),
                                  text_size=13, password=True)
        role_dd = ft.Dropdown(
            label="نقش",
            options=[ft.dropdown.Option(o) for o in ["user", "manager", "admin"]],
            value=user.get("role", "user"), bgcolor=BG_IN, border_color=C_BRD,
            focused_border_color=C_CY, color=C_TX, border_radius=8,
            label_style=ft.TextStyle(color=C_TX2), text_size=13,
        )
        section_dd = ft.Dropdown(
            label="بخش",
            options=[ft.dropdown.Option("")] + [ft.dropdown.Option(s["name"]) for s in sections],
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY, color=C_TX,
            border_radius=8, label_style=ft.TextStyle(color=C_TX2), text_size=13,
        )

        def save(e):
            section_id = None
            if section_dd.value:
                for s in sections:
                    if s["name"] == section_dd.value:
                        section_id = s["id"]
                        break
            data = {
                "full_name": name_f.value.strip(),
                "role": role_dd.value,
                "section_id": section_id,
            }
            if password_f.value:
                data["password"] = password_f.value
            db.update_user(uid, data)
            self._close_dlg(dlg)
            self._go("users")
            self._snack("کاربر ویرایش شد", C_GR)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("ویرایش کاربر", color=C_CY, weight=ft.FontWeight.BOLD),
            content=ft.Column([name_f, password_f, role_dd, section_dd], spacing=12, width=420),
            actions=[ghost_btn("لغو", lambda e: self._close_dlg(dlg), C_TX2),
                     neon_btn("ذخیره", save, C_CY)],
            bgcolor=BG_CARD, shape=ft.RoundedRectangleBorder(radius=12),
        )
        self.page.open(dlg)

    def _delete_user(self, uid):
        db.delete_user(uid)
        self._go("users")
        self._snack("کاربر حذف شد", C_OR)

    def _import_users_dlg(self):
        file_picker = ft.FilePicker(on_result=lambda e: self._on_import_file_picked(e))

        def pick_file(e):
            self.page.overlay.append(file_picker)
            self.page.update()
            file_picker.pick_files(allowed_extensions=["xlsx", "xls"])

        def do_import(e):
            if not self._import_file_path:
                self._snack("فایل اکسل را انتخاب کنید", C_RE)
                return
            count, msg = db.import_users_from_excel(self._import_file_path)
            self._close_dlg(dlg)
            self._go("users")
            self._snack(msg, C_GR if count > 0 else C_RE)

        self._import_file_path = ""
        file_name_txt = ft.Text("فایلی انتخاب نشده", color=C_TX2, size=12)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("ایمپورت کاربران از اکسل", color=C_PU,
                          weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Text("ستون‌های مورد نیاز: نام, کد پرسنلی, دپارتمان, نقش, فعال",
                        color=C_TX2, size=11),
                ft.Container(height=8),
                ft.Row([
                    ghost_btn("انتخاب فایل", pick_file, C_PU,
                              ft.Icons.FOLDER_OPEN_ROUNDED),
                    file_name_txt,
                ], spacing=10),
            ], spacing=12, width=420),
            actions=[ghost_btn("لغو", lambda e: self._close_dlg(dlg), C_TX2),
                     neon_btn("ایمپورت", do_import, C_PU)],
            bgcolor=BG_CARD, shape=ft.RoundedRectangleBorder(radius=12),
        )
        self.page.open(dlg)

    def _on_import_file_picked(self, e):
        if e.files and len(e.files) > 0:
            self._import_file_path = e.files[0].path

    # ── CHAT VIEW ────────────────────────────────

    def _chat_view(self):
        user = self.current_user
        sections = db.get_sections()
        all_users = db.get_users()
        uid = user["id"]

        if not hasattr(self, '_chat_mode'):
            self._chat_mode = "group"
        if not hasattr(self, '_chat_section_id') or self._chat_section_id is None:
            self._chat_section_id = user.get("section_id") or (sections[0]["id"] if sections else None)
        if not hasattr(self, '_chat_dm_user'):
            self._chat_dm_user = None

        unread_dm = db.get_unread_dm_count(uid)
        dm_contacts = db.get_dm_contacts(uid)

        # ── تب‌های چت گروهی / انفرادی ──
        tab_group = ft.Container(
            content=ft.Text("چت گروهی", color=C_CY if self._chat_mode == "group" else C_TX2,
                            size=13, weight=ft.FontWeight.W_600 if self._chat_mode == "group" else ft.FontWeight.NORMAL),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(2, C_CY if self._chat_mode == "group" else "transparent")),
            on_click=lambda e: self._switch_chat_mode("group"),
        )
        tab_dm = ft.Container(
            content=ft.Row([
                ft.Text("پیام خصوصی", color=C_CY if self._chat_mode == "dm" else C_TX2,
                        size=13, weight=ft.FontWeight.W_600 if self._chat_mode == "dm" else ft.FontWeight.NORMAL),
                ft.Container(content=ft.Text(str(unread_dm), size=9, color=BG, weight=ft.FontWeight.BOLD),
                             bgcolor=C_RE, border_radius=8,
                             padding=ft.padding.symmetric(horizontal=4, vertical=1),
                             visible=unread_dm > 0),
            ], spacing=6),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(2, C_CY if self._chat_mode == "dm" else "transparent")),
            on_click=lambda e: self._switch_chat_mode("dm"),
        )

        if self._chat_mode == "group":
            return self._chat_group_view(sections, all_users, tab_group, tab_dm)
        else:
            return self._chat_dm_view(all_users, dm_contacts, tab_group, tab_dm)

    def _switch_chat_mode(self, mode):
        self._chat_mode = mode
        self._go("chat")

    # ── چت گروهی ──
    def _chat_group_view(self, sections, all_users, tab_group, tab_dm):
        user = self.current_user
        uid = user["id"]

        if not sections:
            return ft.Column([tab_group, tab_dm,
                ft.Container(content=ft.Text("هنوز بخشی تعریف نشده", color=C_TX2, size=14),
                             alignment=ft.alignment.center, padding=60, expand=True)
            ], expand=True, spacing=0)

        section_dd = ft.Dropdown(
            hint_text="بخش را انتخاب کنید",
            options=[ft.dropdown.Option(s["name"]) for s in sections],
            value=next((s["name"] for s in sections if s["id"] == self._chat_section_id), None),
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_CY,
            color=C_TX, border_radius=8, width=200, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
        )

        def on_section_change(e):
            for s in sections:
                if s["name"] == section_dd.value:
                    self._chat_section_id = s["id"]
                    break
            self._go("chat")
        section_dd.on_change = on_section_change

        messages = db.get_messages(self._chat_section_id) if self._chat_section_id else []
        section_name = next((s["name"] for s in sections if s["id"] == self._chat_section_id), "")
        section_members = [u for u in all_users if u.get("section_id") == self._chat_section_id]

        msg_controls = self._build_msg_controls(messages, uid)

        msg_list = ft.Column(msg_controls if msg_controls else [
            ft.Text("هنوز پیامی ارسال نشده", color=C_TX2, size=12, text_align=ft.TextAlign.CENTER)
        ], spacing=6, scroll=ft.ScrollMode.AUTO, expand=True, auto_scroll=True)

        msg_input, voice_btn, file_btn, send_btn, file_label = self._build_input_bar(
            lambda e: self._send_group_msg(), "group")

        header = ft.Row([tab_group, tab_dm,
            ft.Container(expand=True),
            ft.Text(f"چت گروهی: {section_name}", color=C_TX, size=14, weight=ft.FontWeight.W_600),
        ], spacing=0)

        member_items = []
        for m in section_members:
            mname = m.get("full_name") or m["username"]
            member_items.append(ft.Row([
                ft.Container(content=ft.Text(mname[0] if mname else "?", color=BG, size=10,
                                             weight=ft.FontWeight.BOLD),
                             bgcolor=C_PU, width=24, height=24, border_radius=12,
                             alignment=ft.alignment.center),
                ft.Column([ft.Text(mname, color=C_TX, size=11),
                           ft.Text(m.get("role", ""), color=C_TX2, size=9)], spacing=1, expand=True),
            ], spacing=6))
        if not member_items:
            member_items = [ft.Text("عضوی وجود ندارد", color=C_TX2, size=11)]

        members_panel = ft.Container(
            content=ft.Column([ft.Text("اعضای بخش", color=C_CY, size=12, weight=ft.FontWeight.W_600),
                              ft.Container(height=6)] + member_items, spacing=6),
            width=150, bgcolor=BG_CARD, border=ft.border.all(1, C_BRD), border_radius=10, padding=10)

        return ft.Column([header, ft.Container(height=8),
            ft.Row([members_panel, ft.Container(width=10),
                ft.Column([neon_card(msg_list, color=C_BRD, padding=14, expand=True),
                    ft.Container(height=8),
                    ft.Container(content=ft.Column([ft.Row([msg_input, voice_btn, file_btn, send_btn],
                        spacing=6, vertical_alignment=ft.CrossAxisAlignment.END), file_label], spacing=3),
                        bgcolor=BG_CARD, border=ft.border.all(1, C_BRD), border_radius=10, padding=10),
                ], spacing=0, expand=True)], expand=True)
        ], expand=True, spacing=0)

    def _send_group_msg(self):
        user = self.current_user
        if not self._chat_section_id:
            self._snack("ابتدا یک بخش انتخاب کنید", C_RE)
            return
        content = getattr(self, '_chat_msg_input_val', '') or ""
        file_data = getattr(self, '_chat_file_data', None) or ""
        file_name = getattr(self, '_chat_file_name', '') or ""
        voice_data = getattr(self, '_chat_voice_data', '') or ""
        msg_type = "voice" if voice_data else ("file" if file_data else "text")

        if not content.strip() and not file_data and not voice_data:
            return

        db.add_message(self._chat_section_id, user["id"], content.strip(),
                       file_name=file_name, file_data=file_data, voice_data=voice_data, msg_type=msg_type)

        con = db._conn()
        cur = con.cursor()
        if db.USE_POSTGRES:
            cur.execute("SELECT id FROM users WHERE section_id=%s AND id!=%s", (self._chat_section_id, user["id"]))
        else:
            cur.execute("SELECT id FROM users WHERE section_id=? AND id!=?", (self._chat_section_id, user["id"]))
        others = [r['id'] for r in cur.fetchall()]
        con.close()

        alarm_msg = f"پیام جدید از {user.get('full_name', '')} در چت گروهی"
        if file_name:
            alarm_msg += f" (فایل: {file_name})"
        if voice_data:
            alarm_msg += " (پیام صوتی)"
        elif content.strip():
            alarm_msg += f": {content[:30]}..."
        for oid in others:
            db.add_alarm(None, alarm_msg, user_id=oid)

        self._chat_file_data = None
        self._chat_file_name = ""
        self._chat_voice_data = ""
        self._chat_msg_input_val = ""
        self._go("chat")

    # ── چت انفرادی ──
    def _chat_dm_view(self, all_users, dm_contacts, tab_group, tab_dm):
        user = self.current_user
        uid = user["id"]

        if not self._chat_dm_user:
            contact_items = []
            for c in dm_contacts:
                cname = c.get("full_name") or c["username"]
                unread = c.get("unread", 0) or 0
                contact_items.append(ft.Container(
                    content=ft.Row([
                        ft.Container(content=ft.Text(cname[0] if cname else "?", color=BG, size=14,
                                                     weight=ft.FontWeight.BOLD),
                                     bgcolor=C_CY if unread else C_PU, width=36, height=36, border_radius=18,
                                     alignment=ft.alignment.center),
                        ft.Column([
                            ft.Text(cname, color=C_TX, size=12, weight=ft.FontWeight.W_500),
                            ft.Text((c.get("last_msg") or "")[:40], color=C_TX2, size=10),
                        ], spacing=1, expand=True),
                        ft.Column([
                            ft.Text((c.get("last_time") or "")[:10], color=C_DIM, size=9),
                            ft.Container(content=ft.Text(str(unread), size=8, color=BG),
                                         bgcolor=C_RE, border_radius=8,
                                         padding=ft.padding.symmetric(horizontal=3, vertical=1),
                                         visible=unread > 0),
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=BG_C2, border=ft.border.all(1, C_BRD), border_radius=8, padding=10,
                    on_click=lambda e, cid=c["id"]: self._open_dm(cid),
                ))

            other_users = [u for u in all_users if u["id"] != uid and u.get("is_active", True)]
            user_items = []
            for u in other_users:
                uname = u.get("full_name") or u["username"]
                user_items.append(ft.Container(
                    content=ft.Row([
                        ft.Container(content=ft.Text(uname[0] if uname else "?", color=BG, size=14,
                                                     weight=ft.FontWeight.BOLD),
                                     bgcolor=C_GR, width=36, height=36, border_radius=18,
                                     alignment=ft.alignment.center),
                        ft.Column([
                            ft.Text(uname, color=C_TX, size=12),
                            ft.Text(u.get("section_name") or "", color=C_TX2, size=10),
                        ], spacing=1, expand=True),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=BG_C2, border=ft.border.all(1, C_BRD), border_radius=8, padding=10,
                    on_click=lambda e, cid=u["id"]: self._open_dm(cid),
                ))

            header = ft.Row([tab_group, tab_dm, ft.Container(expand=True),
                ft.Text("پیام خصوصی", color=C_TX, size=14, weight=ft.FontWeight.W_600)])
            all_items = contact_items + ([ft.Container(height=8)] if contact_items else []) + user_items

            return ft.Column([header, ft.Container(height=10),
                neon_card(ft.Column(all_items if all_items else [
                    ft.Text("هنوز مکالمه‌ای وجود ندارد", color=C_TX2, size=12)],
                    spacing=6, scroll=ft.ScrollMode.AUTO), color=C_BRD, padding=14, expand=True)
            ], expand=True, spacing=0)

        # نمایش مکالمه
        dm_user = db.get_user(self._chat_dm_user)
        dm_user_name = dm_user.get("full_name") or dm_user.get("username", "") if dm_user else ""
        messages = db.get_direct_messages(uid, self._chat_dm_user)

        db.mark_dm_read(self._chat_dm_user, uid)

        msg_controls = self._build_dm_controls(messages, uid)

        msg_list = ft.Column(msg_controls if msg_controls else [
            ft.Text("هنوز پیامی رد و بدل نشده", color=C_TX2, size=12, text_align=ft.TextAlign.CENTER)
        ], spacing=6, scroll=ft.ScrollMode.AUTO, expand=True, auto_scroll=True)

        msg_input, voice_btn, file_btn, send_btn, file_label = self._build_input_bar(
            lambda e: self._send_dm_msg(), "dm")

        header = ft.Row([
            ghost_btn("برگشت", lambda e: self._back_to_dm_list(), C_CY, ft.Icons.ARROW_FORWARD_ROUNDED),
            ft.Container(width=8),
            ft.Text(dm_user_name, color=C_TX, size=14, weight=ft.FontWeight.W_600),
        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Column([header, ft.Container(height=10),
            neon_card(msg_list, color=C_BRD, padding=14, expand=True),
            ft.Container(height=8),
            ft.Container(content=ft.Column([ft.Row([msg_input, voice_btn, file_btn, send_btn],
                spacing=6, vertical_alignment=ft.CrossAxisAlignment.END), file_label], spacing=3),
                bgcolor=BG_CARD, border=ft.border.all(1, C_BRD), border_radius=10, padding=10),
        ], expand=True, spacing=0)

    def _open_dm(self, user_id):
        self._chat_dm_user = user_id
        self._go("chat")

    def _back_to_dm_list(self):
        self._chat_dm_user = None
        self._go("chat")

    def _send_dm_msg(self):
        user = self.current_user
        if not self._chat_dm_user:
            return
        content = getattr(self, '_chat_msg_input_val', '') or ""
        file_data = getattr(self, '_chat_file_data', None) or ""
        file_name = getattr(self, '_chat_file_name', '') or ""
        voice_data = getattr(self, '_chat_voice_data', '') or ""
        msg_type = "voice" if voice_data else ("file" if file_data else "text")

        if not content.strip() and not file_data and not voice_data:
            return

        db.add_direct_message(user["id"], self._chat_dm_user, content.strip(),
                              file_name=file_name, file_data=file_data, voice_data=voice_data, msg_type=msg_type)

        receiver = db.get_user(self._chat_dm_user)
        rname = receiver.get("full_name", "") if receiver else ""
        alarm_msg = f"پیام خصوصی از {user.get('full_name', '')}"
        if file_name:
            alarm_msg += f" (فایل: {file_name})"
        if voice_data:
            alarm_msg += " (پیام صوتی)"
        elif content.strip():
            alarm_msg += f": {content[:30]}..."
        db.add_alarm(None, alarm_msg, user_id=self._chat_dm_user)

        self._chat_file_data = None
        self._chat_file_name = ""
        self._chat_voice_data = ""
        self._chat_msg_input_val = ""
        self._go("chat")

    # ── کامپوننت‌های مشترک ──
    def _build_msg_controls(self, messages, uid):
        controls = []
        for m in messages:
            is_me = m.get("sender_id") == uid
            content = m.get("content", "")
            file_name = m.get("file_name", "")
            file_data = m.get("file_data", "")
            voice_data = m.get("voice_data", "")
            sender_name = m.get("sender_name") or "ناشناس"
            msg_type = m.get("msg_type", "text")

            items = [ft.Text(sender_name, color=C_CY if is_me else C_PU, size=10, weight=ft.FontWeight.W_500)]

            if voice_data:
                items.append(self._voice_bubble(voice_data))
            if content:
                items.append(ft.Text(content, color=C_TX, size=13))
            if file_name:
                items.append(self._file_bubble(file_name, file_data))

            controls.append(ft.Container(
                content=ft.Column(items, spacing=3),
                bgcolor=BG_C2 if is_me else BG_CARD,
                border=ft.border.all(1, C_CY + "44" if is_me else C_BRD),
                border_radius=10, padding=10,
                alignment=ft.alignment.center_left if not is_me else ft.alignment.center_right,
                margin=ft.margin.only(left=50 if is_me else 0, right=50 if not is_me else 0),
            ))
        return controls

    def _build_dm_controls(self, messages, uid):
        controls = []
        for m in messages:
            is_me = m.get("sender_id") == uid
            content = m.get("content", "")
            file_name = m.get("file_name", "")
            file_data = m.get("file_data", "")
            voice_data = m.get("voice_data", "")

            items = []
            if voice_data:
                items.append(self._voice_bubble(voice_data))
            if content:
                items.append(ft.Text(content, color=C_TX, size=13))
            if file_name:
                items.append(self._file_bubble(file_name, file_data))
            if not items:
                items.append(ft.Text("پیام خالی", color=C_TX2, size=11))

            controls.append(ft.Container(
                content=ft.Column(items, spacing=3),
                bgcolor=BG_C2 if is_me else BG_CARD,
                border=ft.border.all(1, C_CY + "44" if is_me else C_BRD),
                border_radius=10, padding=10,
                alignment=ft.alignment.center_left if not is_me else ft.alignment.center_right,
                margin=ft.margin.only(left=50 if is_me else 0, right=50 if not is_me else 0),
            ))
        return controls

    def _file_bubble(self, file_name, file_data):
        def make_download(fname=file_name, fdata=file_data):
            def download(e):
                import base64, os
                if fdata:
                    try:
                        data = base64.b64decode(fdata)
                        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
                        path = os.path.join(downloads, fname)
                        with open(path, "wb") as f:
                            f.write(data)
                    except Exception:
                        pass
            return download
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ATTACH_FILE_ROUNDED, color=C_CY, size=14),
                ft.Text(file_name, color=C_CY, size=11, weight=ft.FontWeight.W_500),
                ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, color=C_CY, size=12),
            ], spacing=4),
            bgcolor=C_CY + "11", border=ft.border.all(1, C_CY + "44"),
            border_radius=6, padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_click=make_download(),
        )

    def _voice_bubble(self, voice_data):
        def play_voice(e):
            import base64, os, tempfile, subprocess, platform
            try:
                data = base64.b64decode(voice_data)
                ext = ".ogg" if platform.system() != "Windows" else ".wav"
                tmp = os.path.join(tempfile.gettempdir(), f"voice_{id(voice_data)}{ext}")
                with open(tmp, "wb") as f:
                    f.write(data)
                if platform.system() == "Windows":
                    os.startfile(tmp)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["afplay", tmp])
                else:
                    subprocess.Popen(["aplay", tmp])
            except Exception:
                pass
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED, color=C_GR, size=20),
                ft.Text("پیام صوتی", color=C_GR, size=12),
            ], spacing=4),
            bgcolor=C_GR + "11", border=ft.border.all(1, C_GR + "44"),
            border_radius=6, padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_click=play_voice,
        )

    def _build_input_bar(self, send_callback, mode):
        msg_input = ft.TextField(
            hint_text="پیام بنویسید...", bgcolor=BG_IN, border_color=C_BRD,
            focused_border_color=C_CY, color=C_TX, border_radius=8, expand=True, text_size=13,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8), multiline=True, max_lines=3,
        )

        if not hasattr(self, '_chat_file_data'):
            self._chat_file_data = None
            self._chat_file_name = ""
            self._chat_voice_data = ""

        if not hasattr(self, '_chat_file_picker'):
            self._chat_file_picker = ft.FilePicker(on_result=lambda e: self._on_chat_file_picked(e))
        if not hasattr(self, '_chat_voice_picker'):
            self._chat_voice_picker = ft.FilePicker(on_result=lambda ev: self._on_voice_picked(ev))

        def ensure_overlay():
            if self._chat_file_picker not in self.page.overlay:
                self.page.overlay.append(self._chat_file_picker)
            if self._chat_voice_picker not in self.page.overlay:
                self.page.overlay.append(self._chat_voice_picker)
            self.page.update()

        def pick_file(e):
            ensure_overlay()
            self._chat_file_picker.pick_files(allowed_extensions=["jpg","png","pdf","docx","xlsx","zip","txt","csv","mp3","wav","ogg","mp4"])

        def record_voice(e):
            ensure_overlay()
            self._chat_voice_picker.pick_files(allowed_extensions=["mp3","wav","ogg","m4a","aac","wma"])

        def do_send(e):
            self._chat_msg_input_val = msg_input.value or ""
            send_callback(e)

        def on_key(e):
            if e.key == "Enter" and not e.shift:
                do_send(e)

        file_label = ft.Text("", color=C_PU, size=10)
        self._chat_file_label = file_label

        if self._chat_file_name:
            file_label.value = f"فایل: {self._chat_file_name}"
        if self._chat_voice_data:
            file_label.value = "پیام صوتی آماده ارسال"

        voice_btn = ghost_btn("ویس", record_voice, C_GR, ft.Icons.MIC_ROUNDED)
        file_btn = ghost_btn("فایل", pick_file, C_PU, ft.Icons.ATTACH_FILE_ROUNDED)
        send_btn = neon_btn("ارسال", do_send, C_CY, ft.Icons.SEND_ROUNDED)

        return msg_input, voice_btn, file_btn, send_btn, file_label

    def _on_chat_file_picked(self, e):
        if e.files and len(e.files) > 0 and e.files[0].path:
            import base64, os
            fpath = e.files[0].path
            fname = e.files[0].name
            try:
                with open(fpath, "rb") as f:
                    self._chat_file_data = base64.b64encode(f.read()).decode()
                self._chat_file_name = fname
                if hasattr(self, '_chat_file_label') and self._chat_file_label:
                    self._chat_file_label.value = f"فایل: {fname}"
                    self.page.update()
                self._snack(f"فایل {fname} آماده ارسال", C_GR)
            except Exception as ex:
                self._snack(f"خطا در خواندن فایل: {ex}", C_RE)

    def _on_voice_picked(self, e):
        if e.files and len(e.files) > 0 and e.files[0].path:
            import base64, os
            fpath = e.files[0].path
            fname = e.files[0].name
            try:
                with open(fpath, "rb") as f:
                    self._chat_voice_data = base64.b64encode(f.read()).decode()
                self._chat_file_name = ""
                self._chat_file_data = None
                if hasattr(self, '_chat_file_label') and self._chat_file_label:
                    self._chat_file_label.value = f"پیام صوتی: {fname}"
                    self.page.update()
                self._snack(f"پیام صوتی {fname} آماده ارسال", C_GR)
            except Exception as ex:
                self._snack(f"خطا در خواندن فایل صوتی: {ex}", C_RE)

    # ── DAILY REPORT VIEW ────────────────────────

    def _daily_report_view(self):
        user = self.current_user
        uid = user["id"]

        jy, jm, jd = ju.today_j()
        today_str = f"{jy}{jm:02d}{jd:02d}"
        today_tasks = db.get_today_tasks(uid)
        today_progress = db.get_daily_progress(uid, today_str)

        progress_map = {p["task_id"]: p for p in today_progress}

        task_controls = []
        for t in today_tasks:
            existing = progress_map.get(t["id"])
            prog_val = existing["progress_pct"] / 100 if existing else t.get("progress", 0.0)
            notes_val = existing["notes"] if existing else ""

            slider = ft.Slider(min=0, max=1, divisions=10, value=prog_val,
                               active_color=C_GR, thumb_color=C_GR, label="{value}",
                               key=f"slider_{t['id']}")
            notes_f = ft.TextField(value=notes_val, hint_text="توضیحات...",
                                   bgcolor=BG_IN, border_color=C_BRD,
                                   focused_border_color=C_CY, color=C_TX, border_radius=8,
                                   text_size=12, expand=True, key=f"notes_{t['id']}",
                                   content_padding=ft.padding.symmetric(horizontal=10, vertical=4))

            task_controls.append(ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(width=4, height=24, bgcolor=C_CY, border_radius=2),
                        ft.Text(t["title"][:50], color=C_TX, size=13,
                                weight=ft.FontWeight.W_500, expand=True),
                        ft.Text(ju.dl_label(ju.days_left(t.get("deadline", ""))),
                                color=ju.dl_color(ju.days_left(t.get("deadline", ""))),
                                size=10),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(height=4),
                    ft.Row([
                        ft.Text("پیشرفت:", color=C_TX2, size=11),
                        slider,
                        notes_f,
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ], spacing=2),
                bgcolor=BG_CARD, border=ft.border.all(1, C_BRD), border_radius=10,
                padding=12,
            ))

        # گزارش‌های 7 روز اخیر
        history_controls = []
        for day_offset in range(1, 8):
            jy2, jm2, jd2 = ju.today_j()
            # تبدیل ساده
            from datetime import date, timedelta
            g_date = date.today() - timedelta(days=day_offset)
            jy2, jm2, jd2 = ju.g2j(g_date.year, g_date.month, g_date.day)
            day_str = f"{jy2}{jm2:02d}{jd2:02d}"
            day_progress = db.get_daily_progress(uid, day_str)
            if day_progress:
                items = []
                for p in day_progress:
                    items.append(ft.Row([
                        ft.Text((p.get("task_title") or "")[:40], color=C_TX, size=11,
                                expand=True),
                        ft.Text(f"{int(p['progress_pct'])}%", color=C_GR, size=11),
                    ], spacing=8))
                history_controls.append(ft.Container(
                    content=ft.Column([
                        ft.Text(ju.fmt_fa(jy2, jm2, jd2), color=C_CY, size=12,
                                weight=ft.FontWeight.W_500),
                        ft.Column(items, spacing=4),
                    ], spacing=4),
                    bgcolor=BG_C2, border=ft.border.all(1, C_BRD), border_radius=8,
                    padding=10,
                ))

        def save_all(e):
            for t in today_tasks:
                for ctrl in task_controls:
                    if hasattr(ctrl.content, 'controls'):
                        row2 = ctrl.content.controls[1] if len(ctrl.content.controls) > 1 else None
                        if row2 and hasattr(row2, 'controls'):
                            for c in row2.controls:
                                if hasattr(c, 'key') and c.key == f"slider_{t['id']}":
                                    slider_val = c.value
                                if hasattr(c, 'key') and c.key == f"notes_{t['id']}":
                                    notes_val = c.value
                            db.save_daily_progress(t["id"], uid, slider_val * 100,
                                                   notes_val or "", today_str)
            # به‌روزرسانی پیشرفت کار در جدول tasks
            for t in today_tasks:
                for ctrl in task_controls:
                    if hasattr(ctrl.content, 'controls'):
                        row2 = ctrl.content.controls[1] if len(ctrl.content.controls) > 1 else None
                        if row2 and hasattr(row2, 'controls'):
                            for c in row2.controls:
                                if hasattr(c, 'key') and c.key == f"slider_{t['id']}":
                                    db.update_task(t["id"], {"progress": c.value})
            self._snack("گزارش روزانه ذخیره شد", C_GR)
            self._go("daily_report")

        return ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("گزارش پیشرفت روزانه", color=C_TX, size=22,
                            weight=ft.FontWeight.BOLD),
                    ft.Text(ju.fmt_fa(jy, jm, jd), color=C_TX2, size=12),
                ], spacing=2),
                neon_btn("ذخیره همه", save_all, C_GR, ft.Icons.SAVE_ROUNDED) if today_tasks else ft.Container(),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=14),
            ft.Column(task_controls if task_controls else [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color=C_GR, size=48),
                        ft.Text("کاری با موعد امروز ندارید", color=C_TX2, size=14,
                                text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    alignment=ft.alignment.center, padding=60,
                ),
            ], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
            ft.Container(height=14) if history_controls else ft.Container(),
            ft.Column(history_controls if history_controls else [], spacing=8),
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

    # ── ALARMS VIEW ──────────────────────────────

    def _alarms_view(self):
        uid = self.current_user["id"]
        alarms = db.get_all_alarms(user_id=uid)
        unread = [a for a in alarms if not a["ack"]]

        def alarm_card(a):
            is_new = not a["ack"]
            color = C_RE if "عقب" in a["message"] else C_OR if "روز تا" in a["message"] else C_CY

            def mark_read(e, aid=a["id"]):
                db.ack_alarm(aid)
                self._go("alarms")
                self._refresh_alarm_badge()

            return ft.Container(
                content=ft.Row([
                    ft.Container(content=ft.Icon(
                        ft.Icons.NOTIFICATIONS_ACTIVE_ROUNDED if is_new else ft.Icons.NOTIFICATIONS_NONE_ROUNDED,
                        color=color, size=20), bgcolor=color + "22", border_radius=10,
                        padding=8),
                    ft.Column([
                        ft.Text(a["message"], color=C_TX if is_new else C_TX2, size=13,
                                weight=ft.FontWeight.W_500 if is_new else ft.FontWeight.NORMAL),
                        ft.Text((a.get("task_title") or "")[:40], color=C_TX2, size=11),
                        ft.Text((a.get("alarm_time") or "")[:16], color=C_DIM, size=10),
                    ], spacing=2, expand=True),
                    ft.IconButton(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, icon_color=C_GR,
                                  icon_size=18, tooltip="خوانده شد", on_click=mark_read,
                                  disabled=not is_new),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=color + "11" if is_new else BG_CARD,
                border=ft.border.all(1, color + "66" if is_new else C_BRD),
                border_radius=10, padding=14,
                shadow=glow(color, 10) if is_new else None,
            )

        def ack_all(e):
            db.ack_all(uid)
            self._go("alarms")
            self._refresh_alarm_badge()
            self._snack("همه آلارم‌ها خوانده شد", C_GR)

        def refresh_alarms(e):
            n = db.check_and_create_alarms(uid)
            self._go("alarms")
            self._refresh_alarm_badge()
            self._snack(f"{n} آلارم جدید یافت شد", C_CY)

        return ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("آلارم‌ها و اعلان‌ها", color=C_TX, size=22,
                            weight=ft.FontWeight.BOLD),
                    ft.Text(f"{len(unread)} خوانده‌نشده از {len(alarms)}", color=C_TX2,
                            size=12),
                ], spacing=2),
                ft.Row([
                    ghost_btn("بررسی مجدد", refresh_alarms, C_CY,
                              ft.Icons.REFRESH_ROUNDED),
                    ft.Container(width=8),
                    ghost_btn("همه خوانده شد", ack_all, C_GR,
                              ft.Icons.DONE_ALL_ROUNDED),
                ], spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=16),
            ft.Container(content=ft.Column([
                ft.Row([ft.Container(width=4, height=20, bgcolor=C_RE, border_radius=2),
                        ft.Text("خوانده‌نشده", color=C_RE, size=13,
                                weight=ft.FontWeight.W_500)], spacing=8),
                ft.Container(height=8),
                ft.Column([alarm_card(a) for a in unread] if unread else [
                    ft.Container(content=ft.Column([
                        ft.Text("هیچ آلارم خوانده‌نشده‌ای ندارید", color=C_TX2, size=13,
                                text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center, height=100)
                ], spacing=8),
            ]), bgcolor=BG_CARD, border=ft.border.all(1, C_RE + "44"), border_radius=12,
                padding=16),
            ft.Container(height=14),
            neon_card(ft.Column([
                ft.Text("تاریخچه آلارم‌ها", color=C_TX2, size=13,
                        weight=ft.FontWeight.W_500),
                ft.Container(height=8),
                ft.Column([alarm_card(a) for a in alarms if a["ack"]] or [
                    ft.Text("تاریخچه‌ای موجود نیست", color=C_TX2, size=12)],
                    spacing=6),
            ]), color=C_BRD, padding=16),
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

    # ── NOTES VIEW ───────────────────────────────

    def _notes_view(self):
        notes = db.get_notes()
        note_field = ft.TextField(
            label="یادداشت جدید", hint_text="متن یادداشت را بنویسید...",
            bgcolor=BG_IN, border_color=C_BRD, focused_border_color=C_YE, color=C_TX,
            border_radius=8, label_style=ft.TextStyle(color=C_TX2),
            multiline=True, min_lines=2, max_lines=5, text_size=13, expand=True,
        )
        date_field = ft.TextField(
            label="تاریخ (اختیاری، مثال: 14041201)", bgcolor=BG_IN, border_color=C_BRD,
            focused_border_color=C_YE, color=C_TX, border_radius=8,
            label_style=ft.TextStyle(color=C_TX2), width=200, text_size=13,
        )

        def save_note(e):
            if not note_field.value.strip():
                return
            db.add_note(note_field.value.strip(), date_field.value.strip())
            self._go("notes")
            self._snack("یادداشت ذخیره شد", C_YE)

        def del_note(e, nid):
            db.delete_note(nid)
            self._go("notes")

        note_cards = []
        for n in notes:
            note_cards.append(ft.Container(content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.STICKY_NOTE_2_ROUNDED, color=C_YE, size=14),
                    ft.Text(n.get("note_date") or (n.get("created_at") or "")[:10],
                            color=C_TX2, size=10),
                    ft.Container(expand=True),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE_ROUNDED, icon_color=C_RE,
                                  icon_size=14,
                                  on_click=lambda e, nid=n["id"]: del_note(e, nid)),
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text(n["content"], color=C_TX, size=12),
            ], spacing=4), bgcolor=BG_C2, border=ft.border.all(1, C_YE + "44"),
                border_radius=10, padding=12, shadow=glow(C_YE, 8, 0)))

        return ft.Column([
            ft.Text("یادداشت‌ها", color=C_TX, size=22, weight=ft.FontWeight.BOLD),
            ft.Container(height=16),
            neon_card(ft.Column([
                section_header("یادداشت جدید", C_YE, ft.Icons.ADD_ROUNDED),
                ft.Container(height=8),
                ft.Row([note_field, date_field], spacing=12,
                       vertical_alignment=ft.CrossAxisAlignment.END),
                ft.Container(height=8),
                neon_btn("ذخیره یادداشت", save_note, C_YE, ft.Icons.SAVE_ROUNDED),
            ]), color=C_YE, padding=18),
            ft.Container(height=14),
            ft.Column(note_cards if note_cards else [
                ft.Text("هیچ یادداشتی ثبت نشده", color=C_TX2, size=12)
            ], spacing=10),
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

    # ── ALARM BACKGROUND THREAD ──────────────────

    def _start_alarm_thread(self):
        if self.alarm_running:
            return
        self.alarm_running = True

        def run():
            while self.alarm_running:
                try:
                    uid = self.current_user["id"] if self.current_user else None
                    created = db.check_and_create_alarms(uid)
                    if created > 0:
                        self._refresh_alarm_badge()
                        n = db.unread_count(uid)
                        if n > 0:
                            self._snack(f"{n} آلارم جدید دارید!", C_OR)
                except Exception as ex:
                    print(f"[Alarm] {ex}")
                time.sleep(60)

        threading.Thread(target=run, daemon=True).start()


def main(page: ft.Page):
    TaskManagerApp(page)


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8500, host="0.0.0.0")
