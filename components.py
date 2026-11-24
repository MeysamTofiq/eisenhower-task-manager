
import flet as ft
import colorsys
import threading
import contextvars
import inspect

try:
    from flet.core.dropdown import Option
except ImportError:
    from flet import dropdown
    Option = dropdown.Option

import jdatetime
from database import ConfigManager, db

# Thread-local and Context-local page references to track multi-session Flet pages
_thread_local = threading.local()
_page_context = contextvars.ContextVar("flet_page", default=None)

def set_active_page(page):
    _thread_local.active_page = page
    _page_context.set(page)

def get_active_page():
    # 1. Inspect call stack to find any page or object with a page (most accurate for concurrent rendering/callbacks)
    try:
        for frame_info in inspect.stack():
            frame = frame_info.frame
            if 'page' in frame.f_locals:
                val = frame.f_locals['page']
                if isinstance(val, ft.Page):
                    return val
            if 'self' in frame.f_locals:
                val = frame.f_locals['self']
                if hasattr(val, 'page') and isinstance(val.page, ft.Page):
                    return val.page
                if isinstance(val, ft.Page):
                    return val
    except Exception:
        pass

    # 2. Try contextvar
    try:
        p = _page_context.get()
        if p:
            return p
    except Exception:
        pass

    # 3. Try thread local
    try:
        p = getattr(_thread_local, "active_page", None)
        if p:
            return p
    except Exception:
        pass

    return None

def get_contrast_color(hex_color):
    try:
        hex_color = str(hex_color).strip().replace("#", "")
        if len(hex_color) == 3:
            hex_color = "".join([c*2 for c in hex_color])
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            luma = 0.299 * r + 0.587 * g + 0.114 * b
            return "black" if luma > 128 else "white"
    except Exception:
        pass
    return "white"

class AppColorsMeta(type):
    _fallbacks = {
        'col_primary': "#00FFFF",
        'col_bg': "#050508",
        'col_sidebar': "#080810",
        'col_success': "#00FF99",
        'col_warning': "#FFD700",
        'col_danger': "#FF0055",
        'col_card': "#101018",
        'col_text': "#FFFFFF"
    }

    def get_color(cls, key, default):
        return cls._fallbacks.get(key, default)

    def set_color(cls, key, value):
        cls._fallbacks[key] = value

    @property
    def PRIMARY(cls):
        return cls.get_color('col_primary', "#00FFFF")

    @PRIMARY.setter
    def PRIMARY(cls, value):
        cls.set_color('col_primary', value)

    @property
    def DARK_BG(cls):
        return cls.get_color('col_bg', "#050508")

    @DARK_BG.setter
    def DARK_BG(cls, value):
        cls.set_color('col_bg', value)

    @property
    def SIDEBAR_BG(cls):
        return cls.get_color('col_sidebar', "#080810")

    @SIDEBAR_BG.setter
    def SIDEBAR_BG(cls, value):
        cls.set_color('col_sidebar', value)

    @property
    def SUCCESS(cls):
        return cls.get_color('col_success', "#00FF99")

    @SUCCESS.setter
    def SUCCESS(cls, value):
        cls.set_color('col_success', value)

    @property
    def WARNING(cls):
        return cls.get_color('col_warning', "#FFD700")

    @WARNING.setter
    def WARNING(cls, value):
        cls.set_color('col_warning', value)

    @property
    def DANGER(cls):
        return cls.get_color('col_danger', "#FF0055")

    @DANGER.setter
    def DANGER(cls, value):
        cls.set_color('col_danger', value)

    @property
    def CARD_COLOR(cls):
        return cls.get_color('col_card', "#101018")

    @CARD_COLOR.setter
    def CARD_COLOR(cls, value):
        cls.set_color('col_card', value)

    @property
    def TEXT_DIM(cls):
        contrast = get_contrast_color(cls.CARD_COLOR)
        return "#64748B" if contrast == "black" else "#94A3B8"

    @property
    def ON_PRIMARY(cls):
        return "#FFFFFF"

    @property
    def SECONDARY(cls):
        contrast = get_contrast_color(cls.CARD_COLOR)
        return "#475569" if contrast == "black" else "#CBD5E1"

    @property
    def TERTIARY(cls):
        return "#7D5260"

    @property
    def SURFACE_VARIANT(cls):
        return "#1A1A2E"

    @property
    def ON_SURFACE_VARIANT(cls):
        return "#E0E0E0"

    @property
    def TEXT_BRIGHT(cls):
        return cls.get_color('col_text', ft.Colors.WHITE)

    @TEXT_BRIGHT.setter
    def TEXT_BRIGHT(cls, value):
        cls.set_color('col_text', value)

    @property
    def INPUT_BG(cls):
        contrast = get_contrast_color(cls.CARD_COLOR)
        return "#FCFCFC" if contrast == "black" else ft.Colors.WHITE10

    @property
    def INPUT_BORDER(cls):
        contrast = get_contrast_color(cls.CARD_COLOR)
        return "#CCCCCC" if contrast == "black" else ft.Colors.TRANSPARENT

