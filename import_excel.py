# import_excel.py – وارد کردن داده از اکسل
import os, sys, warnings
warnings.filterwarnings("ignore")

EXCEL_PATHS = [
    "مدیریت_امور_بر_-ابتدای_بهمن-توفیق-2-1404.xlsm",
    "/mnt/user-data/uploads/مدیریت_امور_بر_-ابتدای_بهمن-توفیق-2-1404.xlsm",
]

DEFAULT_PERSONNEL = [
    "توفیق","آقای میرزائی","ابولفضل","آقای حقیقی","آقای رخساری",
    "آقای محسنی","آقای راد","آقا یوسف نیا","خانم مهمانوار",
    "خانم مژدهی","خانم انصاری","خانم سرور","خانم سوگند سرور",
]


def _clean(v):
    if v is None: return ""
    s = str(v).strip()
    return "" if s in ("None","nan","0","0.0") else s


def _parse_date(v):
    if not v: return ""
    s = ''.join(c for c in str(v) if c.isdigit())
    return s[:8] if len(s) >= 8 else ""


def _parse_progress(status_val, progress_val):
    """ستون K ممکنه عدد باشه (پیشرفت) یا متن وضعیت"""
    sv = str(status_val).strip() if status_val else ""
    status_map = {
        "تکمیل": ("تکمیل", 1.0),
        "منتفی": ("منتفی", 0.0),
        "پیگیری مستمر": ("پیگیری مستمر", 0.0),
    }
    if sv in status_map:
        return status_map[sv]
    # Numeric progress
    try:
        prog = float(sv)
        if 0 < prog <= 1:
            return ("در حال انجام", prog)
    except: pass
    # Use col O
    try:
        prog = float(progress_val)
        return ("در حال انجام", min(prog, 1.0))
    except: pass
    return ("در حال انجام", 0.0)


def do_import(filepath=None):
    try:
        import openpyxl
    except ImportError:
        print("❌ openpyxl not installed")
        return 0

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import db

    # Find Excel file
    path = filepath
    if not path or not os.path.exists(path):
        for p in EXCEL_PATHS:
            if os.path.exists(p): path = p; break

    if not path or not os.path.exists(path):
        print(f"❌ Excel file not found")
        return 0

    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as e:
        print(f"❌ Cannot open Excel: {e}")
        return 0

    ws = wb.active
    count = 0
    personnel_set = set(DEFAULT_PERSONNEL)

    for row in ws.iter_rows(min_row=2, values_only=True):
        # Skip empty title rows
        title = _clean(row[1])
        if not title: continue

        announce_date = _parse_date(row[2])
        requester     = _clean(row[3])
        priority      = _clean(row[4]) or "مهم"
        urgency       = _clean(row[5]) or "غیر فوری"

        # Level (col G)
        level_raw = _clean(row[6])
        try: level = int(''.join(c for c in level_raw if c.isdigit())) if level_raw else 3
        except: level = 3

        delegatable = 1 if _clean(row[7]) == "بله" else 0
        assigned_to = _clean(row[8])
        collaborator = _clean(row[9])

        # Status & progress from col K + col O
        status, progress = _parse_progress(row[10], row[14])

        deadline   = _parse_date(row[11])
        try: time_given = int(row[12]) if row[12] else 0
        except: time_given = 0

        today_task = _clean(row[15])
        notes      = _clean(row[16])

        if assigned_to: personnel_set.add(assigned_to)
        if collaborator: personnel_set.add(collaborator)

        db.add_task({
            "title": title,
            "announce_date": announce_date,
            "requester": requester,
            "priority": priority,
            "urgency": urgency,
            "level": level,
            "delegatable": delegatable,
            "assigned_to": assigned_to,
            "collaborator": collaborator,
            "status": status,
            "progress": progress,
            "deadline": deadline,
            "time_given": time_given,
            "notes": notes,
            "today_task": today_task,
        })
        count += 1

    # Import notes from col W/X
    ws2 = wb["Sheet1"]
    for row in ws2.iter_rows(min_row=16, max_row=40, min_col=23, max_col=25, values_only=True):
        content = _clean(row[0])
        nd = _parse_date(row[1])
        if content and content not in ("یاد داشت ها",):
            db.add_note(content, nd)

    # Register all personnel
    for name in personnel_set:
        if name: db.ensure_personnel(name)

    wb.close()
    return count


if __name__ == "__main__":
    import db as _db
    _db.init_db()
    n = do_import()
    print(f"Imported {n} tasks")
