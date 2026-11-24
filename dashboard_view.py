"""
dashboard_view.py
داشبورد پیشرفته سامانه امور پرسنلی
طراحی شده برای Flet 0.28.x با انیمیشن‌های گرافیکی خفن

اصلاحات نسخه 2:
- ارتفاع یکسان همه کارت‌های بالا (155px)
- میله‌های بار چارت فشرده‌تر (spacing کمتر، width کمتر)
- مربع‌های heatmap دقیقاً 13px
- انیمیشن حلقه‌ها نرم‌تر (20 قدم، 0.10 ثانیه هر قدم)
- اسپینر فقط rotate می‌کند، scale نمی‌خورد (مشکل بزرگ شدن حلقه حل شد)
"""

import flet as ft
import threading
import time


class DashboardView:
    """
    یک کلاس مستقل برای نمایش داشبورد.
    برای استفاده در main.py:
        from dashboard_view import DashboardView
        dash = DashboardView(self.page, self, db, AppColors)
        self.content_area.content = dash.build()
        threading.Thread(target=dash.run_animations, args=(self.content_area,), daemon=True).start()
    """

    def __init__(self, page: ft.Page, app_controller, db, AppColors):
        self.page = page
        self.app = app_controller
        self.db = db
        self.AppColors = AppColors

        # ─── Animation state ─────────────────────────────────────
        self.dashboard_cards = []
        self.dashboard_bars = []
        self.dashboard_heatmap_squares = []
        self.dashboard_rings = []
        self.dashboard_remaining_pie = None
        self.dashboard_remaining_target_values = None
        self.dashboard_remaining_text = None
        # اسپینر: فقط rotate می‌کند، بدون scale
        self.dashboard_spinner_ring = None     # خود ProgressRing
        self.dashboard_allowed_pie = None
        self.dashboard_allowed_target_values = None

        # Build the view
        self._view = self._build()

    # ── Public interface ─────────────────────────────────────────
    def build(self):
        return self._view

    # ── Internal helpers ─────────────────────────────────────────
    def _wo(self, opacity, color):
        """with_opacity shorthand"""
        return ft.Colors.with_opacity(opacity, color)

    def _glass_card(self, content, padding=14, height=None, animate=True):
        """کارت شیشه‌ای پایه"""
        C = self.AppColors
        kwargs = dict(
            content=content,
            padding=padding,
            border_radius=8,
            bgcolor=self._wo(0.55, getattr(C, 'CARD_COLOR', '#1e2235')),
            border=ft.border.all(1, self._wo(0.12, ft.Colors.WHITE)),
            shadow=ft.BoxShadow(
                blur_radius=8,
                spread_radius=-4,
                color=self._wo(0.22, ft.Colors.BLACK),
                offset=ft.Offset(0, 6),
            ),
        )
        if height:
            kwargs['height'] = height
        if animate:
            kwargs['animate_opacity'] = ft.Animation(700, ft.AnimationCurve.EASE_IN_OUT)
            kwargs['animate_scale'] = ft.Animation(700, ft.AnimationCurve.DECELERATE)
            kwargs['opacity'] = 0.0
            kwargs['scale'] = ft.Scale(0.93)
        return ft.Container(**kwargs)

    def _section_title(self, icon, label, color=None):
        C = self.AppColors
        col = color or C.PRIMARY
        return ft.Row([
            ft.Container(
                content=ft.Icon(icon, color=col, size=15),
                width=28, height=28,
                bgcolor=self._wo(0.12, col),
                border_radius=7,
                alignment=ft.alignment.center,
            ),
            ft.Text(label, size=12, weight="bold",
                    font_family="IRANSans",
                    color=getattr(C, 'TEXT_BRIGHT', '#ffffff')),
        ], spacing=7)

    # ── Donut با اسپینر فقط rotate ─────────────────────────────────
    def _build_remaining_donut(self, rem_transferred, rem_current, total_allowed):
        C = self.AppColors
        
        # ─────────────────────────────────────────────────────────────────────────────
        # 📌 راهنمای تنظیمات ابعاد دایره پیشرفت (Donut):
        # SZ: قطر نهایی دایره دونات (بر حسب پیکسل). 
        # کاهش این مقدار از ۵۸ به ۴۶ باعث می‌شود تا دایره جمع‌وجورتر شده و فضای بالاییِ
        # کارت اولِ "مانده خالص" با بقیه کارت‌های آماری کاملاً هماهنگ شود و متن ساعت‌ها روی یک خط تراز گردد.
        # ─────────────────────────────────────────────────────────────────────────────
        SZ = 49  # اندازه قطر کل دایره (پیکسل) - کوچک‌تر شده جهت هم‌ترازی افقی ساعت‌ها


        # Pie sections
        if total_allowed > 0:
            sections = [
                ft.PieChartSection(value=1e-6, color=C.WARNING, radius=7, title="", badge=None),
                ft.PieChartSection(value=1e-6, color=C.SUCCESS, radius=7, title="", badge=None),
                ft.PieChartSection(value=float(total_allowed),
                                   color=self._wo(0.06, ft.Colors.WHITE),
                                   radius=7, title="", badge=None),
            ]
        else:
            sections = [ft.PieChartSection(
                value=1.0, color=self._wo(0.06, ft.Colors.WHITE),
                radius=7, title="", badge=None)]

        pie = ft.PieChart(
            sections=sections,
            sections_space=1.5,
            center_space_radius=19,
            expand=False,
            height=SZ, width=SZ,
        )
        self.dashboard_remaining_pie = pie
        self.dashboard_remaining_target_values = (
            float(rem_transferred), float(rem_current), float(total_allowed)
        )

        pct_text = ft.Text(
            "0%", size=10, weight="bold",
            color=C.PRIMARY, font_family="IRANSans",
            text_align=ft.TextAlign.CENTER,
        )
        self.dashboard_remaining_text = pct_text

        # ── اسپینر: یک ProgressRing که فقط opacity/rotate دارد، بدون scale ──
        # scale روی wrapper باعث می‌شد خود ring هم scale بخورد و بزرگ به نظر برسد.
        # راه‌حل: اسپینر را مستقیم در Stack قرار می‌دهیم؛ animate_opacity دارد اما animate_scale ندارد.
        spinner_ring = ft.ProgressRing(
            value=0.5,
            stroke_width=5.0,
            color=self._wo(0.75, C.PRIMARY),
            width=SZ + 20,
            height=SZ + 20,
        )
        self.dashboard_spinner_ring = spinner_ring

        spinner_container = ft.Container(
            content=spinner_ring,
            alignment=ft.alignment.center,
            width=SZ + 8, height=SZ + 8,
            # فقط opacity برای fade-in/out؛ بدون scale
            opacity=0.0,
            animate_opacity=ft.Animation(900, ft.AnimationCurve.EASE_IN_OUT),
            # rotate برای چرخش
            rotate=ft.Rotate(0.0, alignment=ft.alignment.center),
            animate_rotation=ft.Animation(1800, ft.AnimationCurve.DECELERATE),
        )
        self.dashboard_spinning_ring_container = spinner_container

        bg_track = ft.ProgressRing(
            value=1.0, stroke_width=7,
            color=self._wo(0.07, ft.Colors.WHITE),
            width=SZ, height=SZ,
        )

        stack = ft.Stack([
            ft.Container(content=bg_track, alignment=ft.alignment.center,
                         width=SZ + 8, height=SZ + 8),
            ft.Container(content=pie, alignment=ft.alignment.center,
                         width=SZ + 8, height=SZ + 8),
            spinner_container,
            ft.Container(content=pct_text, alignment=ft.alignment.center,
                         width=SZ + 8, height=SZ + 8),
        ], width=SZ + 8, height=SZ + 8)

        return ft.Container(
            content=stack,
            alignment=ft.alignment.center,
            width=SZ + 8, height=SZ + 8,
            border_radius=(SZ + 8) // 2,
            # ─────────────────────────────────────────────────────────────────────────────
            # 📌 راهنمای تنظیمات افکت درخشش دایره (Glow):
            # shadow: سایه پیش‌فرض اطراف دایره اصلی.
            # - blur_radius: پهنای پخش درخشش (هر چه کمتر باشد نور متمرکزتر و ملایم‌تر است؛ از ۵ به ۳ تغییر یافت).
            # - color: با کاهش غلظت رنگ به ۵٪ (0.05) هاله درخشش سبز دور دایره مهار و چشم‌نواز گردید.
            # ─────────────────────────────────────────────────────────────────────────────
            shadow=ft.BoxShadow(
                blur_radius=3,                  # میزان پراکندگی افکت سایه/درخشش
                color=self._wo(0.05, C.PRIMARY), # رنگ درخشش با اوپاسیتی بسیار ملایم ۵٪
                spread_radius=2,                # اندازه پیش‌گسترش افکت درخشش
            ),
        )

    # ── Allowed solid pie ─────────────────────────────────────────
    def _build_allowed_pie(self, transferred, entitlement_current, total_allowed):
        C = self.AppColors
        if total_allowed > 0:
            sections = [
                ft.PieChartSection(value=1e-6, color=C.WARNING, radius=23, title="", badge=None),
                ft.PieChartSection(value=1e-6, color=C.SUCCESS, radius=23, title="", badge=None),
                ft.PieChartSection(value=float(total_allowed),
                                   color=self._wo(0.06, ft.Colors.WHITE),
                                   radius=23, title="", badge=None),
            ]
        else:
            sections = [ft.PieChartSection(
                value=1.0, color=self._wo(0.06, ft.Colors.WHITE),
                radius=23, title="", badge=None)]

        pie = ft.PieChart(
            sections=sections,
            sections_space=1.5,
            center_space_radius=0,
            expand=False,
            height=50, width=50,
        )
        self.dashboard_allowed_pie = pie
        self.dashboard_allowed_target_values = (
            float(transferred), float(entitlement_current), float(total_allowed)
        )

        bg = ft.Container(
            width=50, height=50, border_radius=25,
            bgcolor=self._wo(0.06, ft.Colors.WHITE),
        )

        return ft.Stack([
            bg,
            ft.Container(content=pie, alignment=ft.alignment.center, width=50, height=50),
        ], width=50, height=50)

    # ── کارت مانده خالص ─────────────────────────────────────────
    def _build_remaining_card(self, rem_transferred, rem_current,
                               remaining_total, total_allowed):
        C = self.AppColors
        donut = self._build_remaining_donut(rem_transferred, rem_current, total_allowed)

        card = self._glass_card(
            ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.DONUT_LARGE_ROUNDED, color=C.PRIMARY, size=15),
                        width=28, height=28,
                        bgcolor=self._wo(0.12, C.PRIMARY),
                        border_radius=7,
                        alignment=ft.alignment.center,
                    ),
                    ft.Text("مانده خالص مرخصی", size=10, weight="bold",
                            font_family="IRANSans",
                            color=getattr(C, 'TEXT_BRIGHT', '#ffffff'),
                            expand=True),
                    donut,
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=3),
                ft.Text(f"{remaining_total} ساعت", size=18, weight="bold",
                        color=C.PRIMARY, font_family="IRANSans"),
                ft.Text("مجموع مانده قابل استفاده", size=8.5,
                        color=getattr(C, 'TEXT_DIM', '#888'), font_family="IRANSans"),
                ft.Divider(height=8, color=self._wo(0.08, ft.Colors.WHITE)),
                ft.Row([
                    ft.Column([
                        ft.Row([
                            ft.Container(width=5, height=5, bgcolor=C.WARNING, border_radius=2.5),
                            ft.Text("مانده سال قبل", size=7.5,
                                    color=getattr(C, 'TEXT_DIM', '#888'), font_family="IRANSans"),
                        ], spacing=3),
                        ft.Text(f"{rem_transferred} ساعت", size=10, weight="bold",
                                color=C.WARNING, font_family="IRANSans"),
                    ], spacing=1),
                    ft.Container(width=1, height=20, bgcolor=self._wo(0.1, ft.Colors.WHITE)),
                    ft.Column([
                        ft.Row([
                            ft.Container(width=5, height=5, bgcolor=C.SUCCESS, border_radius=2.5),
                            ft.Text("مانده سال جاری", size=7.5,
                                    color=getattr(C, 'TEXT_DIM', '#888'), font_family="IRANSans"),
                        ], spacing=3),
                        ft.Text(f"{rem_current} ساعت", size=10, weight="bold",
                                color=C.SUCCESS, font_family="IRANSans"),
                    ], spacing=1),
                ], spacing=4, alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            ], spacing=2),
            # ─────────────────────────────────────────────────────────────────────────────
            # 📌 راهنمای ابعاد کارت‌های ردیف اول (Stats Card Height):
            # height: تمام ۴ کارت آماری بالای صفحه به صورت کاملاً هم‌ارتفاع روی ۱۵۵ پیکسل قفل شده‌اند.
            # این کار باعث بقای هم‌ترازی افقی ستاره‌ای در صفحه می‌گردد. برای بلندتر کردن آن‌ها این متغیر را افزایش دهید.
            # ─────────────────────────────────────────────────────────────────────────────
            padding=12,
            height=165,   # ارتفاع ثابت برای تضمین کادربندی هم‌سطح
        )
        self.dashboard_cards.append(card)
        return card

    # ── کارت کل مجاز قرارداد ─────────────────────────────────────
    def _build_allowed_card(self, transferred, entitlement_current, total_allowed):
        C = self.AppColors
        pie_stack = self._build_allowed_pie(transferred, entitlement_current, total_allowed)

        card = self._glass_card(
            ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.VERIFIED_USER_ROUNDED, color=C.SUCCESS, size=15),
                        width=28, height=28,
                        bgcolor=self._wo(0.12, C.SUCCESS),
                        border_radius=7,
                        alignment=ft.alignment.center,
                    ),
                    ft.Text("کل مجاز قرارداد", size=10, weight="bold",
                            font_family="IRANSans",
                            color=getattr(C, 'TEXT_BRIGHT', '#ffffff'),
                            expand=True),
                    ft.Container(
                        content=pie_stack,
                        alignment=ft.alignment.center,
                        shadow=ft.BoxShadow(blur_radius=5,
                                            color=self._wo(0.3, C.SUCCESS),
                                            spread_radius=1),
                        border_radius=25,
                    ),
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=3),
                ft.Text(f"{total_allowed} ساعت", size=18, weight="bold",
                        color=C.SUCCESS, font_family="IRANSans"),
                ft.Text("کل تعهدات قانونی و انتقالی", size=8.5,
                        color=getattr(C, 'TEXT_DIM', '#888'), font_family="IRANSans"),
                ft.Divider(height=8, color=self._wo(0.08, ft.Colors.WHITE)),
                ft.Row([
                    ft.Column([
                        ft.Row([
                            ft.Container(width=5, height=5, bgcolor=C.WARNING, border_radius=2.5),
                            ft.Text("انتقالی سال قبل", size=7.5,
                                    color=getattr(C, 'TEXT_DIM', '#888'), font_family="IRANSans"),
                        ], spacing=3),
                        ft.Text(f"{transferred} ساعت", size=10, weight="bold",
                                color=C.WARNING, font_family="IRANSans"),
                    ], spacing=1),
                    ft.Container(width=1, height=20, bgcolor=self._wo(0.1, ft.Colors.WHITE)),
                    ft.Column([
                        ft.Row([
                            ft.Container(width=5, height=5, bgcolor=C.SUCCESS, border_radius=2.5),
                            ft.Text("مرخصی قانونی", size=7.5,
                                    color=getattr(C, 'TEXT_DIM', '#888'), font_family="IRANSans"),
                        ], spacing=3),
                        ft.Text(f"{round(entitlement_current, 2)} ساعت", size=10, weight="bold",
                                color=C.SUCCESS, font_family="IRANSans"),
                    ], spacing=1),
                ], spacing=4, alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            ], spacing=2),
            # ─────────────────────────────────────────────────────────────────────────────
            # 📌 راهنمای ابعاد کارت‌های ردیف اول (Stats Card Height):
            # height: تمام ۴ کارت آماری بالای صفحه به صورت کاملاً هم‌ارتفاع روی ۱۵۵ پیکسل قفل شده‌اند.
            # ─────────────────────────────────────────────────────────────────────────────
            padding=12,
            height=165,   # ارتفاع ثابت برای کارت‌های آماری
        )
        self.dashboard_cards.append(card)
        return card

    # ── کارت حلقه پیشرفت (StatCard) ─────────────────────────────
    def _build_stat_ring_card(self, title, value_text, icon, ring_color,
                               progress, bottom_left, bottom_right):
        C = self.AppColors

        ring = ft.ProgressRing(
            value=0.0,
            stroke_width=5,
            color=ring_color,
            bgcolor=self._wo(0.08, ring_color),
            width=50, height=50,
        )
        self.dashboard_rings.append((ring, min(1.0, max(0.0, progress))))

        card = self._glass_card(
            ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=ring_color, size=15),
                        width=28, height=28,
                        bgcolor=self._wo(0.12, ring_color),
                        border_radius=7,
                        alignment=ft.alignment.center,
                    ),
                    ft.Text(title, size=10, weight="bold",
                            font_family="IRANSans",
                            color=getattr(C, 'TEXT_BRIGHT', '#ffffff'),
                            expand=True),
                    ft.Stack([
                        ring,
                        ft.Container(
                            content=ft.Text(
                                f"{int(progress * 100)}%",
                                size=9, weight="bold",
                                color=ring_color, font_family="IRANSans",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            width=50, height=50,
                            alignment=ft.alignment.center,
                        ),
                    ], width=50, height=50),
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=3),
                ft.Text(value_text, size=18, weight="bold",
                        color=ring_color, font_family="IRANSans"),
                ft.Divider(height=8, color=self._wo(0.1, ft.Colors.WHITE)),
                ft.Row([
                    ft.Column([
                        ft.Text(bottom_left[0], size=7.5,
                                color=getattr(C, 'TEXT_DIM', '#888888'), font_family="IRANSans"),
                        ft.Text(bottom_left[1], size=10, weight="bold",
                                color=getattr(C, 'TEXT_BRIGHT', '#ffffff'), font_family="IRANSans"),
                    ], spacing=1, expand=True),
                    ft.Container(width=1, height=20, bgcolor=self._wo(0.1, ft.Colors.WHITE)),
                    ft.Column([
                        ft.Text(bottom_right[0], size=7.5,
                                color=getattr(C, 'TEXT_DIM', '#888888'), font_family="IRANSans"),
                        ft.Text(bottom_right[1], size=10, weight="bold",
                                color=getattr(C, 'TEXT_BRIGHT', '#ffffff'), font_family="IRANSans"),
                    ], spacing=1, expand=True),
                ], spacing=4),
            ], spacing=2),
            # ─────────────────────────────────────────────────────────────────────────────
            # 📌 راهنمای ابعاد کارت‌های ردیف اول (Stats Card Height):
            # height: تمام ۴ کارت آماری بالای صفحه به صورت کاملاً هم‌ارتفاع روی ۱۵۵ پیکسل قفل شده‌اند.
            # ─────────────────────────────────────────────────────────────────────────────
            padding=12,
            height=165,   # ارتفاع ثابت برای کارت‌های آماری ردیف اول
        )
        self.dashboard_cards.append(card)
        return card

    # ── بار چارت ─────────────────────────────────────────────────
    def _build_chart_card(self, months_list_data, month_names):
        C = self.AppColors
        max_hours = max([m["hours"] for m in months_list_data] + [10.0])
        
        # ─────────────────────────────────────────────────────────────────────────────
        # 📌 راهنمای تنظیمات ابعاد فرعی نمودار میله‌ای (Bar Chart):
        # - BAR_H: حداکثر ارتفاع فیزیکی ستون بر حسب پیکسل (از ۸۰ به ۱۰۰ افزایش یافته که ستون‌ها بزرگ‌تر و واضح‌تر شوند).
        # - BAR_W: پهنا / عرض تک‌تک ستون‌های قرارگیری ساعات مرخصی بر حسب پیکسل (۱۶ پیکسل).
        # - SPACING: فاصله افقی فیمابین ستون‌های ماه‌ها برای خوانایی عالی و پر کردن حجم خالی (۱۲ پیکسل).
        # ─────────────────────────────────────────────────────────────────────────────
        BAR_H = 120   # ارتفاع بهینه‌شده ستون‌ها برای نمایش بزرگتر و جذاب‌تر
        BAR_W = 22    # ضخامت ستون‌های نمودار
        SPACING = 10  # فاصله‌ی بین میله‌های نمودار


        bar_controls = []
        for m in months_list_data:
            pct = m["hours"] / max_hours
            fill_height = max(3, int(pct * BAR_H))

            bar_fill = ft.Container(
                bgcolor=C.PRIMARY,
                width=BAR_W,
                height=2,  # از 2 شروع می‌کند، انیمیشن بالا می‌رود
                border_radius=ft.border_radius.only(top_left=4, top_right=4),
                shadow=ft.BoxShadow(
                    blur_radius=7,
                    color=self._wo(0.45, C.PRIMARY),
                ),
                tooltip=f"{m['month_label']}: {m['hours']} ساعت",
                animate=ft.Animation(700, ft.AnimationCurve.DECELERATE),
            )
            self.dashboard_bars.append((bar_fill, fill_height))

            bar_track = ft.Stack([
                ft.Container(
                    width=BAR_W, height=BAR_H,
                    bgcolor=self._wo(0.05, ft.Colors.WHITE),
                    border_radius=4,
                ),
                ft.Container(
                    content=bar_fill,
                    alignment=ft.alignment.bottom_center,
                    width=BAR_W, height=BAR_H,
                ),
            ], alignment=ft.alignment.bottom_center)

            bar_controls.append(
                ft.Column([
                    ft.Text(
                        f"{m['hours']}س" if m['hours'] > 0 else "—",
                        size=8.5, font_family="IRANSans", weight="semibold",
                        color=getattr(C, 'TEXT_BRIGHT', '#ffffff'),
                    ),
                    ft.Container(height=2),
                    bar_track,
                    ft.Container(height=3),
                    ft.Text(
                        m["month_label"], size=8.5,
                        font_family="IRANSans",
                        color=getattr(C, 'TEXT_DIM', '#888888'),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            )

        card = self._glass_card(
            ft.Column([
                self._section_title(ft.Icons.AREA_CHART_ROUNDED, "میزان مرخصی در ۵ ماه اخیر"),
                ft.Text("مجموع ساعات مرخصی تایید شده هر ماه",
                        size=8.5, color=getattr(C, 'TEXT_DIM', '#888888'),
                        font_family="IRANSans"),
                ft.Container(height=2),
                ft.Row(
                    bar_controls,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=SPACING,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                ),
            ], expand=True, spacing=3), # فشرده‌سازی فاصله‌ها برای هماهنگی با کارت هیت‌مپ
            # ─────────────────────────────────────────────────────────────────────────────
            # 📌 راهنمای ابعاد اصلی کارت‌ها (Card Height):
            # ارتفاع کارت‌های ردیف دوم (کارت نمودار و کارت هیت‌مپ) همگی به شکل هماهنگ روی ۲۱۵ تنظیم شده‌اند
            # تا تقارن افقی صفحه کاملاً حفظ شده و فضاهای خالی ناهنجار بالا و پایین به حداقل برسند.
            # ─────────────────────────────────────────────────────────────────────────────
            padding=14,
            height=245,  # ارتفاع بهینه و هم‌سان با کارت هیت‌مپ جهت لغو فضاهای اضافی
        )
        self.dashboard_cards.append(card)
        return card

    # ── هیت‌مپ تقویم ─────────────────────────────────────────────
    def _build_heatmap_card(self, four_months, month_names):
        C = self.AppColors
        
        # ─────────────────────────────────────────────────────────────────────────────
        # 📌 راهنمای تنظیمات ابعاد مربع‌های تقویم حرارتی (Heatmap Calendar):
        # - SQ: طول و عرض هر خانه مربع در تقویم بر حسب پیکسل (دقیقاً ۱۳ پیکسل طبق خواسته‌ی شما).
        # - GAP: فاصله افقی و عمودی فیمابین مربع‌های روزهای ماه بر حسب پیکسل (۲ پیکسل برای حفظ توازن شبکه).
        # ─────────────────────────────────────────────────────────────────────────────
        SQ = 13   # سایز طول و عرض مربع‌های اختصاصی روزها
        GAP = 2   # فاصله‌ی خانه‌های تقویم از یکدیگر


        try:
            import jdatetime
        except ImportError:
            jdatetime = None

        all_month_cols = []
        for index, (ty, tm) in enumerate(four_months):
            num_days_tm = 31 if tm <= 6 else 30
            if tm == 12:
                num_days_tm = 29

            tm_start_str = f"{ty}-{tm:02d}-01"
            tm_end_str = f"{ty}-{tm:02d}-{num_days_tm}"

            leaves_this_tm = self.db.get_leaves_in_range(
                self.app.current_user['id'], tm_start_str, tm_end_str
            )

            day_hours_tm = {d: 0.0 for d in range(1, num_days_tm + 1)}
            for start_str, end_str, hrs_val, desc in leaves_this_tm:
                try:
                    sy, sm, sd = map(int, start_str.split('-'))
                    ey, em, ed = map(int, end_str.split('-'))
                    if sy == ty and sm == tm:
                        if sd == ed:
                            day_hours_tm[sd] += float(hrs_val)
                        else:
                            num_span_days = (ed - sd) + 1
                            hours_per_day = float(hrs_val) / num_span_days
                            for d_span in range(sd, ed + 1):
                                if d_span in day_hours_tm:
                                    day_hours_tm[d_span] += hours_per_day
                except Exception:
                    pass

            first_wday_tm = 0
            if jdatetime:
                try:
                    first_day_date = jdatetime.date(ty, tm, 1)
                    first_wday_tm = first_day_date.weekday()
                except Exception:
                    pass

            days_list_tm = [
                ft.Container(width=SQ, height=SQ, bgcolor=ft.Colors.TRANSPARENT)
                for _ in range(first_wday_tm)
            ]

            for d in range(1, num_days_tm + 1):
                h_val = day_hours_tm.get(d, 0.0)
                if h_val == 0.0:
                    sq_color = self._wo(0.05, ft.Colors.WHITE)
                    lbl_tag = "بدون مرخصی"
                elif h_val <= 2.0:
                    sq_color = self._wo(0.22, C.PRIMARY)
                    lbl_tag = f"{h_val:.1f} ساعت ساعتی"
                elif h_val <= 4.0:
                    sq_color = self._wo(0.48, C.PRIMARY)
                    lbl_tag = f"{h_val:.1f} ساعت"
                elif h_val <= 6.0:
                    sq_color = self._wo(0.72, C.PRIMARY)
                    lbl_tag = f"{h_val:.1f} ساعت"
                else:
                    sq_color = C.PRIMARY
                    lbl_tag = f"روز کامل ({h_val:.1f} ساعت)"

                tooltip_msg = f"{d} {month_names[tm]} - {lbl_tag}"

                day_sq = ft.Container(
                    width=SQ, height=SQ,
                    bgcolor=sq_color,
                    border_radius=3,
                    tooltip=tooltip_msg,
                    scale=ft.Scale(0.0),
                    animate_scale=ft.Animation(260, ft.AnimationCurve.DECELERATE),
                    shadow=ft.BoxShadow(
                        blur_radius=4,
                        color=self._wo(0.5, C.PRIMARY),
                    ) if h_val > 4 else None,
                )
                days_list_tm.append(day_sq)
                self.dashboard_heatmap_squares.append(day_sq)

            weeks_tm, current_week_tm = [], []
            for d_control in days_list_tm:
                current_week_tm.append(d_control)
                if len(current_week_tm) == 7:
                    weeks_tm.append(ft.Row(current_week_tm, spacing=GAP,
                                           alignment=ft.MainAxisAlignment.CENTER))
                    current_week_tm = []
            if current_week_tm:
                while len(current_week_tm) < 7:
                    current_week_tm.append(
                        ft.Container(width=SQ, height=SQ, bgcolor=ft.Colors.TRANSPARENT))
                weeks_tm.append(ft.Row(current_week_tm, spacing=GAP,
                                        alignment=ft.MainAxisAlignment.CENTER))

            wday_headers = ["ش", "ی", "د", "س", "چ", "پ", "ج"]
            header_row_tm = ft.Row(
                [
                    ft.Container(
                        content=ft.Text(d, size=7,
                                        color=getattr(C, 'TEXT_DIM', '#888'),
                                        weight="bold", font_family="IRANSans"),
                        width=SQ, height=SQ,
                        alignment=ft.alignment.center,
                    )
                    for d in wday_headers
                ],
                spacing=GAP,
                alignment=ft.MainAxisAlignment.CENTER,
            )

            month_col = ft.Column([
                ft.Text(month_names[tm], size=9.5, weight="bold",
                        font_family="IRANSans", color=C.PRIMARY),
                ft.Container(height=2),
                header_row_tm,
                ft.Column(weeks_tm, spacing=GAP,
                           alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1)

            all_month_cols.append(month_col)
            if index < 3:
                all_month_cols.append(
                    ft.Container(
                        width=1, height=85,
                        bgcolor=self._wo(0.08, ft.Colors.WHITE),
                    )
                )

        heatmap_row = ft.Row(
            all_month_cols,
            spacing=10,
            scroll=ft.ScrollMode.ADAPTIVE,
            vertical_alignment=ft.CrossAxisAlignment.START,
            alignment=ft.MainAxisAlignment.START,
        )

        legend = ft.Row([
            ft.Text("کمتر", size=7.5, color=getattr(C, 'TEXT_DIM', '#888'), font_family="IRANSans"),
            *[
                ft.Container(
                    width=7, height=7, bgcolor=col, border_radius=2,
                    shadow=ft.BoxShadow(blur_radius=4,
                                        color=self._wo(0.5, C.PRIMARY)) if i > 2 else None,
                )
                for i, col in enumerate([
                    self._wo(0.05, ft.Colors.WHITE),
                    self._wo(0.25, C.PRIMARY),
                    self._wo(0.55, C.PRIMARY),
                    C.PRIMARY,
                ])
            ],
            ft.Text("بیشتر", size=7.5, color=getattr(C, 'TEXT_DIM', '#888'), font_family="IRANSans"),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=5)

        card = self._glass_card(
            ft.Column([
                self._section_title(ft.Icons.CALENDAR_MONTH_ROUNDED, "تقویم مرخصی‌های ۴ ماه اخیر"),
                ft.Text("توزیع روزانه مرخصی‌ها", size=8.5,
                        color=getattr(C, 'TEXT_DIM', '#888'), font_family="IRANSans"),
                # ─────────────────────────────────────────────────────────────────────────────
                # 📌 برطرف‌سازی مشکل فاصله زیاد:
                # - جهت بالا کشیدن تقویم، فاصله‌ی عمومیِ (spacing) ستون اصلی روی ۲ تنظیم شد و
                #   کانتینرهای اضافی حذف شدند تا تقویم کاملاً بالاتر آید و فاصله‌ی اضافی حذف شود.
                # ─────────────────────────────────────────────────────────────────────────────
                ft.Container(
                    content=heatmap_row,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    padding=ft.padding.symmetric(vertical=2, horizontal=1),
                    margin=ft.Margin(left=0, top=-15, right=0, bottom=0),
                ),
                legend,
            ], expand=True, spacing=15), # تنظیم اسپیسینگ ستون به ۲ جهت فشرده‌سازی و بالا رفتن تقویم
            # ─────────────────────────────────────────────────────────────────────────────
            # 📌 راهنمای ابعاد اصلی کارت‌ها (Card Height):
            # ارتفاع هر دو کارت پایین به صورت متقارن روی ۲۱۵ تنظیم شده تا توازن بصری زیبا مهیا گردد.
            # ─────────────────────────────────────────────────────────────────────────────
            padding=14,
            height=245,                         # ارتفاع یکپارچه و بهینه‌شده برای حذف فضاهای مرده
        )
        self.dashboard_cards.append(card)
        return card

    # ── دسترسی سریع ──────────────────────────────────────────────
    def _build_quick_jump_card(self):
        C = self.AppColors

        def quick_jump(target):
            for i, (name, _) in enumerate(self.app.sidebar.menu_items_data):
                if name == target:
                    self.app.sidebar.select_menu(i)
                    self.app.navigate_to(target, i)
                    break

        def _btn(label, icon, target, color=None):
            col = color or C.PRIMARY
            return ft.Container(
                content=ft.Row([
                    ft.Icon(icon, color=col, size=14),
                    ft.Text(label, size=12, weight="bold",
                            color=col, font_family="IRANSans"),
                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.symmetric(vertical=10, horizontal=18),
                border_radius=12,
                bgcolor=self._wo(0.10, col),
                border=ft.border.all(1, self._wo(0.30, col)),
                on_click=lambda e, t=target: quick_jump(t),
                ink=True,
                shadow=ft.BoxShadow(blur_radius=10, color=self._wo(0.20, col)),
                expand=True,
            )

        card = self._glass_card(
            ft.Column([
                self._section_title(ft.Icons.BOLT_ROUNDED, "دسترسی سریع",
                                    color=getattr(C, 'WARNING', '#f5a623')),
                ft.Container(height=8),
                ft.Row([
                    _btn("ثبت مرخصی", ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, "مرخصی‌ها"),
                    _btn("کارتابل", ft.Icons.FACT_CHECK_ROUNDED,
                         "کارتابل", getattr(C, 'WARNING', '#f5a623')),
                    _btn("گزارشات", ft.Icons.ANALYTICS_ROUNDED,
                         "گزارشات", getattr(C, 'SUCCESS', '#43e97b')),
                ], spacing=10),
            ], spacing=4),
            padding=14,
        )
        self.dashboard_cards.append(card)
        return card

    # ── ساخت اصلی داشبورد ─────────────────────────────────────────
    def _build(self):
        try:
            import jdatetime
        except ImportError:
            jdatetime = None

        C = self.AppColors
        db = self.db
        current_user = self.app.current_user

        # ── Data ─────────────────────────────────────────────────
        leave_data = db.calculate_leave_balance(current_user['id'], return_extended=True)

        transferred       = leave_data.get('transferred', 0.0)
        used_current      = leave_data.get("used_current", 0.0)
        remaining_total   = leave_data.get("remaining", 0.0)
        total_allowed     = leave_data.get("total_allowed", 0.0)
        total_used_lifetime = leave_data.get('total_used_lifetime', 0.0)

        rem_transferred = round(max(0.0, transferred - used_current), 2)
        rem_current     = round(max(0.0, remaining_total - rem_transferred), 2)

        progress_used     = (min(1.0, max(0.0, float(used_current) / float(total_allowed)))
                             if total_allowed > 0 else 0.0)
        progress_lifetime = min(1.0, max(0.0, float(total_used_lifetime) / 120.0))
        entitlement_current_year = max(0.0, total_allowed - transferred)

        month_names = [
            "", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
        ]

        if jdatetime:
            try:
                today = jdatetime.date.today()
                year, month = today.year, today.month
            except Exception:
                import datetime; today = datetime.date.today()
                year, month = today.year, today.month
        else:
            import datetime; today = datetime.date.today()
            year, month = today.year, today.month

        # ── داده ماه‌ها برای بار چارت ─────────────────────────────
        months_list_data = []
        for i in range(4, -1, -1):
            target_month = month - i
            target_year = year
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            start_date_str = f"{target_year}-{target_month:02d}-01"
            end_day = 31 if target_month <= 6 else 30
            if target_month == 12:
                end_day = 29
            end_date_str = f"{target_year}-{target_month:02d}-{end_day}"
            q = ("SELECT SUM(Hours) FROM LeaveRequests "
                 "WHERE EmployeeID=? AND Status='approved' "
                 "AND StartDate >= ? AND StartDate <= ?")
            res = db.execute_query(q, (current_user['id'], start_date_str, end_date_str), fetch=True)
            hours = res[0][0] if res and res[0][0] else 0.0
            months_list_data.append({"month_label": month_names[target_month],
                                      "hours": round(hours, 1)})

        # ── ماه‌های هیت‌مپ ────────────────────────────────────────
        four_months = []
        for i in range(3, -1, -1):
            tm = month - i
            ty = year
            while tm <= 0:
                tm += 12; ty -= 1
            four_months.append((ty, tm))

        # ── ساخت کارت‌ها ──────────────────────────────────────────
        remaining_card = self._build_remaining_card(
            rem_transferred, rem_current, remaining_total, total_allowed)

        used_card = self._build_stat_ring_card(
            "استفاده شده در سال جاری",
            f"{used_current} ساعت",
            ft.Icons.TIMELAPSE_ROUNDED,
            "#f5576c",
            progress_used,
            ("سقف سال جاری", f"{total_allowed} س"),
            ("سهم مصرف", f"{progress_used * 100:.1f}%"),
        )

        allowed_card = self._build_allowed_card(
            transferred, entitlement_current_year, total_allowed)

        lifetime_card = self._build_stat_ring_card(
            "کل استفاده شده (سابقه)",
            f"{total_used_lifetime} ساعت",
            ft.Icons.HISTORY_ROUNDED,
            getattr(C, 'DANGER', '#e74c3c'),
            progress_lifetime,
            ("مجموع تایید", f"{total_used_lifetime} س"),
            ("وضعیت سابقه", "فعال / معتبر"),
        )

        chart_card = self._build_chart_card(months_list_data, month_names)
        heatmap_card = self._build_heatmap_card(four_months, month_names)
        quick_card = self._build_quick_jump_card()

        # ── Grid کارت‌های بالا ───────────────────────────────────
        stats_grid = ft.ResponsiveRow([
            ft.Column(col={"xs": 12, "sm": 6, "md": 3}, controls=[remaining_card]),
            ft.Column(col={"xs": 12, "sm": 6, "md": 3}, controls=[used_card]),
            ft.Column(col={"xs": 12, "sm": 6, "md": 3}, controls=[allowed_card]),
            ft.Column(col={"xs": 12, "sm": 6, "md": 3}, controls=[lifetime_card]),
        ], spacing=12)

        # ── هدر صفحه ─────────────────────────────────────────────
        try:
            if jdatetime:
                jd = jdatetime.date.today()
                date_str = f"{jd.year}/{jd.month:02d}/{jd.day:02d}"
            else:
                date_str = ""
        except Exception:
            date_str = ""

        greeting_text = self._get_greeting(current_user.get('name', ''))

        header_row = ft.Row([
            ft.Column([
                ft.Text(greeting_text, size=21, weight="bold",
                        font_family="IRANSans",
                        color=getattr(C, 'TEXT_BRIGHT', '#ffffff')),
                ft.Text(f"نمای کلی وضعیت مرخصی • {date_str}",
                        size=11, color=getattr(C, 'TEXT_DIM', '#888'),
                        font_family="IRANSans"),
            ], spacing=2, expand=True),
            ft.Container(
                content=ft.Row([
                    ft.Container(width=7, height=7, bgcolor=C.SUCCESS,
                                 border_radius=3.5,
                                 shadow=ft.BoxShadow(blur_radius=6,
                                                     color=self._wo(0.7, C.SUCCESS))),
                    ft.Text("آنلاین", size=10, color=C.SUCCESS, font_family="IRANSans"),
                ], spacing=5),
                padding=ft.padding.symmetric(vertical=5, horizontal=10),
                border_radius=20,
                bgcolor=self._wo(0.10, C.SUCCESS),
                border=ft.border.all(1, self._wo(0.25, C.SUCCESS)),
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
           vertical_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Column([
            header_row,
            ft.Divider(color="transparent", height=10),
            stats_grid,
            ft.Divider(color="transparent", height=10),
            ft.ResponsiveRow([
                ft.Column(col={"xs": 12, "md": 5}, controls=[chart_card]),
                ft.Column(col={"xs": 12, "md": 7}, controls=[heatmap_card]),
            ], spacing=12),
            ft.Divider(color="transparent", height=10),
            quick_card,
            ft.Container(height=14),
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

    # ── تشخیص سلام ──────────────────────────────────────────────
    @staticmethod
    def _get_greeting(name):
        try:
            import datetime
            h = datetime.datetime.now().hour
            if h < 12:   prefix = "صبح بخیر"
            elif h < 17: prefix = "ظهر بخیر"
            else:        prefix = "عصر بخیر"
        except Exception:
            prefix = "خوش آمدید"
        return f"{prefix}، {name}" if name else prefix

    # ── اجرای انیمیشن‌ها ─────────────────────────────────────────
    def run_animations(self, content_area):
        """
        باید در thread جداگانه فراخوانی شود:
            threading.Thread(target=dash.run_animations, args=(self.content_area,), daemon=True).start()
        """
        try:
            time.sleep(0.20)   # صبر برای رندر اولیه

            # ── مرحله ۱: fade/scale کارت‌ها (staggered) ─────────
            for card in self.dashboard_cards:
                try:
                    card.opacity = 1.0
                    card.scale = ft.Scale(1.0)
                    content_area.update()
                    time.sleep(0.07)
                except Exception:
                    pass

            time.sleep(0.08)

            # ── مرحله ۲: ظاهر شدن اسپینر (فقط fade-in و rotate، بدون scale) ──
            sc = self.dashboard_spinning_ring_container
            if sc:
                sc.opacity = 1.0
                sc.rotate = ft.Rotate(1.57, alignment=ft.alignment.center)
                content_area.update()
                time.sleep(0.20)

            # ── مرحله ۳: پر کردن donut باقی‌مانده ───────────────
            if self.dashboard_remaining_pie and self.dashboard_remaining_target_values:
                v_t, v_c, v_tot = self.dashboard_remaining_target_values
                secs = self.dashboard_remaining_pie.sections
                if len(secs) >= 3 and v_tot > 0:
                    secs[0].value = v_t
                    secs[1].value = v_c
                    secs[2].value = max(1e-6, v_tot - v_t - v_c)
                    if self.dashboard_remaining_text:
                        pct = int(((v_t + v_c) / v_tot) * 100)
                        self.dashboard_remaining_text.value = f"{pct}%"
                content_area.update()

            # ── مرحله ۴: پر کردن pie کل مجاز ────────────────────
            if self.dashboard_allowed_pie and self.dashboard_allowed_target_values:
                v_tr, v_ent, v_tot = self.dashboard_allowed_target_values
                secs = self.dashboard_allowed_pie.sections
                if len(secs) >= 3 and v_tot > 0:
                    secs[0].value = v_tr
                    secs[1].value = v_ent
                    secs[2].value = max(1e-6, v_tot - v_tr - v_ent)
                content_area.update()

            time.sleep(0.10)

            # ── مرحله ۵: حلقه‌های پیشرفت — نرم، 20 قدم، هر قدم 0.10 ثانیه ──
            # کل مدت: ~2.0 ثانیه برای دیدن کامل انیمیشن
            STEPS = 20
            for step in range(1, STEPS + 1):
                fraction = step / STEPS
                for ring, target_val in self.dashboard_rings:
                    ring.value = target_val * fraction
                content_area.update()
                time.sleep(0.10)

            # ── مرحله ۶: خروج اسپینر (fade-out + چرخش بیشتر) ───
            if sc:
                sc.opacity = 0.0
                sc.rotate = ft.Rotate(6.28, alignment=ft.alignment.center)
                content_area.update()

            # ── مرحله ۷: بالا رفتن میله‌های بار چارت ────────────
            for bar_fill, final_h in self.dashboard_bars:
                bar_fill.height = final_h
            content_area.update()

            time.sleep(0.15)

            # ── مرحله ۸: pop مربع‌های هیت‌مپ (cascade در ۵ دسته) ──
            num_sq = len(self.dashboard_heatmap_squares)
            if num_sq:
                batch_size = max(1, num_sq // 5)
                for b in range(5):
                    time.sleep(0.10)
                    start_idx = b * batch_size
                    end_idx = min(num_sq, (b + 1) * batch_size)
                    for idx in range(start_idx, end_idx):
                        self.dashboard_heatmap_squares[idx].scale = ft.Scale(1.0)
                    content_area.update()

        except Exception as e:
            print(f"DashboardView.run_animations error (safe): {e}")