class AppColors(metaclass=AppColorsMeta):
    @classmethod
    def load_theme(cls, page):
        if page:
            set_active_page(page)

    @classmethod
    def refresh_theme(cls):
        pass

class CrazySidebar(ft.Container):
    def __init__(self, page, menu_items, on_change):
        super().__init__()
        self.page_ref = page
        self.menu_items_data = menu_items
        self.on_change = on_change
        self.width = 210
        self.bgcolor = AppColors.SIDEBAR_BG
        self.border = ft.Border(left=ft.BorderSide(1, ft.Colors.WHITE10))
        self.padding = 0
        self.item_height = 60
        self.item_spacing = 10
        self.indicator_height = 40
        self.top_offset = 115 
        
        self.active_indicator = ft.Container(
            width=4, height=self.indicator_height, bgcolor=AppColors.PRIMARY, right=5, top=self.top_offset, 
            border_radius=5,
            animate_position=ft.Animation(500, ft.AnimationCurve.EASE_OUT_BACK),
            shadow=ft.BoxShadow(blur_radius=20, color=AppColors.PRIMARY, offset=ft.Offset(-5, 0)),
        )
        self.menu_col = ft.Column(spacing=self.item_spacing)
        self.build_menu()
        self.content = ft.Stack([
            self.active_indicator,
            ft.Column([
                ft.Container(height=40),
                ft.Container(
                    content=ft.Text("منوی اصلی سیستم", color=AppColors.PRIMARY, size=11, weight=ft.FontWeight.BOLD, opacity=0.5),
                    padding=ft.Padding(0, 0, 30, 0), height=30
                ),
                ft.Container(height=15), 
                self.menu_col
            ])
        ])

    def build_menu(self):
        for i, (name, icon) in enumerate(self.menu_items_data):
            btn = ft.Container(
                content=ft.Row([
                    ft.Icon(icon, color=AppColors.TEXT_DIM, size=24),
                    ft.Text(name, color=AppColors.TEXT_DIM, size=13, weight=ft.FontWeight.NORMAL),
                ], spacing=10),
                padding=ft.Padding(10, 0, 10, 0), height=self.item_height, width=190,
                border_radius=15, on_click=lambda e, idx=i: self.select_menu(idx),
                animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
                animate_scale=ft.Animation(300, ft.AnimationCurve.DECELERATE),
                border=None, bgcolor=ft.Colors.TRANSPARENT, data=i 
            )
            self.menu_col.controls.append(btn)

    def select_menu(self, index):
        new_top = self.top_offset + (index * (self.item_height + self.item_spacing)) + (self.item_height - self.indicator_height) / 2
        self.active_indicator.top = new_top
        for i, item in enumerate(self.menu_col.controls):
            is_selected = (i == index)
            icon_control = item.content.controls[0]
            text_control = item.content.controls[1]
            icon_control.color = AppColors.PRIMARY if is_selected else AppColors.TEXT_DIM
            text_control.color = AppColors.TEXT_BRIGHT if is_selected else AppColors.TEXT_DIM
            text_control.weight = ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL
            if is_selected:
                item.bgcolor = ft.Colors.with_opacity(0.05, AppColors.PRIMARY)
                side = ft.BorderSide(1, AppColors.PRIMARY)
                item.border = ft.Border(top=side, bottom=side, left=side, right=side)
                item.shadow = ft.BoxShadow(blur_radius=1, color=ft.Colors.with_opacity(0.2, AppColors.PRIMARY))
                item.width = 180 
            else:
                item.bgcolor = ft.Colors.TRANSPARENT
                item.border = None
                item.shadow = None
                item.width = 190
        self.active_indicator.bgcolor = AppColors.PRIMARY
        self.active_indicator.shadow.color = AppColors.PRIMARY
        self.update()
        self.on_change(index)

