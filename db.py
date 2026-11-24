# db.py – لایه دیتابیس (SQLite + PostgreSQL)
import os, sqlite3
from datetime import datetime

# ═══════════════════════════════════════════════
#  انتخاب دیتابیس
#  اگر PostgreSQL نصب باشد → از PostgreSQL استفاده می‌شود
#  در غیر این صورت → از SQLite استفاده می‌شود
# ═══════════════════════════════════════════════

USE_POSTGRES = False  # اگر PostgreSQL نصب کردید، این را True کنید

if USE_POSTGRES:
    try:
        import psycopg2
        import psycopg2.extras
        from werkzeug.security import generate_password_hash, check_password_hash
        DB_CONFIG = {
            "dbname": "mohseni_tasks",
            "user": "postgres",
            "password": "postgres",
            "host": "localhost",
            "port": 5432,
        }
    except ImportError:
        print("psycopg2 یا werkzeug نصب نیست. از SQLite استفاده می‌شود.")
        USE_POSTGRES = False

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mohseni_tasks.db")


def _conn():
    if USE_POSTGRES:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn
    else:
        c = sqlite3.connect(DB_PATH, check_same_thread=False)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        return c


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _q(n):
    """برگرداندن علامت سوال برای پارامترها"""
    if USE_POSTGRES:
        return f"%({n})s"
    return "?"


# ═══════════════════════════════════════════════
#  INIT
# ═══════════════════════════════════════════════

def init_db():
    con = _conn()
    if USE_POSTGRES:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) DEFAULT '',
            role VARCHAR(20) DEFAULT 'user',
            section_id INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS sections (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            manager_id INTEGER,
            description TEXT DEFAULT '',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '',
            announce_date TEXT DEFAULT '',
            requester TEXT DEFAULT '',
            priority TEXT DEFAULT 'مهم',
            urgency TEXT DEFAULT 'غیر فوری',
            level INTEGER DEFAULT 3,
            delegatable INTEGER DEFAULT 0,
            assigned_to TEXT DEFAULT '',
            collaborator TEXT DEFAULT '',
            section_id INTEGER,
            status TEXT DEFAULT 'در حال انجام',
            progress REAL DEFAULT 0.0,
            deadline TEXT DEFAULT '',
            time_given INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            today_task TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS alarms (
            id SERIAL PRIMARY KEY,
            task_id INTEGER,
            user_id INTEGER,
            message TEXT NOT NULL,
            alarm_time TEXT DEFAULT '',
            ack INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS notes_board (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            note_date TEXT DEFAULT '',
            created_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            section_id INTEGER,
            sender_id INTEGER,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS daily_progress (
            id SERIAL PRIMARY KEY,
            task_id INTEGER,
            user_id INTEGER,
            progress_pct REAL DEFAULT 0.0,
            notes TEXT DEFAULT '',
            report_date VARCHAR(8) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        con.commit()
        # کاربر ادمین پیش‌فرض
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
        if cur.fetchone()[0] == 0:
            pw_hash = generate_password_hash("admin123")
            cur.execute(
                "INSERT INTO users(username,password_hash,full_name,role) VALUES(%s,%s,%s,%s)",
                ("admin", pw_hash, "مدیر سیستم", "admin")
            )
            con.commit()
    else:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT DEFAULT '',
            role TEXT DEFAULT 'user',
            section_id INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            manager_id INTEGER,
            description TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT '',
            announce_date TEXT DEFAULT '',
            requester TEXT DEFAULT '',
            priority TEXT DEFAULT 'مهم',
            urgency TEXT DEFAULT 'غیر فوری',
            level INTEGER DEFAULT 3,
            delegatable INTEGER DEFAULT 0,
            assigned_to TEXT DEFAULT '',
            collaborator TEXT DEFAULT '',
            section_id INTEGER,
            status TEXT DEFAULT 'در حال انجام',
            progress REAL DEFAULT 0.0,
            deadline TEXT DEFAULT '',
            time_given INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            today_task TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            user_id INTEGER,
            message TEXT NOT NULL,
            alarm_time TEXT DEFAULT '',
            ack INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS notes_board (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            note_date TEXT DEFAULT '',
            created_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER,
            sender_id INTEGER,
            content TEXT NOT NULL DEFAULT '',
            file_name TEXT DEFAULT '',
            file_data TEXT DEFAULT '',
            voice_data TEXT DEFAULT '',
            msg_type TEXT DEFAULT 'text',
            created_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS direct_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            content TEXT NOT NULL DEFAULT '',
            file_name TEXT DEFAULT '',
            file_data TEXT DEFAULT '',
            voice_data TEXT DEFAULT '',
            msg_type TEXT DEFAULT 'text',
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS daily_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            user_id INTEGER,
            progress_pct REAL DEFAULT 0.0,
            notes TEXT DEFAULT '',
            report_date TEXT NOT NULL,
            created_at TEXT DEFAULT ''
        );
        """)
        con.commit()

        # ── مهاجرت: اضافه کردن ستون‌های گمشده به جداول قدیمی ──
        cur = con.cursor()
        cur.execute("PRAGMA table_info(alarms)")
        cols = [r[1] for r in cur.fetchall()]
        if "user_id" not in cols:
            cur.execute("ALTER TABLE alarms ADD COLUMN user_id INTEGER")
            con.commit()

        cur.execute("PRAGMA table_info(tasks)")
        cols = [r[1] for r in cur.fetchall()]
        if "section_id" not in cols:
            cur.execute("ALTER TABLE tasks ADD COLUMN section_id INTEGER")
            con.commit()
        if "collaborator" not in cols:
            cur.execute("ALTER TABLE tasks ADD COLUMN collaborator TEXT DEFAULT ''")
            con.commit()
        if "delegatable" not in cols:
            cur.execute("ALTER TABLE tasks ADD COLUMN delegatable INTEGER DEFAULT 0")
            con.commit()
        if "announce_date" not in cols:
            cur.execute("ALTER TABLE tasks ADD COLUMN announce_date TEXT DEFAULT ''")
            con.commit()
        if "time_given" not in cols:
            cur.execute("ALTER TABLE tasks ADD COLUMN time_given INTEGER DEFAULT 0")
            con.commit()

        cur.execute("PRAGMA table_info(users)")
        cols = [r[1] for r in cur.fetchall()]
        if "section_id" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN section_id INTEGER")
            con.commit()

        cur.execute("PRAGMA table_info(messages)")
        cols = [r[1] for r in cur.fetchall()]
        if "file_name" not in cols:
            cur.execute("ALTER TABLE messages ADD COLUMN file_name TEXT DEFAULT ''")
            con.commit()
        if "file_data" not in cols:
            cur.execute("ALTER TABLE messages ADD COLUMN file_data TEXT DEFAULT ''")
            con.commit()
        if "voice_data" not in cols:
            try:
                cur.execute("ALTER TABLE messages ADD COLUMN voice_data TEXT DEFAULT ''")
                con.commit()
            except Exception:
                pass
        if "msg_type" not in cols:
            try:
                cur.execute("ALTER TABLE messages ADD COLUMN msg_type TEXT DEFAULT 'text'")
                con.commit()
            except Exception:
                pass

        # جدول پیام‌های انفرادی
        cur.execute("""CREATE TABLE IF NOT EXISTS direct_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            content TEXT NOT NULL DEFAULT '',
            file_name TEXT DEFAULT '',
            file_data TEXT DEFAULT '',
            voice_data TEXT DEFAULT '',
            msg_type TEXT DEFAULT 'text',
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT ''
        )""")
        con.commit()

        # کاربر ادمین پیش‌فرض
        try:
            from werkzeug.security import generate_password_hash
            pw_hash = generate_password_hash("admin123")
        except ImportError:
            pw_hash = "admin123"
        cur.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO users(username,password_hash,full_name,role,created_at) VALUES(?,?,?,?,?)",
                ("admin", pw_hash, "مدیر سیستم", "admin", _now())
            )
            con.commit()
    con.close()


# ═══════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════

def authenticate_user(username, password):
    try:
        from werkzeug.security import check_password_hash
    except ImportError:
        # اگر werkzeug نباشد
        pass
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM users WHERE username=%s AND is_active=TRUE", (username,))
    else:
        cur.execute("SELECT * FROM users WHERE username=? AND is_active=1", (username,))
    user = cur.fetchone()
    con.close()
    if not user:
        return None
    if user['password_hash'] == password:
        return dict(user)
    try:
        from werkzeug.security import check_password_hash as cph
        if cph(user['password_hash'], password):
            return dict(user)
    except:
        pass
    return None


# ═══════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════

def create_user(username, password, full_name="", role="user", section_id=None):
    try:
        from werkzeug.security import generate_password_hash
        pw_hash = generate_password_hash(password)
    except ImportError:
        pw_hash = password
    con = _conn()
    cur = con.cursor()
    try:
        if USE_POSTGRES:
            cur.execute(
                "INSERT INTO users(username,password_hash,full_name,role,section_id) VALUES(%s,%s,%s,%s,%s) RETURNING id",
                (username, pw_hash, full_name, role, section_id)
            )
            uid = cur.fetchone()['id']
        else:
            cur.execute(
                "INSERT INTO users(username,password_hash,full_name,role,section_id,created_at) VALUES(?,?,?,?,?,?)",
                (username, pw_hash, full_name, role, section_id, _now())
            )
            uid = cur.lastrowid
        con.commit()
        con.close()
        return uid
    except Exception:
        con.rollback()
        con.close()
        return None


def get_users():
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("""SELECT u.id,u.username,u.full_name,u.role,u.section_id,u.is_active,u.created_at,
            s.name as section_name
            FROM users u LEFT JOIN sections s ON s.id=u.section_id
            ORDER BY u.id""")
    else:
        cur.execute("""SELECT u.id,u.username,u.full_name,u.role,u.section_id,u.is_active,u.created_at,
            s.name as section_name
            FROM users u LEFT JOIN sections s ON s.id=u.section_id
            ORDER BY u.id""")
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_user(uid):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM users WHERE id=%s", (uid,))
    else:
        cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None


def update_user(uid, data):
    con = _conn()
    cur = con.cursor()
    fields = []
    vals = []
    for k, v in data.items():
        if k == "password" and v:
            try:
                from werkzeug.security import generate_password_hash
                pw_hash = generate_password_hash(v)
            except ImportError:
                pw_hash = v
            fields.append("password_hash=%s" if USE_POSTGRES else "password_hash=?")
            vals.append(pw_hash)
        elif k != "password":
            fields.append(f"{k}=%s" if USE_POSTGRES else f"{k}=?")
            vals.append(v)
    if fields:
        vals.append(uid)
        if USE_POSTGRES:
            cur.execute(f"UPDATE users SET {','.join(fields)} WHERE id=%s", vals)
        else:
            cur.execute(f"UPDATE users SET {','.join(fields)} WHERE id=?", vals)
        con.commit()
    con.close()


def delete_user(uid):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("DELETE FROM users WHERE id=%s AND username != 'admin'", (uid,))
    else:
        cur.execute("DELETE FROM users WHERE id=? AND username != 'admin'", (uid,))
    con.commit()
    con.close()


# ═══════════════════════════════════════════════
#  SECTIONS
# ═══════════════════════════════════════════════

def create_section(name, manager_id=None, description=""):
    con = _conn()
    cur = con.cursor()
    try:
        if USE_POSTGRES:
            cur.execute(
                "INSERT INTO sections(name,manager_id,description) VALUES(%s,%s,%s) RETURNING id",
                (name, manager_id, description)
            )
            sid = cur.fetchone()['id']
        else:
            cur.execute(
                "INSERT INTO sections(name,manager_id,description,created_at) VALUES(?,?,?,?)",
                (name, manager_id, description, _now())
            )
            sid = cur.lastrowid
        con.commit()
        con.close()
        return sid
    except Exception:
        con.rollback()
        con.close()
        return None


def get_sections():
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("""SELECT s.*,
            u.full_name as manager_name,
            (SELECT COUNT(*) FROM users WHERE section_id=s.id) as member_count,
            (SELECT COUNT(*) FROM tasks WHERE section_id=s.id) as task_count
            FROM sections s LEFT JOIN users u ON u.id=s.manager_id
            WHERE s.is_active=TRUE ORDER BY s.name""")
    else:
        cur.execute("""SELECT s.*,
            u.full_name as manager_name,
            (SELECT COUNT(*) FROM users WHERE section_id=s.id) as member_count,
            (SELECT COUNT(*) FROM tasks WHERE section_id=s.id) as task_count
            FROM sections s LEFT JOIN users u ON u.id=s.manager_id
            WHERE s.is_active=1 ORDER BY s.name""")
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_section(sid):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM sections WHERE id=%s", (sid,))
    else:
        cur.execute("SELECT * FROM sections WHERE id=?", (sid,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None


def update_section(sid, data):
    con = _conn()
    cur = con.cursor()
    fields = []
    vals = []
    for k, v in data.items():
        fields.append(f"{k}=%s" if USE_POSTGRES else f"{k}=?")
        vals.append(v)
    vals.append(sid)
    if USE_POSTGRES:
        cur.execute(f"UPDATE sections SET {','.join(fields)} WHERE id=%s", vals)
    else:
        cur.execute(f"UPDATE sections SET {','.join(fields)} WHERE id=?", vals)
    con.commit()
    con.close()


def delete_section(sid):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("UPDATE sections SET is_active=FALSE WHERE id=%s", (sid,))
    else:
        cur.execute("UPDATE sections SET is_active=0 WHERE id=?", (sid,))
    con.commit()
    con.close()


# ═══════════════════════════════════════════════
#  TASKS
# ═══════════════════════════════════════════════

def get_all_tasks(filters=None, user_role=None, user_section=None, user_name=None):
    con = _conn()
    cur = con.cursor()
    q = "SELECT * FROM tasks WHERE title != '' AND title IS NOT NULL"
    p = []

    if user_role == "manager" and user_section:
        q += " AND (section_id=? OR assigned_to=?)" if not USE_POSTGRES else " AND (section_id=%s OR assigned_to=%s)"
        p += [user_section, user_name or ""]
    elif user_role == "user" and user_name:
        q += " AND (assigned_to=? OR collaborator=?)" if not USE_POSTGRES else " AND (assigned_to=%s OR collaborator=%s)"
        p += [user_name, user_name]

    if filters:
        if filters.get("assigned_to"):
            q += " AND assigned_to=?" if not USE_POSTGRES else " AND assigned_to=%s"
            p.append(filters["assigned_to"])
        if filters.get("status"):
            q += " AND status=?" if not USE_POSTGRES else " AND status=%s"
            p.append(filters["status"])
        if filters.get("priority"):
            q += " AND priority=?" if not USE_POSTGRES else " AND priority=%s"
            p.append(filters["priority"])
        if filters.get("urgency"):
            q += " AND urgency=?" if not USE_POSTGRES else " AND urgency=%s"
            p.append(filters["urgency"])
        if filters.get("search"):
            t = f"%{filters['search']}%"
            q += " AND (title LIKE ? OR notes LIKE ? OR requester LIKE ?)" if not USE_POSTGRES else " AND (title LIKE %s OR notes LIKE %s OR requester LIKE %s)"
            p += [t, t, t]
        if filters.get("section_id"):
            q += " AND section_id=?" if not USE_POSTGRES else " AND section_id=%s"
            p.append(filters["section_id"])

    q += " ORDER BY id DESC"
    cur.execute(q, p)
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_task(tid):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM tasks WHERE id=%s", (tid,))
    else:
        cur.execute("SELECT * FROM tasks WHERE id=?", (tid,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None


def add_task(d):
    con = _conn()
    cur = con.cursor()
    now = _now()
    if USE_POSTGRES:
        cur.execute("""INSERT INTO tasks
            (title,announce_date,requester,priority,urgency,level,delegatable,
             assigned_to,collaborator,section_id,status,progress,deadline,time_given,
             notes,today_task,created_at,updated_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id""",
            (d.get("title", ""), d.get("announce_date", ""), d.get("requester", ""),
             d.get("priority", "مهم"), d.get("urgency", "غیر فوری"), d.get("level", 3),
             d.get("delegatable", 0), d.get("assigned_to", ""), d.get("collaborator", ""),
             d.get("section_id"), d.get("status", "در حال انجام"), d.get("progress", 0.0),
             d.get("deadline", ""), d.get("time_given", 0), d.get("notes", ""),
             d.get("today_task", ""), now, now))
        tid = cur.fetchone()['id']
    else:
        cur.execute("""INSERT INTO tasks
            (title,announce_date,requester,priority,urgency,level,delegatable,
             assigned_to,collaborator,section_id,status,progress,deadline,time_given,
             notes,today_task,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (d.get("title", ""), d.get("announce_date", ""), d.get("requester", ""),
             d.get("priority", "مهم"), d.get("urgency", "غیر فوری"), d.get("level", 3),
             d.get("delegatable", 0), d.get("assigned_to", ""), d.get("collaborator", ""),
             d.get("section_id"), d.get("status", "در حال انجام"), d.get("progress", 0.0),
             d.get("deadline", ""), d.get("time_given", 0), d.get("notes", ""),
             d.get("today_task", ""), now, now))
        tid = cur.lastrowid
    con.commit()
    con.close()
    return tid


def update_task(tid, d):
    con = _conn()
    cur = con.cursor()
    now = _now()
    fields = []
    vals = []
    for k, v in d.items():
        fields.append(f"{k}=%s" if USE_POSTGRES else f"{k}=?")
        vals.append(v)
    vals.extend([now, tid])
    op = "%s" if USE_POSTGRES else "?"
    cur.execute(f"UPDATE tasks SET {','.join(fields)},updated_at={op} WHERE id={op}", vals)
    con.commit()
    con.close()


def delete_task(tid):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("DELETE FROM tasks WHERE id=%s", (tid,))
        cur.execute("DELETE FROM alarms WHERE task_id=%s", (tid,))
    else:
        cur.execute("DELETE FROM tasks WHERE id=?", (tid,))
        cur.execute("DELETE FROM alarms WHERE task_id=?", (tid,))
    con.commit()
    con.close()


def get_task_stats(user_role=None, user_section=None, user_name=None):
    con = _conn()
    cur = con.cursor()

    where = "WHERE title!='' AND title IS NOT NULL"
    params = []

    def _scalar(row):
        if hasattr(row, 'keys') and 'c' in row.keys():
            return row['c']
        return row[0]

    cur.execute(f"SELECT COUNT(*) as c FROM tasks {where}", params)
    total = _scalar(cur.fetchone())

    cur.execute(f"SELECT COUNT(*) as c FROM tasks {where} AND status NOT IN ('تکمیل','منتفی')", params)
    active = _scalar(cur.fetchone())

    cur.execute(f"SELECT COUNT(*) as c FROM tasks {where} AND status='تکمیل'", params)
    completed = _scalar(cur.fetchone())

    cur.execute(f"SELECT COUNT(*) as c FROM tasks {where} AND status='منتفی'", params)
    cancelled = _scalar(cur.fetchone())

    cur.execute(f"""SELECT assigned_to,
        COUNT(*) as total,
        SUM(CASE WHEN status='تکمیل' THEN 1 ELSE 0 END) as completed,
        SUM(CASE WHEN status NOT IN ('تکمیل','منتفی') THEN 1 ELSE 0 END) as active
        FROM tasks {where} AND assigned_to!=''
        GROUP BY assigned_to ORDER BY total DESC""", params)
    person = cur.fetchall()
    con.close()

    return dict(total=total, active=active, completed=completed,
                cancelled=cancelled, personnel=[dict(r) for r in person])


def get_overdue_tasks(limit=20, user_role=None, user_section=None, user_name=None):
    import jalali_utils as ju
    tasks = get_all_tasks(user_role=user_role, user_section=user_section, user_name=user_name)
    od = []
    for t in tasks:
        if t["status"] in ("تکمیل", "منتفی"):
            continue
        d = ju.days_left(t["deadline"])
        if d is not None and d < 0:
            t["_days"] = d
            od.append(t)
    od.sort(key=lambda x: x["_days"])
    return od[:limit]


def get_upcoming_tasks(days=7, limit=20, user_role=None, user_section=None, user_name=None):
    import jalali_utils as ju
    tasks = get_all_tasks(user_role=user_role, user_section=user_section, user_name=user_name)
    up = []
    for t in tasks:
        if t["status"] in ("تکمیل", "منتفی"):
            continue
        d = ju.days_left(t["deadline"])
        if d is not None and 0 <= d <= days:
            t["_days"] = d
            up.append(t)
    up.sort(key=lambda x: x["_days"])
    return up[:limit]


def get_today_tasks(user_id):
    import jalali_utils as ju
    jy, jm, jd = ju.today_j()
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM tasks WHERE assigned_to=(SELECT full_name FROM users WHERE id=%s) AND status NOT IN ('تکمیل','منتفی')", (user_id,))
    else:
        cur.execute("SELECT * FROM tasks WHERE assigned_to=(SELECT full_name FROM users WHERE id=?) AND status NOT IN ('تکمیل','منتفی')", (user_id,))
    rows = cur.fetchall()
    con.close()
    result = []
    for r in rows:
        t = dict(r)
        d = ju.days_left(t["deadline"])
        if d is not None and d <= 0:
            result.append(t)
    return result


# ═══════════════════════════════════════════════
#  PERSONNEL
# ═══════════════════════════════════════════════

def get_all_personnel():
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM users WHERE is_active=TRUE ORDER BY full_name")
    else:
        cur.execute("SELECT * FROM users WHERE is_active=1 ORDER BY full_name")
    rows = cur.fetchall()
    con.close()
    return [{"name": r['full_name'] or r['username'], "role": r['role']} for r in rows]


def get_person_task_counts():
    con = _conn()
    cur = con.cursor()
    cur.execute("""SELECT assigned_to as name,
        COUNT(*) as total,
        SUM(CASE WHEN status='تکمیل' THEN 1 ELSE 0 END) as completed,
        SUM(CASE WHEN status NOT IN ('تکمیل','منتفی') THEN 1 ELSE 0 END) as active,
        SUM(CASE WHEN status='منتفی' THEN 1 ELSE 0 END) as cancelled
        FROM tasks WHERE title!='' AND assigned_to!=''
        GROUP BY assigned_to ORDER BY total DESC""")
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════
#  ALARMS
# ═══════════════════════════════════════════════

def get_unread_alarms(user_id=None):
    con = _conn()
    cur = con.cursor()
    if user_id:
        if USE_POSTGRES:
            cur.execute("""SELECT a.*,t.title as task_title,t.deadline,t.assigned_to
                FROM alarms a LEFT JOIN tasks t ON t.id=a.task_id
                WHERE a.ack=0 AND (a.user_id=%s OR a.user_id IS NULL)
                ORDER BY a.id DESC""", (user_id,))
        else:
            cur.execute("""SELECT a.*,t.title as task_title,t.deadline,t.assigned_to
                FROM alarms a LEFT JOIN tasks t ON t.id=a.task_id
                WHERE a.ack=0 AND (a.user_id=? OR a.user_id IS NULL)
                ORDER BY a.id DESC""", (user_id,))
    else:
        cur.execute("""SELECT a.*,t.title as task_title,t.deadline,t.assigned_to
            FROM alarms a LEFT JOIN tasks t ON t.id=a.task_id
            WHERE a.ack=0 ORDER BY a.id DESC""")
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_all_alarms(limit=60, user_id=None):
    con = _conn()
    cur = con.cursor()
    if user_id:
        if USE_POSTGRES:
            cur.execute("""SELECT a.*,t.title as task_title,t.deadline,t.assigned_to
                FROM alarms a LEFT JOIN tasks t ON t.id=a.task_id
                WHERE a.user_id=%s OR a.user_id IS NULL
                ORDER BY a.id DESC LIMIT %s""", (user_id, limit))
        else:
            cur.execute("""SELECT a.*,t.title as task_title,t.deadline,t.assigned_to
                FROM alarms a LEFT JOIN tasks t ON t.id=a.task_id
                WHERE a.user_id=? OR a.user_id IS NULL
                ORDER BY a.id DESC LIMIT ?""", (user_id, limit))
    else:
        if USE_POSTGRES:
            cur.execute("""SELECT a.*,t.title as task_title,t.deadline,t.assigned_to
                FROM alarms a LEFT JOIN tasks t ON t.id=a.task_id
                ORDER BY a.id DESC LIMIT %s""", (limit,))
        else:
            cur.execute("""SELECT a.*,t.title as task_title,t.deadline,t.assigned_to
                FROM alarms a LEFT JOIN tasks t ON t.id=a.task_id
                ORDER BY a.id DESC LIMIT ?""", (limit,))
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


def add_alarm(task_id, message, user_id=None):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("INSERT INTO alarms(task_id,message,alarm_time,user_id) VALUES(%s,%s,%s,%s)",
                    (task_id, message, _now(), user_id))
    else:
        cur.execute("INSERT INTO alarms(task_id,message,alarm_time,user_id) VALUES(?,?,?,?)",
                    (task_id, message, _now(), user_id))
    con.commit()
    con.close()


def ack_alarm(aid):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("UPDATE alarms SET ack=1 WHERE id=%s", (aid,))
    else:
        cur.execute("UPDATE alarms SET ack=1 WHERE id=?", (aid,))
    con.commit()
    con.close()


def ack_all(user_id=None):
    con = _conn()
    cur = con.cursor()
    if user_id:
        if USE_POSTGRES:
            cur.execute("UPDATE alarms SET ack=1 WHERE user_id=%s OR user_id IS NULL", (user_id,))
        else:
            cur.execute("UPDATE alarms SET ack=1 WHERE user_id=? OR user_id IS NULL", (user_id,))
    else:
        cur.execute("UPDATE alarms SET ack=1")
    con.commit()
    con.close()


def unread_count(user_id=None):
    con = _conn()
    cur = con.cursor()
    if user_id:
        if USE_POSTGRES:
            cur.execute("SELECT COUNT(*) as c FROM alarms WHERE ack=0 AND (user_id=%s OR user_id IS NULL)", (user_id,))
        else:
            cur.execute("SELECT COUNT(*) as c FROM alarms WHERE ack=0 AND (user_id=? OR user_id IS NULL)", (user_id,))
    else:
        cur.execute("SELECT COUNT(*) as c FROM alarms WHERE ack=0")
    row = cur.fetchone()
    n = row['c'] if hasattr(row, 'keys') and 'c' in row.keys() else row[0]
    con.close()
    return n


def check_and_create_alarms(user_id=None):
    import jalali_utils as ju
    tasks = get_all_tasks()
    created = 0
    for t in tasks:
        if t["status"] in ("تکمیل", "منتفی"):
            continue
        d = ju.days_left(t["deadline"])
        if d is None:
            continue
        msg = None
        if d < 0:
            msg = f"عقب افتاده {abs(d)} روز: {t['title'][:40]}"
        elif d <= 3:
            msg = f"{d} روز تا موعد: {t['title'][:40]}"
        if msg:
            con = _conn()
            cur = con.cursor()
            today_pfx = datetime.now().strftime("%Y-%m-%d")
            if USE_POSTGRES:
                cur.execute("SELECT 1 FROM alarms WHERE task_id=%s AND alarm_time LIKE %s LIMIT 1",
                            (t["id"], f"{today_pfx}%"))
            else:
                cur.execute("SELECT 1 FROM alarms WHERE task_id=? AND alarm_time LIKE ? LIMIT 1",
                            (t["id"], f"{today_pfx}%"))
            exists = cur.fetchone()
            con.close()
            if not exists:
                add_alarm(t["id"], msg, user_id)
                created += 1
    return created


# ═══════════════════════════════════════════════
#  MESSAGES
# ═══════════════════════════════════════════════

def add_message(section_id, sender_id, content, file_name="", file_data="", voice_data="", msg_type="text"):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("""INSERT INTO messages(section_id,sender_id,content,file_name,file_data,voice_data,msg_type)
            VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (section_id, sender_id, content, file_name, file_data, voice_data, msg_type))
        mid = cur.fetchone()['id']
    else:
        cur.execute("""INSERT INTO messages(section_id,sender_id,content,file_name,file_data,voice_data,msg_type,created_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (section_id, sender_id, content, file_name, file_data, voice_data, msg_type, _now()))
        mid = cur.lastrowid
    con.commit()
    con.close()
    return mid


def get_messages(section_id, limit=50):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("""SELECT m.*, u.full_name as sender_name, u.username
            FROM messages m LEFT JOIN users u ON u.id=m.sender_id
            WHERE m.section_id=%s
            ORDER BY m.created_at DESC LIMIT %s""", (section_id, limit))
    else:
        cur.execute("""SELECT m.*, u.full_name as sender_name, u.username
            FROM messages m LEFT JOIN users u ON u.id=m.sender_id
            WHERE m.section_id=?
            ORDER BY m.created_at DESC LIMIT ?""", (section_id, limit))
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in reversed(rows)]


# ═══════════════════════════════════════════════
#  DIRECT MESSAGES (چت انفرادی)
# ═══════════════════════════════════════════════

def add_direct_message(sender_id, receiver_id, content, file_name="", file_data="", voice_data="", msg_type="text"):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("""INSERT INTO direct_messages(sender_id,receiver_id,content,file_name,file_data,voice_data,msg_type)
            VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (sender_id, receiver_id, content, file_name, file_data, voice_data, msg_type))
        mid = cur.fetchone()['id']
    else:
        cur.execute("""INSERT INTO direct_messages(sender_id,receiver_id,content,file_name,file_data,voice_data,msg_type,created_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (sender_id, receiver_id, content, file_name, file_data, voice_data, msg_type, _now()))
        mid = cur.lastrowid
    con.commit()
    con.close()
    return mid


def get_direct_messages(user1_id, user2_id, limit=100):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("""SELECT dm.*,
            u1.full_name as sender_name, u2.full_name as receiver_name
            FROM direct_messages dm
            LEFT JOIN users u1 ON u1.id=dm.sender_id
            LEFT JOIN users u2 ON u2.id=dm.receiver_id
            WHERE (dm.sender_id=%s AND dm.receiver_id=%s)
               OR (dm.sender_id=%s AND dm.receiver_id=%s)
            ORDER BY dm.created_at ASC LIMIT %s""",
            (user1_id, user2_id, user2_id, user1_id, limit))
    else:
        cur.execute("""SELECT dm.*,
            u1.full_name as sender_name, u2.full_name as receiver_name
            FROM direct_messages dm
            LEFT JOIN users u1 ON u1.id=dm.sender_id
            LEFT JOIN users u2 ON u2.id=dm.receiver_id
            WHERE (dm.sender_id=? AND dm.receiver_id=?)
               OR (dm.sender_id=? AND dm.receiver_id=?)
            ORDER BY dm.created_at ASC LIMIT ?""",
            (user1_id, user2_id, user2_id, user1_id, limit))
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


def mark_dm_read(sender_id, receiver_id):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("UPDATE direct_messages SET is_read=1 WHERE sender_id=%s AND receiver_id=%s AND is_read=0",
                    (sender_id, receiver_id))
    else:
        cur.execute("UPDATE direct_messages SET is_read=1 WHERE sender_id=? AND receiver_id=? AND is_read=0",
                    (sender_id, receiver_id))
    con.commit()
    con.close()


def get_unread_dm_count(user_id):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT COUNT(*) as c FROM direct_messages WHERE receiver_id=%s AND is_read=0", (user_id,))
    else:
        cur.execute("SELECT COUNT(*) as c FROM direct_messages WHERE receiver_id=? AND is_read=0", (user_id,))
    row = cur.fetchone()
    n = row['c'] if hasattr(row, 'keys') and 'c' in row.keys() else row[0]
    con.close()
    return n


def get_dm_contacts(user_id):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("""SELECT DISTINCT u.id, u.full_name, u.username,
            (SELECT content FROM direct_messages
             WHERE ((sender_id=%s AND receiver_id=u.id) OR (sender_id=u.id AND receiver_id=%s))
             ORDER BY created_at DESC LIMIT 1) as last_msg,
            (SELECT created_at FROM direct_messages
             WHERE ((sender_id=%s AND receiver_id=u.id) OR (sender_id=u.id AND receiver_id=%s))
             ORDER BY created_at DESC LIMIT 1) as last_time,
            (SELECT COUNT(*) FROM direct_messages WHERE sender_id=u.id AND receiver_id=%s AND is_read=0) as unread
            FROM users u
            WHERE u.id != %s AND u.is_active=TRUE
            AND (EXISTS(SELECT 1 FROM direct_messages WHERE (sender_id=%s AND receiver_id=u.id) OR (sender_id=u.id AND receiver_id=%s)))
            ORDER BY last_time DESC""",
            (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))
    else:
        cur.execute("""SELECT DISTINCT u.id, u.full_name, u.username,
            (SELECT content FROM direct_messages
             WHERE ((sender_id=? AND receiver_id=u.id) OR (sender_id=u.id AND receiver_id=?))
             ORDER BY created_at DESC LIMIT 1) as last_msg,
            (SELECT created_at FROM direct_messages
             WHERE ((sender_id=? AND receiver_id=u.id) OR (sender_id=u.id AND receiver_id=?))
             ORDER BY created_at DESC LIMIT 1) as last_time,
            (SELECT COUNT(*) FROM direct_messages WHERE sender_id=u.id AND receiver_id=? AND is_read=0) as unread
            FROM users u
            WHERE u.id != ? AND u.is_active=1
            AND (EXISTS(SELECT 1 FROM direct_messages WHERE (sender_id=? AND receiver_id=u.id) OR (sender_id=u.id AND receiver_id=?)))
            ORDER BY last_time DESC""",
            (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════
#  DAILY PROGRESS
# ═══════════════════════════════════════════════

def save_daily_progress(task_id, user_id, progress_pct, notes, report_date):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("DELETE FROM daily_progress WHERE task_id=%s AND user_id=%s AND report_date=%s",
                    (task_id, user_id, report_date))
        cur.execute("""INSERT INTO daily_progress(task_id,user_id,progress_pct,notes,report_date)
            VALUES(%s,%s,%s,%s,%s)""", (task_id, user_id, progress_pct, notes, report_date))
    else:
        cur.execute("DELETE FROM daily_progress WHERE task_id=? AND user_id=? AND report_date=?",
                    (task_id, user_id, report_date))
        cur.execute("""INSERT INTO daily_progress(task_id,user_id,progress_pct,notes,report_date,created_at)
            VALUES(?,?,?,?,?,?)""", (task_id, user_id, progress_pct, notes, report_date, _now()))
    con.commit()
    con.close()


def get_daily_progress(user_id, report_date):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("""SELECT dp.*, t.title as task_title, t.deadline
            FROM daily_progress dp LEFT JOIN tasks t ON t.id=dp.task_id
            WHERE dp.user_id=%s AND dp.report_date=%s
            ORDER BY dp.id""", (user_id, report_date))
    else:
        cur.execute("""SELECT dp.*, t.title as task_title, t.deadline
            FROM daily_progress dp LEFT JOIN tasks t ON t.id=dp.task_id
            WHERE dp.user_id=? AND dp.report_date=?
            ORDER BY dp.id""", (user_id, report_date))
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_user_id_by_name(name):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT id FROM users WHERE full_name=%s OR username=%s", (name, name))
    else:
        cur.execute("SELECT id FROM users WHERE full_name=? OR username=?", (name, name))
    row = cur.fetchone()
    con.close()
    return row['id'] if row else None


# ═══════════════════════════════════════════════
#  NOTES
# ═══════════════════════════════════════════════

def get_notes():
    con = _conn()
    cur = con.cursor()
    cur.execute("SELECT * FROM notes_board ORDER BY id DESC LIMIT 30")
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


def add_note(content, note_date=""):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("INSERT INTO notes_board(content,note_date,created_at) VALUES(%s,%s,%s)",
                    (content, note_date, _now()))
    else:
        cur.execute("INSERT INTO notes_board(content,note_date,created_at) VALUES(?,?,?)",
                    (content, note_date, _now()))
    con.commit()
    con.close()


def delete_note(nid):
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("DELETE FROM notes_board WHERE id=%s", (nid,))
    else:
        cur.execute("DELETE FROM notes_board WHERE id=?", (nid,))
    con.commit()
    con.close()


# ═══════════════════════════════════════════════
#  EXCEL IMPORT
# ═══════════════════════════════════════════════

def import_users_from_excel(filepath):
    """ایمپورت کاربران از فایل اکسل
    ستون‌ها: نام, کد پرسنلی, دپارتمان, نقش, فعال
    """
    try:
        import openpyxl
    except ImportError:
        return 0, "openpyxl نصب نیست"

    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
    except Exception as e:
        return 0, f"خطا در باز کردن فایل: {e}"

    ws = wb.active
    count = 0
    errors = []

    # خواندن هدر
    headers = [str(c.value).strip() if c.value else "" for c in next(ws.iter_rows(min_row=1, max_row=1))]
    wb.close()

    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
        ws = wb.active
        for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
            if not row or not row[0]:
                continue
            name = str(row[0]).strip() if row[0] else ""
            code = str(row[1]).strip() if row[1] else ""
            dept = str(row[2]).strip() if row[2] else ""
            role = str(row[3]).strip() if row[3] else "user"
            active = str(row[4]).strip() if len(row) > 4 and row[4] else "بله"

            if not name:
                continue

            # نام کاربری = کد پرسنلی یا نام انگلیسی
            username = code if code else name.replace(" ", "_")

            # نقش
            if role not in ("admin", "manager", "user"):
                role = "user"

            # فعال
            is_active = 1 if active in ("بله", "yes", "1", "true", "فعال") else 0

            # پیدا کردن یا ایجاد بخش
            section_id = None
            if dept:
                section_id = _get_or_create_section(dept)

            # ایجاد کاربر
            try:
                pw_hash = None
                try:
                    from werkzeug.security import generate_password_hash
                    pw_hash = generate_password_hash(username)
                except ImportError:
                    pw_hash = username

                con = _conn()
                cur = con.cursor()
                if USE_POSTGRES:
                    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
                else:
                    cur.execute("SELECT id FROM users WHERE username=?", (username,))
                existing = cur.fetchone()

                if existing:
                    # به‌روزرسانی
                    if USE_POSTGRES:
                        cur.execute("""UPDATE users SET full_name=%s, role=%s, section_id=%s,
                            is_active=%s WHERE username=%s""",
                            (name, role, section_id, is_active, username))
                    else:
                        cur.execute("""UPDATE users SET full_name=?, role=?, section_id=?,
                            is_active=? WHERE username=?""",
                            (name, role, section_id, is_active, username))
                else:
                    # ایجاد جدید
                    if USE_POSTGRES:
                        cur.execute("""INSERT INTO users(username,password_hash,full_name,
                            role,section_id,is_active,created_at)
                            VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                            (username, pw_hash, name, role, section_id, is_active, _now()))
                    else:
                        cur.execute("""INSERT INTO users(username,password_hash,full_name,
                            role,section_id,is_active,created_at)
                            VALUES(?,?,?,?,?,?,?)""",
                            (username, pw_hash, name, role, section_id, is_active, _now()))

                con.commit()
                con.close()
                count += 1
            except Exception as e:
                errors.append(f"{name}: {e}")

        wb.close()
    except Exception as e:
        return 0, f"خطا در خواندن فایل: {e}"

    msg = f"{count} کاربر ایمپورت شد"
    if errors:
        msg += f" ({len(errors)} خطا)"
    return count, msg


def _get_or_create_section(name):
    """پیدا کردن یا ایجاد بخش"""
    con = _conn()
    cur = con.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT id FROM sections WHERE name=%s", (name,))
    else:
        cur.execute("SELECT id FROM sections WHERE name=?", (name,))
    row = cur.fetchone()
    if row:
        con.close()
        if hasattr(row, 'keys') and 'id' in row.keys():
            return row['id']
        return row[0]

    # ایجاد بخش جدید
    if USE_POSTGRES:
        cur.execute("INSERT INTO sections(name,created_at) VALUES(%s,%s) RETURNING id", (name, _now()))
        sid = cur.fetchone()['id']
    else:
        cur.execute("INSERT INTO sections(name,created_at) VALUES(?,?)", (name, _now()))
        sid = cur.lastrowid
    con.commit()
    con.close()
    return sid