class GlassCard(ft.Card):
    def __init__(self, content, width=None, height=None, padding=20, tooltip=None, animate_on_load=False):
        super().__init__()
        self.variant = "elevated" 
        self.elevation = 0 
        self.color = AppColors.CARD_COLOR
        self.tooltip = tooltip
        side = ft.BorderSide(1, ft.Colors.WHITE10)
        safe_border = ft.Border(top=side, bottom=side, left=side, right=side)
        self.content = ft.Container(
            content=content, padding=padding, width=width, height=height,
            border_radius=12, border=safe_border, 
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            opacity=0.0 if animate_on_load else 1.0,
            scale=0.92 if animate_on_load else 1.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.DECELERATE),
            animate_scale=ft.Animation(500, ft.AnimationCurve.DECELERATE)
        )

class StatCard(GlassCard):
    def __init__(self, title, value, icon_name, color, progress_value=0.0, bottom_left=None, bottom_right=None, animate_on_load=False):
        self.target_progress = float(progress_value) if progress_value is not None else 0.0
        
        # Elegant progress ring surrounding the icon in a stack (starts flat at 0.0 for premium animate loading)
        self.ring = ft.ProgressRing(
            value=0.0 if animate_on_load else self.target_progress,
            stroke_width=3.5,
            color=color,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
            width=42,
            height=42,
        )
        
        icon_and_ring = ft.Stack([
            ft.Container(
                content=self.ring,
                alignment=ft.alignment.center
            ),
            ft.Container(
                content=ft.Icon(icon_name, color=color, size=18),
                alignment=ft.alignment.center
            )
        ], width=42, height=42)

        cc = ft.Column([
            ft.Row([
                ft.Icon(icon_name, color=ft.Colors.with_opacity(0.5, color), size=14),
                ft.Text(title, size=11, color=AppColors.TEXT_DIM, font_family="IRANSans"),
            ], spacing=6),
            ft.Container(height=2),
            ft.Row([
                ft.Column([
                    ft.Text(value, size=20, weight="bold", color=AppColors.TEXT_BRIGHT, font_family="IRANSans"),
                    ft.Text("بروزرسانی شده", size=9, color=AppColors.TEXT_DIM, font_family="IRANSans")
                ], spacing=1, expand=True),
                ft.Container(
                    content=icon_and_ring,
                    alignment=ft.alignment.center
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Divider(height=10, color=ft.Colors.WHITE10),
            ft.Row([
                ft.Column([
                    ft.Text(bottom_left[0] if bottom_left else "", size=8, color=AppColors.TEXT_DIM, font_family="IRANSans"),
                    ft.Text(bottom_left[1] if bottom_left else "", size=10, weight="bold", color=AppColors.TEXT_BRIGHT, font_family="IRANSans")
                ], spacing=1, expand=True),
                ft.Container(width=1, height=18, bgcolor=ft.Colors.WHITE10),
                ft.Column([
                    ft.Text(bottom_right[0] if bottom_right else "", size=8, color=AppColors.TEXT_DIM, font_family="IRANSans"),
                    ft.Text(bottom_right[1] if bottom_right else "", size=10, weight="bold", color=AppColors.TEXT_BRIGHT, font_family="IRANSans")
                ], spacing=1, expand=True),
            ], spacing=4, alignment=ft.MainAxisAlignment.SPACE_EVENLY)
        ], spacing=2)

        super().__init__(content=cc, padding=12, height=135, animate_on_load=animate_on_load)

class NeonButton(ft.ElevatedButton):
    def __init__(self, text, icon, on_click, width=None, color=None):
        super().__init__()
        self.on_click = on_click
        self.width = width
        base_color = color if color else AppColors.PRIMARY
        contrast_color = get_contrast_color(base_color)
        self.content = ft.Row(
            [
                ft.Icon(icon, color=contrast_color),
                ft.Text(text, color=contrast_color, weight="bold")
            ],
            alignment=ft.MainAxisAlignment.CENTER, spacing=10
        )
        self.style = ft.ButtonStyle(
            bgcolor=base_color, shape=ft.RoundedRectangleBorder(radius=10),
            padding=15, shadow_color=base_color, elevation=5
        )

class EmployeeCard(ft.Card):
    def __init__(self, emp_data, on_edit, on_delete, can_delete=False, stats=None):
        super().__init__()
        # [0]=ID [1]=Name [2]=Code [3]=Dept [4]=Join [5]=End [6]=Role [7]=Active [8]=ImgPath [9]=Phone
        emp_data_9 = emp_data[:9]
        emp_id, name, code, dept, join, end, role, is_active, img_path = emp_data_9
        is_active = (is_active == 1)
        
        is_expired = False
        expired_text = ""
        if end and str(end).strip().lower() not in ['none', 'nan', '', '---']:
            try:
                p = str(end).split('-')
                end_date = jdatetime.date(int(p[0]), int(p[1]), int(p[2]))
                if end_date < jdatetime.date.today():
                    is_expired = True
                    expired_text = " (منقضی)"
            except: pass

        if not is_active:
            card_border_color = ft.Colors.GREY_800
            active_indicator_color = ft.Colors.GREY_600
            text_color = ft.Colors.GREY_500
            sub_text_color = ft.Colors.GREY_700
            icon_color = ft.Colors.GREY_700
            avatar_bg = ft.Colors.GREY_800
            avatar_fg = ft.Colors.GREY_400
        else:
            text_color = AppColors.TEXT_BRIGHT
            sub_text_color = AppColors.TEXT_DIM
            if is_expired:
                card_border_color = AppColors.DANGER
                active_indicator_color = AppColors.DANGER
                icon_color = AppColors.DANGER
                avatar_bg = AppColors.DANGER
                avatar_fg = "white"
            else:
                card_border_color = ft.Colors.WHITE10
                active_indicator_color = AppColors.SUCCESS
                icon_color = AppColors.TEXT_DIM
                avatar_bg = AppColors.PRIMARY
                avatar_fg = get_contrast_color(AppColors.PRIMARY)

        avatar_content = ft.Text(name[0] if name else "?", size=20, weight="bold", color=avatar_fg)
        if img_path:
            avatar = ft.CircleAvatar(
                # FIX: Set border_radius directly on Image to clip it
                content=ft.Image(src=img_path, fit=ft.ImageFit.COVER, border_radius=50),
                radius=25, bgcolor=ft.Colors.TRANSPARENT
            )
        else:
            avatar = ft.CircleAvatar(content=avatar_content, radius=25, bgcolor=avatar_bg)
        
        menu_items = [ft.PopupMenuItem(text="ویرایش", icon=ft.Icons.EDIT, on_click=lambda _: on_edit(emp_data))]
        if can_delete:
            menu_items.append(ft.PopupMenuItem(text="حذف", icon=ft.Icons.DELETE, on_click=lambda _: on_delete(emp_id)))

        stats_row = ft.Container()
        if stats:
             stats_row = ft.Row([
                 ft.Text(f"مصرف: {stats[0]}", size=10, color=sub_text_color),
                 ft.Text(f"مانده: {stats[1]}", size=10, color=AppColors.SUCCESS if (is_active and stats[1] > 0) else sub_text_color)
             ], spacing=5)

        self.color = AppColors.CARD_COLOR
        side = ft.BorderSide(1, card_border_color)
        safe_border = ft.Border(top=side, bottom=side, left=side, right=side)
        end_date_display = f"{end}{expired_text}" if end else "---"

        self.content = ft.Container(
            padding=10, border_radius=12, border=safe_border,
            content=ft.Row([
                avatar,
                ft.VerticalDivider(width=10, color="transparent"),
                ft.Column([
                    ft.Text(name, weight="bold", size=14, font_family="IRANSans", color=text_color),
                    ft.Row([ft.Text(f"{dept} | {code}", size=11, color=sub_text_color, font_family="IRANSans")], spacing=5),
                    ft.Row([
                         ft.Icon(ft.Icons.DATE_RANGE, size=12, color=icon_color),
                         ft.Text(f"پایان: {end_date_display}", size=10, color=icon_color, font_family="IRANSans"),
                         stats_row
                    ], spacing=5)
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CIRCLE, size=10, color=active_indicator_color),
                ft.PopupMenuButton(items=menu_items, icon=ft.Icons.MORE_VERT)
            ], alignment=ft.MainAxisAlignment.START)
        )

class PersianCalendarWidget(ft.Container):
    def __init__(self, on_date_selected, on_close):
        super().__init__()
        self.rtl = True
        self.on_date_selected = on_date_selected
        self.on_close = on_close
        self.current_date = jdatetime.date.today()
        self.view_year = self.current_date.year
        self.view_month = self.current_date.month
        
        self.bgcolor = AppColors.SIDEBAR_BG
        self.border_radius = 15
        self.padding = 10
        side = ft.BorderSide(1, AppColors.PRIMARY)
        self.border = ft.Border(top=side, bottom=side, left=side, right=side)
        self.width = 300
        self.height = 360  # ارتفاع کل کادر
        self.shadow = ft.BoxShadow(blur_radius=30, color=ft.Colors.BLACK)

        # تنظیمات شبکه روزها
        self.days_grid = ft.GridView(
            runs_count=7,
            spacing=4, 
            run_spacing=2, # فاصله عمودی بسیار کم برای حذف اسکرول
            height=220,    # فضای کافی برای 6 ردیف احتمالی هفته
            expand=False,
            )

        # تنظیمات شبکه ماهها
        self.months_grid = ft.GridView(
            runs_count=3,
            spacing=5, 
            run_spacing=8, 
            height=220, 
            child_aspect_ratio=2.1, # کشیده کردن باکسهای ماه (حل مشکل بزرگی)
            visible=False
        )

        self.header_btn = ft.TextButton(
            content=ft.Text("", weight="bold", size=14, font_family="IRANSans", color="white"),
            on_click=self.toggle_view_mode
        )
        
        self.month_names = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        
        # پر کردن شبکه ماهها
        for i, m_name in enumerate(self.month_names):
            self.months_grid.controls.append(
                ft.Container(
                    content=ft.Text(m_name, color="white", text_align="center", size=11),
                    alignment=ft.Alignment(0, 0), 
                    bgcolor=ft.Colors.WHITE10, 
                    border_radius=6,
                    on_click=lambda e, m=i+1: self.select_month_from_grid(m), 
                    ink=True
                )
            )

        # ساختار کلی محتوا
        self.content = ft.Column([
            # هدر (ماه و سال و دکمههای جابجایی)
            ft.Row([
                ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=lambda e: self.change_month(-1), icon_color=AppColors.PRIMARY, icon_size=20),
                self.header_btn,
                ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=lambda e: self.change_month(1), icon_color=AppColors.PRIMARY, icon_size=20),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # نام روزهای هفته
            ft.Row(
                [
                    ft.Container(content=ft.Text(d, size=11, color="grey"), width=32, alignment=ft.Alignment(0, 0)) 
                    for d in ["ش", "ی", "د", "س", "چ", "پ", "ج"]
                ], 
                alignment=ft.MainAxisAlignment.SPACE_EVENLY, 
                visible=True
            ),
            
            # بخش اصلی (روزها یا ماهها)
            ft.Stack([
                self.days_grid, 
                self.months_grid
            ]),
            
            # دکمه بستن (چسبیده به انتهای کادر)
            ft.Row([
                ft.TextButton("بستن", on_click=lambda e: self.on_close(None))
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=5) # فاصله بین ردیفهای اصلی را کم کردیم
        
        self.update_calendar()

    def toggle_view_mode(self, e):
        is_day_view = self.days_grid.visible
        self.days_grid.visible = not is_day_view
        self.months_grid.visible = is_day_view
        self.content.controls[1].visible = not is_day_view 
        if self.page: self.update()

    def select_month_from_grid(self, month_idx):
        self.view_month = month_idx
        self.days_grid.visible = True
        self.months_grid.visible = False
        self.content.controls[1].visible = True
        self.update_calendar()

    
    
    def update_calendar(self):
        m_name = self.month_names[self.view_month-1] if 1 <= self.view_month <= 12 else "---"
        self.header_btn.content.value = f"{m_name} {self.view_year}"
        
        try:
            first_day = jdatetime.date(self.view_year, self.view_month, 1)
        except:
            self.view_month = 1
            first_day = jdatetime.date(self.view_year, self.view_month, 1)

        # اصلاح منطقی: چون هفته 7 روزه شده، فاصله را مستقیماً از wd میگیریم
        wd = first_day.weekday() 
        weekday_start = wd 
        
        # اصلاح روزهای ماه (به خصوص اسفند و سال کبیسه)
        if self.view_month <= 6:
            days_in_month = 31
        elif self.view_month <= 11:
            days_in_month = 30
        else:
            days_in_month = 30 if first_day.isleap() else 29
        
        self.days_grid.controls.clear()
        
        # ایجاد فضاهای خالی ابتدای ماه
        for _ in range(weekday_start): 
            self.days_grid.controls.append(ft.Container())
            
        # Get holidays for this month
        holidays = db.get_holidays_for_month(self.view_year, self.view_month)

        # ایجاد دکمههای روزها
        for day in range(1, days_in_month + 1):
            is_today = (day == self.current_date.day and 
                        self.view_month == self.current_date.month and 
                        self.view_year == self.current_date.year)
            
            # Holiday Check
            # Weekday logic: (wd + day - 1) % 7. If 6, it is Friday.
            day_of_week = (wd + day - 1) % 7
            is_friday = (day_of_week == 6)
            is_holiday = is_friday or (day in holidays)

            bg = AppColors.PRIMARY if is_today else ft.Colors.WHITE10
            
            if is_today:
                fg = ft.Colors.BLACK
            elif is_holiday:
                fg = AppColors.DANGER
            else:
                fg = ft.Colors.WHITE
            
            self.days_grid.controls.append(
                ft.Container(
                    content=ft.Text(str(day), color=fg, size=12, weight="bold"),
                    alignment=ft.Alignment(0, 0),
                    width=26,          # <--- Reduced size from 30 to 26
                    height=26,
                    bgcolor=bg, 
                    border_radius=13,
                    on_click=lambda e, d=day: self.select_date(d), 
                    ink=True
                )
            )
        
        if self.page:
            self.update()
            
    def change_month(self, delta):
        if self.months_grid.visible:
             self.view_year += delta
        else:
            self.view_month += delta
            if self.view_month > 12: self.view_month = 1; self.view_year += 1
            elif self.view_month < 1: self.view_month = 12; self.view_year -= 1
        self.update_calendar()

    def select_date(self, day):
        formatted = f"{self.view_year}-{self.view_month:02d}-{day:02d}"
        self.on_date_selected(formatted)

class EmployeeFormModal(ft.AlertDialog):
    def __init__(self, page, emp_data, current_user_role, on_save):
        super().__init__()
        self.page_ref = page
        self.emp_data = emp_data
        self.is_edit = emp_data is not None
        self.on_save = on_save
        self.modal = True
        self.bgcolor = AppColors.SIDEBAR_BG
        
        self.name_tf = ft.TextField(label="نام", expand=True, text_size=12, border_radius=8, filled=True, bgcolor=AppColors.INPUT_BG, border_color=AppColors.INPUT_BORDER)
        self.code_tf = ft.TextField(label="کد", expand=True, text_size=12, border_radius=8, filled=True, bgcolor=AppColors.INPUT_BG, border_color=AppColors.INPUT_BORDER)
        self.dept_tf = ft.TextField(label="بخش", expand=True, text_size=12, border_radius=8, filled=True, bgcolor=AppColors.INPUT_BG, border_color=AppColors.INPUT_BORDER)
        self.join_tf = ft.TextField(label="استخدام", read_only=True, expand=True, text_size=12, border_radius=8, filled=True, bgcolor=AppColors.INPUT_BG, border_color=AppColors.INPUT_BORDER)
        self.end_tf = ft.TextField(label="پایان", read_only=True, expand=True, text_size=12, border_radius=8, filled=True, bgcolor=AppColors.INPUT_BG, border_color=AppColors.INPUT_BORDER)
        self.pass_tf = ft.TextField(label="رمز", password=True, can_reveal_password=True, expand=True, text_size=12, border_radius=8, filled=True, bgcolor=AppColors.INPUT_BG, border_color=AppColors.INPUT_BORDER)
        self.phone_tf = ft.TextField(label="شماره تماس", expand=True, text_size=12, border_radius=8, filled=True, bgcolor=AppColors.INPUT_BG, border_color=AppColors.INPUT_BORDER)
        
        if self.is_edit:
            self.name_tf.value = emp_data[1]
            self.code_tf.value = emp_data[2]
            self.dept_tf.value = emp_data[3]
            self.join_tf.value = emp_data[4]
            self.end_tf.value = emp_data[5]
            self.phone_tf.value = emp_data[9] if len(emp_data) > 9 else ""
            if current_user_role != 'admin':
                self.phone_tf.read_only = True
        
        self.join_tf.on_click = lambda e: self.open_calendar(self.join_tf)
        self.end_tf.on_click = lambda e: self.open_calendar(self.end_tf)

        role_opts = [Option("user"), Option("manager"), Option("hr"), Option("admin"), Option("ceo")]
        self.role_dd = ft.Dropdown(
            label="نقش", options=role_opts, value=emp_data[6] if self.is_edit else "user",
            border_radius=8, filled=True, bgcolor=AppColors.INPUT_BG, border_color=AppColors.INPUT_BORDER, disabled=(current_user_role!='admin')
        )
        self.active_sw = ft.Switch(label="فعال", value=(emp_data[7] == 1) if self.is_edit else True, active_color=AppColors.PRIMARY)

        # Permissions Checklist
        self.perms_checklist = ft.Column(scroll=ft.ScrollMode.AUTO, height=150)
        all_perms = [
            ("delete_leave", "حذف مرخصی"),
            ("edit_leave", "ویرایش مرخصی"),
            ("create_personnel", "ایجاد پرسنل"),
            ("delete_personnel", "حذف پرسنل"),
            ("edit_personnel", "ویرایش پرسنل"),
            ("view_reports", "مشاهده گزارشات"),
            ("change_contract_end", "تغییر پایان قرارداد"),
            ("view_all_personnel", "مشاهده همه پرسنل (در غیر این صورت فقط بخش)")
        ]
        
        current_perms = []
        if self.is_edit:
            current_perms = db.get_user_permissions(emp_data[0])

        for key, label in all_perms:
            val = (key in current_perms) or ('all' in current_perms)
            self.perms_checklist.controls.append(ft.Checkbox(label=label, value=val, data=key))

        self.form_column = ft.Column([
            ft.Row([self.name_tf, self.code_tf]),
            ft.Row([self.dept_tf, self.phone_tf], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([self.join_tf, self.end_tf]),
            ft.Row([self.role_dd, self.pass_tf]),
            self.active_sw,
            ft.Text("دسترسی‌ها:", weight="bold"),
            ft.Container(content=self.perms_checklist, border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.WHITE10), 
                bottom=ft.BorderSide(1, ft.Colors.WHITE10), 
                left=ft.BorderSide(1, ft.Colors.WHITE10), 
                right=ft.BorderSide(1, ft.Colors.WHITE10)
            ), border_radius=5, padding=5)
        ], spacing=15, scroll=ft.ScrollMode.AUTO)
        
        self.calendar_layer = ft.Container(visible=False)
        
        self.title = ft.Text("ویرایش" if self.is_edit else "جدید", font_family="IRANSans", color="white")
        
        self.content = ft.Stack([
            ft.Container(content=self.form_column, width=400, height=500),
            self.calendar_layer
        ], width=400, height=500)
        
        self.actions = [
            ft.TextButton("لغو", on_click=self.close_dlg),
            ft.ElevatedButton("ذخیره", on_click=self.process_save, bgcolor=AppColors.PRIMARY, color="black")
        ]

    def open_calendar(self, control):
        def on_select(d):
            control.value = d
            control.update()
            self.calendar_layer.visible = False
            self.calendar_layer.update()
            
        def on_close(e):
            self.calendar_layer.visible = False
            self.calendar_layer.update()

        cal = PersianCalendarWidget(on_select, on_close)
        self.calendar_layer.content = ft.Container(
            content=cal, alignment=ft.Alignment(0,0),
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.BLACK), 
            on_click=lambda e: None, 
            border_radius=10
        )
        self.calendar_layer.visible = True
        self.calendar_layer.update()

    def process_save(self, e):
        data = {
            "name": self.name_tf.value, "code": self.code_tf.value, "dept": self.dept_tf.value,
            "join": self.join_tf.value, "end": self.end_tf.value, "role": self.role_dd.value,
            "pass": self.pass_tf.value, "phone": self.phone_tf.value, "active": self.active_sw.value,
            "perms": [cb.data for cb in self.perms_checklist.controls if cb.value]
        }
        if self.on_save(data, self.emp_data[0] if self.is_edit else None):
            self.close_dlg(None)

    def close_dlg(self, e):
        self.page_ref.close(self)

class PersianCalendarDialog(ft.AlertDialog):
    def __init__(self, page, on_date_selected):
        super().__init__()
        self.page_ref = page
        self.bgcolor = ft.Colors.TRANSPARENT
        self.modal = True
        self.content = PersianCalendarWidget(
            on_date_selected=lambda d: self.finish(d, on_date_selected),
            on_close=lambda e: self.page_ref.close(self)
        )
    
    def finish(self, d, cb):
        cb(d)
        self.page_ref.close(self)

class ColorPickerModal(ft.AlertDialog):
    def __init__(self, page, initial_color, on_color_picked):
        super().__init__()
        self.page = page
        self.on_color_picked = on_color_picked
        self.bgcolor = AppColors.SIDEBAR_BG
        self.hue = 0.0
        self.sat = 1.0
        self.val = 1.0
        try:
            if initial_color.startswith("#"):
                h = initial_color.lstrip('#')
                rgb = tuple(int(h[i:i+2], 16)/255.0 for i in (0, 2, 4))
                self.hue, self.sat, self.val = colorsys.rgb_to_hsv(*rgb)
        except: pass

        side = ft.BorderSide(2, "white")
        self.preview_box = ft.Container(
            width=60, height=60, bgcolor=initial_color, 
            border=ft.Border(top=side, bottom=side, left=side, right=side), 
            border_radius=5
        )
        self.hex_text = ft.Text(initial_color, size=14, weight="bold")
        
        self.hue_slider = ft.Slider(min=0, max=1, value=self.hue, label="Hue", on_change=self.update_color)
        self.sat_slider = ft.Slider(min=0, max=1, value=self.sat, label="Saturation", on_change=self.update_color)
        self.val_slider = ft.Slider(min=0, max=1, value=self.val, label="Value", on_change=self.update_color)

        self.title = ft.Text("انتخاب رنگ پیشرفته")
        self.content = ft.Container(
            width=300, height=300,
            content=ft.Column([
                ft.Row([self.preview_box, self.hex_text], alignment=ft.MainAxisAlignment.CENTER),
                ft.Text("رنگ (Hue)"), self.hue_slider,
                ft.Text("غلظت (Saturation)"), self.sat_slider,
                ft.Text("روشنایی (Value/Lightness)"), self.val_slider,
            ])
        )
        self.actions = [
            ft.TextButton("لغو", on_click=lambda e: self.page.close(self)),
            ft.ElevatedButton("تایید", on_click=self.confirm, bgcolor=AppColors.PRIMARY, color="black")
        ]

    def update_color(self, e):
        h = self.hue_slider.value
        s = self.sat_slider.value
        v = self.val_slider.value
        rgb = colorsys.hsv_to_rgb(h, s, v)
        hex_code = '#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        self.preview_box.bgcolor = hex_code
        self.preview_box.update()
        self.hex_text.value = hex_code
        self.hex_text.update()

    def confirm(self, e):
        self.on_color_picked(self.hex_text.value)
        self.page.close(self)

class ExcelMapperDialog(ft.AlertDialog):
    def __init__(self, page, df, required_fields, on_import):
        super().__init__()
        self.page = page
        self.df = df
        self.on_import = on_import
        self.dropdowns = {}
        self.bgcolor = AppColors.SIDEBAR_BG
        
        cols = ["(نادیده بگیر)"] + list(df.columns)
        controls = []
        for key, label in required_fields.items():
            dd = ft.Dropdown(
                label=label, 
                options=[Option(c) for c in cols], 
                value="(نادیده بگیر)",
                bgcolor=AppColors.SIDEBAR_BG,
                filled=True,
                border_color=ft.Colors.WHITE24,
                color="white"
            )
            for c in df.columns:
                if label in c or key in c: dd.value = c
            self.dropdowns[key] = dd
            controls.append(dd)
            
        self.title = ft.Text("تطبیق ستون‌ها", color="white")
        self.content = ft.Container(
             content=ft.Column(controls, tight=True, scroll=ft.ScrollMode.AUTO, height=300),
             bgcolor=AppColors.SIDEBAR_BG 
        )
        self.actions = [
            ft.TextButton("لغو", on_click=self.close_dlg),
            ft.ElevatedButton("تایید", on_click=self.do_import, bgcolor=AppColors.PRIMARY, color="black")
        ]

    def do_import(self, e):
        mapping = {k: v.value for k, v in self.dropdowns.items() if v.value != "(نادیده بگیر)"}
        self.on_import(self.df, mapping)
        self.close_dlg(None)

    def close_dlg(self, e):
        self.page.close(self)
