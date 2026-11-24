"""
مدیریت امور بازرگانی محسنی - Flask Backend
"""
import os, secrets, re, unicodedata, logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
import speech_recognition as sr
from io import BytesIO
import sqlite3
import jdatetime

# لاگر
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, 'debug.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=50*1024*1024)
DB_PATH = os.path.join(os.path.dirname(__file__), 'mohseni_tasks.db')

# Token storage in database
def _save_token(token, user_id):
    con = get_db()
    con.execute("INSERT OR REPLACE INTO auth_tokens(token,user_id,created_at) VALUES(?,?,?)",
                (token, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    con.commit(); con.close()

def _get_user_by_token(token):
    con = get_db()
    row = con.execute("SELECT user_id FROM auth_tokens WHERE token=?", (token,)).fetchone()
    con.close()
    return row['user_id'] if row else None

def _delete_token(token):
    con = get_db()
    con.execute("DELETE FROM auth_tokens WHERE token=?", (token,))
    con.commit(); con.close()


def get_db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = get_db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL, full_name TEXT DEFAULT '', role TEXT DEFAULT 'user',
        section_id INTEGER, is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL,
        manager_id INTEGER, description TEXT DEFAULT '', is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL DEFAULT '',
        requester TEXT DEFAULT '', priority TEXT DEFAULT 'مهم', urgency TEXT DEFAULT 'غیر فوری',
        level INTEGER DEFAULT 3, assigned_to TEXT DEFAULT '', collaborator TEXT DEFAULT '',
        section_id INTEGER, status TEXT DEFAULT 'در حال انجام', progress REAL DEFAULT 0.0,
        deadline TEXT DEFAULT '', notes TEXT DEFAULT '', today_task TEXT DEFAULT '',
        created_at TEXT DEFAULT '', updated_at TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS alarms (
        id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER, user_id INTEGER,
        message TEXT NOT NULL, alarm_time TEXT DEFAULT '', ack INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, section_id INTEGER, sender_id INTEGER,
        content TEXT DEFAULT '', file_name TEXT DEFAULT '', file_path TEXT DEFAULT '',
        voice_path TEXT DEFAULT '', msg_type TEXT DEFAULT 'text', created_at TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS direct_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER, receiver_id INTEGER,
        content TEXT DEFAULT '', file_name TEXT DEFAULT '', file_path TEXT DEFAULT '',
        voice_path TEXT DEFAULT '', msg_type TEXT DEFAULT 'text', is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS daily_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER, user_id INTEGER,
        progress_pct REAL DEFAULT 0.0, notes TEXT DEFAULT '', report_date TEXT NOT NULL,
        created_at TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS notes_board (
        id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL,
        note_date TEXT DEFAULT '', created_at TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS auth_tokens (
        token TEXT PRIMARY KEY, user_id INTEGER, created_at TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY, theme TEXT DEFAULT 'dark_neon',
        font_size TEXT DEFAULT 'normal', created_at TEXT DEFAULT '', updated_at TEXT DEFAULT '');
    """)
    con.commit()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if cur.fetchone()[0] == 0:
        pw = generate_password_hash("admin123")
        cur.execute("INSERT INTO users(username,password_hash,full_name,role,created_at) VALUES(?,?,?,?,?)",
                    ("admin", pw, "مدیر سیستم", "admin", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        con.commit()
    con.close()


# ═══════════════════════════════════════════════
#  TOKEN AUTH
# ═══════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        uid = _get_user_by_token(token)
        if not uid:
            return jsonify({"error": "unauthorized"}), 401
        request.user_id = uid
        return f(*args, **kwargs)
    return decorated


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    con = get_db()
    user = con.execute("SELECT * FROM users WHERE username=? AND is_active=1",
                       (data.get('username', ''),)).fetchone()
    con.close()
    if user and check_password_hash(user['password_hash'], data.get('password', '')):
        token = secrets.token_hex(32)
        _save_token(token, user['id'])
        return jsonify({
            "id": user['id'], "username": user['username'],
            "full_name": user['full_name'], "role": user['role'],
            "section_id": user['section_id'], "token": token
        })
    return jsonify({"error": "نام کاربری یا رمز اشتباه است"}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    _delete_token(token)
    return jsonify({"ok": True})


@app.route('/api/me')
@login_required
def me():
    con = get_db()
    user = con.execute("SELECT * FROM users WHERE id=?", (request.user_id,)).fetchone()
    con.close()
    if user:
        return jsonify({"id": user['id'], "username": user['username'],
                        "full_name": user['full_name'], "role": user['role'],
                        "section_id": user['section_id']})
    return jsonify({"error": "not found"}), 404


# ═══════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════

@app.route('/api/users')
@login_required
def get_users():
    con = get_db()
    rows = con.execute("""SELECT u.*, s.name as section_name FROM users u
        LEFT JOIN sections s ON s.id=u.section_id ORDER BY u.id""").fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    data = request.json
    pw = generate_password_hash(data.get('password', '123456'))
    con = get_db()
    try:
        con.execute("INSERT INTO users(username,password_hash,full_name,role,section_id,created_at) VALUES(?,?,?,?,?,?)",
                    (data['username'], pw, data.get('full_name', ''), data.get('role', 'user'),
                     data.get('section_id'), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        con.commit()
        con.close()
        return jsonify({"ok": True})
    except sqlite3.IntegrityError:
        con.close()
        return jsonify({"error": "نام کاربری تکراری است"}), 400


@app.route('/api/users/<int:uid>', methods=['PUT'])
@login_required
def update_user(uid):
    data = request.json
    con = get_db()
    fields = []
    vals = []
    if data.get('password'):
        fields.append("password_hash=?")
        vals.append(generate_password_hash(data['password']))
    for k in ['full_name', 'role', 'section_id']:
        if k in data:
            fields.append(f"{k}=?")
            vals.append(data[k])
    if fields:
        vals.append(uid)
        con.execute(f"UPDATE users SET {','.join(fields)} WHERE id=?", vals)
        con.commit()
    con.close()
    return jsonify({"ok": True})


@app.route('/api/users/<int:uid>', methods=['DELETE'])
@login_required
def delete_user(uid):
    con = get_db()
    con.execute("UPDATE users SET is_active=0 WHERE id=?", (uid,))
    con.commit()
    con.close()
    return jsonify({"ok": True})


@app.route('/api/users/search')
@login_required
def search_users():
    """جستجوی کاربران برای انتخاب مسئول"""
    q = request.args.get('q', '').strip()
    con = get_db()
    if q:
        rows = con.execute("""SELECT id, username, full_name, role, section_id
            FROM users WHERE is_active=1 AND (
                full_name LIKE ? OR username LIKE ? OR id=?
            ) ORDER BY full_name LIMIT 20""",
            (f"%{q}%", f"%{q}%", q if q.isdigit() else -1)).fetchall()
    else:
        rows = con.execute("""SELECT id, username, full_name, role, section_id
            FROM users WHERE is_active=1 ORDER BY full_name LIMIT 20""").fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])


# ═══════════════════════════════════════════════
#  SECTIONS
# ═══════════════════════════════════════════════

@app.route('/api/sections')
@login_required
def get_sections():
    con = get_db()
    rows = con.execute("""SELECT s.*, u.full_name as manager_name,
        (SELECT COUNT(*) FROM users WHERE section_id=s.id) as member_count
        FROM sections s LEFT JOIN users u ON u.id=s.manager_id
        WHERE s.is_active=1 ORDER BY s.name""").fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/sections', methods=['POST'])
@login_required
def create_section():
    data = request.json
    con = get_db()
    con.execute("INSERT INTO sections(name,manager_id,description,created_at) VALUES(?,?,?,?)",
                (data['name'], data.get('manager_id'), data.get('description', ''),
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    con.commit()
    con.close()
    return jsonify({"ok": True})


# ═══════════════════════════════════════════════
#  TASKS
# ═══════════════════════════════════════════════

@app.route('/api/tasks')
@login_required
def get_tasks():
    con = get_db()
    user = con.execute("SELECT * FROM users WHERE id=?", (request.user_id,)).fetchone()
    if not user:
        con.close()
        return jsonify([])

    role = user['role']
    section_id = user['section_id']
    full_name = user['full_name'] or ''

    if role == 'admin':
        rows = con.execute("SELECT * FROM tasks WHERE title!='' ORDER BY id DESC").fetchall()
    elif role == 'manager':
        rows = con.execute("""SELECT * FROM tasks WHERE title!='' AND (
            assigned_to=? OR requester=? OR
            (section_id=? AND section_id IS NOT NULL)
        ) ORDER BY id DESC""", (full_name, full_name, section_id)).fetchall()
    else:
        rows = con.execute("""SELECT * FROM tasks WHERE title!='' AND (
            assigned_to=? OR requester=?
        ) ORDER BY id DESC""", (full_name, full_name)).fetchall()

    con.close()

    today = jdatetime.date.today()
    result = []
    for r in rows:
        d = dict(r)
        deadline = d.get('deadline', '')
        created_at = d.get('created_at', '')

        # محاسبه فرصت = اختلاف زمان ایجاد کار با موعد تحویل
        if deadline:
            try:
                parts = deadline.split('/')
                if len(parts) == 3:
                    dl = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                    # فرصت: اختلاف امروز با موعد (اگر time_given خالی باشه)
                    if not d.get('time_given'):
                        diff = (dl - today).days
                        d['time_given'] = str(max(diff, 0))
                    # مانده: اختلاف موعد با امروز
                    remaining = (dl - today).days
                    d['remaining_days'] = remaining
            except:
                pass

        result.append(d)

    return jsonify(result)


@app.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.json
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # محاسبه خودکار فرصت = اختلاف زمان ایجاد کار با موعد تحویل
    time_given = data.get('time_given', '')
    deadline = data.get('deadline', '')
    if deadline and not time_given:
        try:
            parts = deadline.split('/')
            if len(parts) == 3:
                dl = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                today = jdatetime.date.today()
                diff = (dl - today).days
                time_given = str(max(diff, 0))
        except:
            pass

    con = get_db()
    con.execute("""INSERT INTO tasks(title,requester,priority,urgency,level,
        assigned_to,collaborator,section_id,status,progress,deadline,
        notes,today_task,time_given,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (data.get('title',''), data.get('requester',''), data.get('priority','مهم'),
         data.get('urgency','غیر فوری'), data.get('level',3), data.get('assigned_to',''),
         data.get('collaborator',''), data.get('section_id'), data.get('status','در حال انجام'),
         data.get('progress',0), deadline, data.get('notes',''),
         data.get('today_task',''), time_given, now, now))
    con.commit()
    con.close()
    return jsonify({"ok": True})


@app.route('/api/tasks/<int:tid>', methods=['DELETE'])
@login_required
def delete_task(tid):
    con = get_db()
    con.execute("DELETE FROM tasks WHERE id=?", (tid,))
    con.commit()
    con.close()
    return jsonify({"ok": True})


@app.route('/api/tasks/<int:tid>', methods=['PUT'])
@login_required
def update_task(tid):
    data = request.json
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # اگر deadline تغییر کرده، time_given رو دوباره حساب کن
    if 'deadline' in data and data['deadline'] and not data.get('time_given'):
        try:
            parts = data['deadline'].split('/')
            if len(parts) == 3:
                dl = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                today = jdatetime.date.today()
                diff = (dl - today).days
                data['time_given'] = str(max(diff, 0))
        except:
            pass

    fields = []
    vals = []
    for k, v in data.items():
        if k != 'id':
            fields.append(f"{k}=?")
            vals.append(v)
    fields.append("updated_at=?")
    vals.append(now)
    vals.append(tid)
    con = get_db()
    con.execute(f"UPDATE tasks SET {','.join(fields)} WHERE id=?", vals)
    con.commit()
    con.close()

    # آلارم تکمیل
    if data.get('status') == 'تکمیل':
        send_completion_alarm(tid)

    return jsonify({"ok": True})


@app.route('/api/tasks/<int:tid>/progress', methods=['PUT'])
@login_required
def update_task_progress(tid):
    """به‌روزرسانی درصد پیشرفت تسک با ارسال آلارم تغییر"""
    data = request.json
    progress = data.get('progress', 0)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    con = get_db()
    # دریافت پیشرفت قبلی
    old_task = con.execute("SELECT progress, title, assigned_to, requester FROM tasks WHERE id=?", (tid,)).fetchone()
    old_progress = old_task['progress'] if old_task else 0

    con.execute("UPDATE tasks SET progress=?, updated_at=? WHERE id=?", (progress, now, tid))
    con.commit()

    # ثبت در تاریخچه پیشرفت
    con.execute("""INSERT INTO daily_progress(task_id, user_id, progress_pct, notes, report_date, created_at)
        VALUES(?,?,?,?,?,?)""", (tid, request.user_id, progress, data.get('notes', ''), now[:10], now))
    con.commit()

    # ارسال آلارم تغییر پیشرفت اگر تغییر کرده باشه
    if old_task and old_progress != progress:
        task_title = old_task['title'] or ''
        assigned_to = old_task['assigned_to'] or ''
        requester = old_task['requester'] or ''
        user = con.execute("SELECT full_name FROM users WHERE id=?", (request.user_id,)).fetchone()
        updater_name = user['full_name'] if user else ''

        # پیدا کردن user_id مسئول انجام
        assignee = con.execute("SELECT id FROM users WHERE full_name=?", (assigned_to,)).fetchone()
        assignee_id = assignee['id'] if assignee else None

        # پیدا کردن user_id مرجع
        requester_user = con.execute("SELECT id FROM users WHERE full_name=?", (requester,)).fetchone()
        requester_id = requester_user['id'] if requester_user else None

        progress_pct = round(progress * 100)
        msg = f"پیشرفت تسک «{task_title[:40]}» توسط {updater_name} به {progress_pct}% تغییر کرد"

        # آلارم برای مسئول انجام
        if assignee_id and assignee_id != request.user_id:
            con.execute("INSERT INTO alarms(task_id,user_id,message,alarm_time) VALUES(?,?,?,?)",
                        (tid, assignee_id, msg, now))
            socketio.emit('alarm', {"message": msg, "task_id": tid, "type": "progress_update",
                                    "progress": progress, "title": task_title}, room=f"user_{assignee_id}")

        # آلارم برای مرجع
        if requester_id and requester_id != request.user_id and requester_id != assignee_id:
            con.execute("INSERT INTO alarms(task_id,user_id,message,alarm_time) VALUES(?,?,?,?)",
                        (tid, requester_id, msg, now))
            socketio.emit('alarm', {"message": msg, "task_id": tid, "type": "progress_update",
                                    "progress": progress, "title": task_title}, room=f"user_{requester_id}")

        # ارسال نوتیفیکیشن در چت (برای همه اتاق‌های مرتبط)
        progress_card = {
            "type": "progress_card",
            "task_id": tid,
            "title": task_title,
            "progress": progress,
            "progress_pct": progress_pct,
            "updated_by": updater_name,
            "assigned_to": assigned_to,
            "requester": requester,
            "created_at": now,
            "message": msg
        }
        socketio.emit('progress_update', progress_card)

        con.commit()

    con.close()
    return jsonify({"ok": True})


@app.route('/api/tasks/<int:tid>')
@login_required
def get_task(tid):
    """دریافت یک تسک خاص"""
    con = get_db()
    row = con.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
    con.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "یافت نشد"}), 404


@app.route('/api/tasks/matrix')
@login_required
def get_eisenhower_matrix():
    """دریافت ماتریس آیزنهاور برای وظایف"""
    con = get_db()
    rows = con.execute("SELECT * FROM tasks WHERE title!='' AND status NOT IN ('تکمیل','منتفی') ORDER BY level ASC").fetchall()
    con.close()

    matrix = {1: [], 2: [], 3: [], 4: []}
    for r in rows:
        d = dict(r)
        level = d.get('level', 3)
        if level in matrix:
            matrix[level].append(d)

    return jsonify({
        "matrix": {str(k): v for k, v in matrix.items()},
        "labels": {
            "1": "فوری و مهم - انجام فوری",
            "2": "مهم - برنامه‌ریزی",
            "3": "غیرمهم - واگذاری",
            "4": "حذف/حذف"
        }
    })


@app.route('/api/progress/summary')
@login_required
def get_progress_summary():
    """خلاصه پیشرفت کل پروژه"""
    con = get_db()
    total = con.execute("SELECT COUNT(*) as c FROM tasks WHERE title!=''").fetchone()['c']
    completed = con.execute("SELECT COUNT(*) as c FROM tasks WHERE title!='' AND status='تکمیل'").fetchone()['c']
    in_progress = con.execute("SELECT COUNT(*) as c FROM tasks WHERE title!='' AND status='در حال انجام'").fetchone()['c']
    cancelled = con.execute("SELECT COUNT(*) as c FROM tasks WHERE title!='' AND status='منتفی'").fetchone()['c']
    tracking = con.execute("SELECT COUNT(*) as c FROM tasks WHERE title!='' AND status='پیگیری مستمر'").fetchone()['c']

    # میانگین پیشرفت
    avg_progress = con.execute("SELECT AVG(progress) as avg FROM tasks WHERE title!='' AND status NOT IN ('تکمیل','منتفی')").fetchone()['avg'] or 0

    # وظایف بر اساس سطح
    levels = {}
    for level in range(1, 5):
        levels[level] = con.execute("SELECT COUNT(*) as c FROM tasks WHERE title!='' AND level=? AND status NOT IN ('تکمیل','منتفی')", (level,)).fetchone()['c']

    con.close()

    pct_complete = round(completed / total * 100) if total > 0 else 0

    return jsonify({
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "cancelled": cancelled,
        "tracking": tracking,
        "pct_complete": pct_complete,
        "avg_progress": round(avg_progress * 100, 1),
        "levels": levels
    })


# ═══════════════════════════════════════════════
#  CHAT - GROUP
# ═══════════════════════════════════════════════

@app.route('/api/chat/<int:section_id>')
@login_required
def get_group_messages(section_id):
    con = get_db()
    rows = con.execute("""SELECT m.*, u.full_name as sender_name FROM messages m
        LEFT JOIN users u ON u.id=m.sender_id WHERE m.section_id=?
        ORDER BY m.created_at ASC LIMIT 200""", (section_id,)).fetchall()
    con.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get('file_path'):
            d['file_url'] = f"/uploads/{os.path.basename(d['file_path'])}"
        if d.get('voice_path'):
            d['voice_url'] = f"/uploads/{os.path.basename(d['voice_path'])}"
        result.append(d)
    return jsonify(result)


@app.route('/api/chat/<int:section_id>', methods=['POST'])
@login_required
def send_group_message(section_id):
    content = request.form.get('content', '')
    msg_type = request.form.get('msg_type', 'text')
    file_path = ''
    voice_path = ''

    # اطمینان از وجود پوشه آپلود
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    if 'file' in request.files:
        f = request.files['file']
        if f.filename:
            fname = f"{secrets.token_hex(8)}_{f.filename}"
            fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            f.save(fpath)
            file_path = fpath
            msg_type = 'file'

    if 'voice' in request.files:
        v = request.files['voice']
        if v.filename:
            vname = f"{secrets.token_hex(8)}_{v.filename}"
            vpath = os.path.join(app.config['UPLOAD_FOLDER'], vname)
            v.save(vpath)
            voice_path = vpath
            msg_type = 'voice'

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con = get_db()
    con.execute("""INSERT INTO messages(section_id,sender_id,content,file_name,file_path,
        voice_path,msg_type,created_at) VALUES(?,?,?,?,?,?,?,?)""",
        (section_id, request.user_id, content,
         os.path.basename(file_path) if file_path else '',
         file_path, voice_path, msg_type, now))
    con.commit()
    user = con.execute("SELECT full_name FROM users WHERE id=?", (request.user_id,)).fetchone()
    con.close()

    msg_data = {
        "section_id": section_id, "sender_id": request.user_id,
        "sender_name": user['full_name'] if user else "",
        "content": content, "msg_type": msg_type,
        "file_name": os.path.basename(file_path) if file_path else '',
        "file_url": f"/uploads/{os.path.basename(file_path)}" if file_path else '',
        "voice_url": f"/uploads/{os.path.basename(voice_path)}" if voice_path else '',
        "created_at": now
    }
    socketio.emit('new_message', msg_data, room=f"section_{section_id}")
    return jsonify({"ok": True})


# ═══════════════════════════════════════════════
#  CHAT - DIRECT
# ═══════════════════════════════════════════════

@app.route('/api/dm/<int:user_id>')
@login_required
def get_direct_messages(user_id):
    my_id = request.user_id
    con = get_db()
    rows = con.execute("""SELECT dm.*, u.full_name as sender_name FROM direct_messages dm
        LEFT JOIN users u ON u.id=dm.sender_id
        WHERE (dm.sender_id=? AND dm.receiver_id=?) OR (dm.sender_id=? AND dm.receiver_id=?)
        ORDER BY dm.created_at ASC LIMIT 200""",
        (my_id, user_id, user_id, my_id)).fetchall()
    con.execute("UPDATE direct_messages SET is_read=1 WHERE sender_id=? AND receiver_id=? AND is_read=0",
                (user_id, my_id))
    con.commit()
    con.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get('file_path'):
            d['file_url'] = f"/uploads/{os.path.basename(d['file_path'])}"
        if d.get('voice_path'):
            d['voice_url'] = f"/uploads/{os.path.basename(d['voice_path'])}"
        result.append(d)
    return jsonify(result)


@app.route('/api/dm/<int:receiver_id>', methods=['POST'])
@login_required
def send_direct_message(receiver_id):
    content = request.form.get('content', '')
    msg_type = request.form.get('msg_type', 'text')
    file_path = ''
    voice_path = ''

    # اطمینان از وجود پوشه آپلود
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    if 'file' in request.files:
        f = request.files['file']
        if f.filename:
            fname = f"{secrets.token_hex(8)}_{f.filename}"
            fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            f.save(fpath)
            file_path = fpath
            msg_type = 'file'

    if 'voice' in request.files:
        v = request.files['voice']
        if v.filename:
            vname = f"{secrets.token_hex(8)}_{v.filename}"
            vpath = os.path.join(app.config['UPLOAD_FOLDER'], vname)
            v.save(vpath)
            voice_path = vpath
            msg_type = 'voice'

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con = get_db()
    con.execute("""INSERT INTO direct_messages(sender_id,receiver_id,content,file_name,
        file_path,voice_path,msg_type,created_at) VALUES(?,?,?,?,?,?,?,?)""",
        (request.user_id, receiver_id, content,
         os.path.basename(file_path) if file_path else '',
         file_path, voice_path, msg_type, now))
    con.commit()
    user = con.execute("SELECT full_name FROM users WHERE id=?", (request.user_id,)).fetchone()
    con.close()

    msg_data = {
        "sender_id": request.user_id, "receiver_id": receiver_id,
        "sender_name": user['full_name'] if user else "",
        "content": content, "msg_type": msg_type,
        "file_name": os.path.basename(file_path) if file_path else '',
        "file_url": f"/uploads/{os.path.basename(file_path)}" if file_path else '',
        "voice_url": f"/uploads/{os.path.basename(voice_path)}" if voice_path else '',
        "created_at": now
    }
    socketio.emit('new_dm', msg_data, room=f"user_{receiver_id}")
    return jsonify({"ok": True})


# ═══════════════════════════════════════════════
#  SPEECH TO TEXT
# ═══════════════════════════════════════════════

@app.route('/api/voice-to-task', methods=['POST'])
@login_required
def voice_to_task():
    logger.debug("[VOICE-TO-TASK] called")
    if 'voice' not in request.files:
        logger.debug("[VOICE-TO-TASK] no voice file")
        return jsonify({"error": "فایل صوتی یافت نشد"}), 400
    voice = request.files['voice']
    try:
        recognizer = sr.Recognizer()
        audio_data = BytesIO(voice.read())
        with sr.AudioFile(audio_data) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language='fa-IR')
        logger.debug(f"[VOICE-TO-TASK] recognized text: {text!r}")

        # تابع جستجوی کاربر در دیتابیس
        def find_user_in_db(name):
            con = get_db()
            # جستجو بر اساس نام کامل، نام کاربری یا بخشی از نام
            user = con.execute("""SELECT full_name FROM users WHERE
                full_name LIKE ? OR full_name LIKE ? OR full_name LIKE ? OR username LIKE ?
                ORDER BY CASE
                    WHEN full_name = ? THEN 1
                    WHEN full_name LIKE ? THEN 2
                    WHEN full_name LIKE ? THEN 3
                    ELSE 4
                END LIMIT 1""",
                (name, f"%{name}%", f"%{name}%", name, name, f"{name}%", f"%{name}%")).fetchone()
            con.close()
            if user:
                return user['full_name']
            return None

        # استخراج هوشمند با detect_task_from_message
        result = detect_task_from_message(text, find_user_in_db)
        print(f"[VOICE-TO-TASK] text={text!r}, result={result}")
        if result:
            # اگر "خودم" یا "بهم" گفته شده، نام کاربر فعلی رو قرار بده
            assigned = result.get('assigned_to', '')
            if assigned == '__SELF__':
                con = get_db()
                current_user = con.execute("SELECT full_name FROM users WHERE id=?", (request.user_id,)).fetchone()
                con.close()
                assigned = current_user['full_name'] if current_user else ''
            return jsonify({
                "title": result['title'], "notes": result['notes'],
                "priority": result['priority'], "urgency": result.get('urgency', 'غیر فوری'),
                "level": result.get('level', 3),
                "deadline": result['deadline'],
                "assigned_to": assigned,
                "time_given": result.get('time_given', ''),
                "raw_text": text
            })

        # اگر تشخیص داده نشد، ساده برگردان
        today = jdatetime.date.today()
        lines = text.split('.')
        title = lines[0].strip() if lines else text
        notes = '. '.join(lines[1:]).strip() if len(lines) > 1 else ''
        return jsonify({"title": title[:100], "notes": notes, "priority": "مهم",
                        "urgency": "غیر فوری", "level": 3,
                        "deadline": f"{today.year}/{today.month:02d}/{today.day:02d}",
                        "assigned_to": "", "raw_text": text})
    except sr.UnknownValueError:
        return jsonify({"error": "صدا قابل تشخیص نیست"}), 400
    except sr.RequestError as e:
        return jsonify({"error": f"خطای سرویس گوگل: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/voice-to-text', methods=['POST'])
@login_required
def voice_to_text():
    """تست متنی - متن وارد کن و نتیجه تشخیص رو ببین"""
    data = request.json
    text = data.get('text', '')
    logger.debug(f"[VOICE-TO-TEXT] called, text={text!r}")
    if not text:
        return jsonify({"error": "متن خالیه"}), 400

    def find_user_in_db(name):
        con = get_db()
        user = con.execute("SELECT full_name FROM users WHERE full_name LIKE ? LIMIT 1", (f"%{name}%",)).fetchone()
        con.close()
        return user['full_name'] if user else None

    result = detect_task_from_message(text, find_user_in_db)
    logger.debug(f"[VOICE-TO-TEXT] detect result: {result}")
    if not result:
        logger.debug("[VOICE-TO-TEXT] no task detected")
        return jsonify({"error": "تسک تشخیص داده نشد", "text": text})

    assigned = result.get('assigned_to', '')
    if assigned == '__SELF__':
        con = get_db()
        cu = con.execute("SELECT full_name FROM users WHERE id=?", (request.user_id,)).fetchone()
        con.close()
        assigned = cu['full_name'] if cu else ''

    logger.debug(f"[VOICE-TO-TEXT] returning: title={result['title']!r}, deadline={result['deadline']!r}, assigned_to={assigned!r}")
    return jsonify({
        "title": result['title'], "notes": result['notes'],
        "priority": result['priority'], "urgency": result.get('urgency', 'غیر فوری'),
        "level": result.get('level', 3), "deadline": result['deadline'],
        "assigned_to": assigned, "time_given": result.get('time_given', ''),
        "raw_text": text
    })


# ═══════════════════════════════════════════════
#  ALARMS
# ═══════════════════════════════════════════════

@app.route('/api/alarms')
@login_required
def get_alarms():
    con = get_db()
    rows = con.execute("""SELECT a.*, t.title as task_title FROM alarms a
        LEFT JOIN tasks t ON t.id=a.task_id
        WHERE (a.user_id=? OR a.user_id IS NULL) ORDER BY a.id DESC LIMIT 50""",
        (request.user_id,)).fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/alarms/read', methods=['POST'])
@login_required
def read_alarms():
    con = get_db()
    con.execute("UPDATE alarms SET ack=1 WHERE (user_id=? OR user_id IS NULL)", (request.user_id,))
    con.commit()
    con.close()
    return jsonify({"ok": True})


# ═══════════════════════════════════════════════
#  UPLOADS
# ═══════════════════════════════════════════════

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ═══════════════════════════════════════════════
#  SOCKET.IO
# ═══════════════════════════════════════════════

@socketio.on('join_section')
def on_join_section(data):
    join_room(f"section_{data['section_id']}")


@socketio.on('join_user')
def on_join_user(data):
    join_room(f"user_{data['user_id']}")


# ═══════════════════════════════════════════════
#  AI: تشخیص پیام به عنوان تسک
# ═══════════════════════════════════════════════

# ═══════════════════════════════════════════════
#  ماتریس آیزنهاور - سطح‌بندی خودکار وظایف
# ═══════════════════════════════════════════════

def calculate_eisenhower_level(priority, urgency):
    """
    محاسبه سطح بر اساس ماتریس آیزنهاور:
    سطح 1: فوری و مهم → انجام فوری
    سطح 2: غیرفوری و مهم → برنامه‌ریزی
    سطح 3: فوری و غیرمهم → واگذاری
    سطح 4: غیرفوری و غیرمهم → حذف/حذف
    """
    priority_lower = priority.lower() if priority else ''
    urgency_lower = urgency.lower() if urgency else ''

    is_important = priority_lower in ['مهم', 'خیلی مهم', 'مهم']
    is_urgent = urgency_lower in ['فوری', 'ضروری', 'فوری']

    if is_important and is_urgent:
        return 1  # فوری و مهم
    elif is_important and not is_urgent:
        return 2  # مهم ولی غیرفوری
    elif not is_important and is_urgent:
        return 3  # فوری ولی غیرمهم
    else:
        return 4  # غیرفوری و غیرمهم


def get_level_label(level):
    """برگرداندن برچسب سطح"""
    labels = {
        1: "فوری و مهم",
        2: "مهم - برنامه‌ریزی",
        3: "غیرمهم - واگذاری",
        4: "حذف/حذف"
    }
    return labels.get(level, "نامشخص")


def detect_task_from_message(text, find_user_func=None):
    """تشخیص آیا پیام یک وظیفه/تسک است"""
    if not text or len(text) < 5:
        return None

    # نرمال‌سازی متن: حذف فاصله‌های اضافی، تبدیل ی/ی به یکدیگر
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'\s+', ' ', text).strip()
    # تبدیل ی عربی به ی فارسی
    text = text.replace('ي', 'ی')
    # حذف کاراکترهای مخفی
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    logger.debug(f"[DETECT] normalized text: {text!r}")

    task_keywords = [
        'بفرست', 'بده', 'انجام بده', 'انجام بدهید', 'تکمیل کن', 'تکمیل کنید',
        'آماده کن', 'آماده کنید', 'جمع کن', 'جمع کنید', 'ارسال کن', 'ارسال کنید',
        'بررسی کن', 'بررسی کنید', 'تهیه کن', 'تهیه کنید', 'درست کن', 'درست کنید',
        'لیست', 'حساب', 'موجودی', 'گزارش', 'چک', 'تسک', 'وظیفه',
        'باید', 'لازم است', 'لازم هست', 'ضروری', 'فوری', 'مهم',
        'تا شنبه', 'تا یکشنبه', 'تا دوشنبه', 'تا سه‌شنبه', 'تا چهارشنبه', 'تا پنجشنبه', 'تا جمعه',
        'تا فردا', 'تا پس فردا', 'تا هفته بعد', 'تا ماه بعد',
        'شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه',
        'فردا', 'پس فردا', 'هفته بعد', 'ماه بعد',
        'برای تیم', 'برای گروه', 'برای بخش',
        'خودم', 'بهم', 'یادم', 'یادآور',
        'آقا', 'خانم', 'آقای',  # کلیدواژه برای تشخیص مسئول انجام
    ]

    is_task = any(kw in text for kw in task_keywords)
    logger.debug(f"[DETECT] is_task={is_task}, keywords found: {[kw for kw in task_keywords if kw in text]}")
    if not is_task:
        return None

    # نقشه ماه‌های شمسی
    persian_months = {
        'فروردین': 1, 'اردیبهشت': 2, 'خرداد': 3, 'تیر': 4,
        'مرداد': 5, 'شهریور': 6, 'مهر': 7, 'آبان': 8,
        'آذر': 9, 'دی': 10, 'بهمن': 11, 'اسفند': 12
    }

    # تشخیص نام کاربر مسئول - بهبود یافته
    assigned_to = ''
    raw_assigned = ''
    is_self = False  # آیا "خودم" یا "بهم" گفته شده

    # تشخیص "خودم" یا "بهم"
    if re.search(r'خودم|بهم|خود\s+ام|بِ?من', text):
        is_self = True
        assigned_to = '__SELF__'  # علامت ویژه برای کاربر فعلی

    # الگوهای استخراج نام - ساده و مستقیم
    # فقط "آقای X" یا "خانم X" رو پیدا کن و X رو برگردون
    name_patterns = [
        r'آقای\s+([\w\u0600-\u06FF]+(?:\s+[\w\u0600-\u06FF]+){0,2})',
        r'خانم\s+([\w\u0600-\u06FF]+(?:\s+[\w\u0600-\u06FF]+){0,2})',
        r'آقا\s+([\w\u0600-\u06FF]+(?:\s+[\w\u0600-\u06FF]+){0,2})',
    ]

    for pat in name_patterns:
        m = re.search(pat, text)
        if m:
            name = m.group(1).strip()
            # پاکسازی ساده
            name = name.strip('.,،!?؟ ')
            name = re.sub(r'\s+(بگو|بده|بفرست|انجام|تکمیل|کن|شو|شود|هست|میشه|بشه|باشه)$', '', name)
            logger.debug(f"[DETECT] pattern matched: {pat!r}, name: {name!r}")
            if len(name) > 1 and len(name) < 30:
                raw_assigned = name
                break

    # جستجو در دیتابیس کاربران برای پیدا کردن نام واقعی
    if raw_assigned and find_user_func:
        found_user = find_user_func(raw_assigned)
        logger.debug(f"[DETECT] find_user({raw_assigned!r}) = {found_user!r}")
        if found_user:
            assigned_to = found_user
        else:
            # اگر نام پیدا نشد، تلاش مجدد با نام پاکسازی شده
            cleaned = raw_assigned.strip()
            # حذف "آقا" یا "خانم" از ابتدا
            cleaned = re.sub(r'^(آقا|خانم|آقای|خانم)\s*', '', cleaned)
            if cleaned and cleaned != raw_assigned:
                found_user = find_user_func(cleaned)
                logger.debug(f"[DETECT] retry find_user({cleaned!r}) = {found_user!r}")
                if found_user:
                    assigned_to = found_user
            # اگر هنوز پیدا نشد، از اسم پیش‌فرض استفاده کن
            if not assigned_to:
                assigned_to = 'محمدی'
                logger.debug(f"[DETECT] using default: محمدی")

    # استخراج ددلاین شمسی - بهبود یافته
    today = jdatetime.date.today()

    # تبدیل اعداد فارسی و حروف فارسی به عدد
    persian_to_num = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        'یک': '1', 'دو': '2', 'سه': '3', 'چهار': '4', 'پنج': '5',
        'شش': '6', 'هفت': '7', 'هشت': '8', 'نه': '9', 'ده': '10',
        'یازده': '11', 'دوازده': '12', 'سیزده': '13', 'چهارده': '14', 'پانزده': '15',
        'شانزده': '16', 'هفده': '17', 'هجده': '18', 'نوزده': '19', 'بیست': '20',
    }

    def convert_persian_numbers(s):
        for fa, en in persian_to_num.items():
            s = s.replace(fa, en)
        # تبدیل اعداد عربی
        for ar, en in [('٠','0'),('١','1'),('٢','2'),('٣','3'),('٤','4'),('٥','5'),('٦','6'),('٧','7'),('٨','8'),('٩','9')]:
            s = s.replace(ar, en)
        return s

    # الگوی "X روز دیگه" یا "X روز بعد"
    days_later_pattern = r'(\d+|[\d۰-۹یکدوسهچهارپنجششهفتهشتنهیدهیازدهدوازدهسیزدهچهاردهپانزدهشانزدههفدههجدهنوزدهبیست]+)\s*روز\s*(?:دیگه|بعد|دیگر)'
    m = re.search(days_later_pattern, text)
    days_later = 0
    if m:
        days_str = convert_persian_numbers(m.group(1))
        try:
            days_later = int(days_str)
        except:
            days_later = 0

    # نقشه روزهای هفته: نام → شماره weekday در jdatetime
    # jdatetime.date.weekday(): 0=شنبه, 1=یکشنبه, 2=دوشنبه, 3=سه‌شنبه, 4=چهارشنبه, 5=پنجشنبه, 6=جمعه
    weekday_map = {
        'شنبه': 0, 'یکشنبه': 1, 'دوشنبه': 2,
        'سه‌شنبه': 3, 'چهارشنبه': 4, 'پنجشنبه': 5, 'جمعه': 6
    }

    deadline_map = {
        'تا فردا': 1, 'فردا': 1, 'تا پس فردا': 2, 'پس فردا': 2,
        'تا شنبه': 0, 'تا یکشنبه': 1, 'تا دوشنبه': 2,
        'تا سه‌شنبه': 3, 'تا چهارشنبه': 4, 'تا پنجشنبه': 5, 'تا جمعه': 6,
        'هفته بعد': 7, 'ماه بعد': 30,
    }

    deadline = ''
    time_given_days = 0  # فرصت داده شده به روز

    # الگوی 0: "تاریخ 10 تیر" یا "تاریخ ۱۰ تیر"
    date_pattern0 = r'تاریخ\s+(\d+|[\d۰-۹]+)\s*(?:ام\s+)?(فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور|مهر|آبان|آذر|دی|بهمن|اسفند)'
    m = re.search(date_pattern0, text)
    if m:
        day_str = m.group(1)
        day_str = day_str.replace('۰', '0').replace('۱', '1').replace('۲', '2').replace('۳', '3').replace('۴', '4')
        day_str = day_str.replace('۵', '5').replace('۶', '6').replace('۷', '7').replace('۸', '8').replace('۹', '9')
        day = int(day_str)
        month_name = m.group(2)
        month = persian_months.get(month_name, 0)
        if month > 0 and 1 <= day <= 31:
            year = today.year
            try:
                target = jdatetime.date(year, month, day)
                if target < today:
                    target = jdatetime.date(year + 1, month, day)
                deadline = f"{target.year}/{target.month:02d}/{target.day:02d}"
            except:
                deadline = f"{year}/{month:02d}/{day:02d}"

    # الگوی 1: "10 تیر" یا "۱۰ تیر" یا "۱۰ام تیر"
    if not deadline:
        date_pattern1 = r'(\d+|[\d۰-۹]+)\s*(?:ام\s+)?(فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور|مهر|آبان|آذر|دی|بهمن|اسفند)'
        m = re.search(date_pattern1, text)
        if m:
            day_str = m.group(1)
            day_str = day_str.replace('۰', '0').replace('۱', '1').replace('۲', '2').replace('۳', '3').replace('۴', '4')
            day_str = day_str.replace('۵', '5').replace('۶', '6').replace('۷', '7').replace('۸', '8').replace('۹', '9')
            day = int(day_str)
            month_name = m.group(2)
            month = persian_months.get(month_name, 0)
            if month > 0 and 1 <= day <= 31:
                year = today.year
                try:
                    target = jdatetime.date(year, month, day)
                    if target < today:
                        target = jdatetime.date(year + 1, month, day)
                    deadline = f"{target.year}/{target.month:02d}/{target.day:02d}"
                except:
                    deadline = f"{year}/{month:02d}/{day:02d}"

    # الگوی 2: "1404/04/10" یا "14040410"
    if not deadline:
        date_pattern2 = r'(\d{4})[/\-\s]?(\d{1,2})[/\-\s]?(\d{1,2})'
        m = re.search(date_pattern2, text)
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 1300 <= y <= 1500 and 1 <= mo <= 12 and 1 <= d <= 31:
                deadline = f"{y}/{mo:02d}/{d:02d}"

    # الگوی 3: "X روز دیگه" یا "X روز بعد"
    if not deadline and days_later > 0:
        target = today + jdatetime.timedelta(days=days_later)
        deadline = f"{target.year}/{target.month:02d}/{target.day:02d}"
        time_given_days = days_later

    # الگوی 4: کلمات کلیدی نسبی (بلندترین اول بررسی شه)
    if not deadline:
        sorted_kw = sorted(deadline_map.keys(), key=len, reverse=True)
        found_kw = False
        for kw in sorted_kw:
            if kw in text:
                val = deadline_map[kw]
                if kw in ('هفته بعد', 'ماه بعد'):
                    target = today + jdatetime.timedelta(days=val)
                    deadline = f"{target.year}/{target.month:02d}/{target.day:02d}"
                    time_given_days = val
                elif kw in ('فردا', 'پس فردا', 'تا فردا', 'تا پس فردا'):
                    target = today + jdatetime.timedelta(days=val)
                    deadline = f"{target.year}/{target.month:02d}/{target.day:02d}"
                    time_given_days = val
                elif kw.startswith('تا '):
                    today_wd = today.weekday()
                    target_wd = val
                    days_ahead = (target_wd - today_wd) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    target = today + jdatetime.timedelta(days=days_ahead)
                    deadline = f"{target.year}/{target.month:02d}/{target.day:02d}"
                    time_given_days = days_ahead
                found_kw = True
                break

        # الگوی 4b: روزهای هفته بدون "تا" (شنبه، یکشنبه، ...)
        if not deadline and not found_kw:
            today_wd = today.weekday()
            logger.debug(f"[DETECT] today={today}, weekday={today_wd}")
            for day_name, target_wd in weekday_map.items():
                if day_name in text:
                    days_ahead = (target_wd - today_wd) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    target = today + jdatetime.timedelta(days=days_ahead)
                    deadline = f"{target.year}/{target.month:02d}/{target.day:02d}"
                    time_given_days = days_ahead
                    logger.debug(f"[DETECT] bare day '{day_name}' target_wd={target_wd}, days_ahead={days_ahead}, deadline={deadline}")
                    break

    logger.debug(f"[DETECT] final: title={text[:50]!r}, deadline={deadline!r}, assigned_to={assigned_to!r}")

    # اگر تاریخی پیدا نشد، امروز باشد
    if not deadline:
        deadline = f"{today.year}/{today.month:02d}/{today.day:02d}"

    # محاسبه خودکار فرصت داده شده (اختلاف امروز با موعد)
    if deadline and time_given_days == 0:
        try:
            parts = deadline.split('/')
            if len(parts) == 3:
                dl_year, dl_month, dl_day = int(parts[0]), int(parts[1]), int(parts[2])
                dl_date = jdatetime.date(dl_year, dl_month, dl_day)
                diff = (dl_date - today).days
                time_given_days = max(diff, 0)
        except:
            pass

    # تشخیص فوریت
    urgency = "غیر فوری"
    if any(w in text for w in ['فوری', 'ضروری', 'خیلی مهم', 'الان', 'فورا']):
        urgency = "فوری"

    # تشخیص اهمیت
    priority = "مهم"
    if any(w in text for w in ['فوری', 'ضروری', 'خیلی مهم']):
        priority = "مهم"
    elif any(w in text for w in ['عادی', 'مهم نیست', 'غیر مهم']):
        priority = "غیر مهم"

    # محاسبه سطح آیزنهاور
    level = calculate_eisenhower_level(priority, urgency)

    return {"title": text[:100], "notes": text, "deadline": deadline,
            "priority": priority, "urgency": urgency, "level": level,
            "assigned_to": assigned_to, "time_given": str(time_given_days) if time_given_days > 0 else ''}


def create_task_from_message(text, sender_id, receiver_id=None):
    """ایجاد تسک خودکار از پیام"""
    # تابع جستجوی کاربر
    def find_user_in_db(name):
        con = get_db()
        user = con.execute("""SELECT full_name FROM users WHERE
            full_name LIKE ? OR full_name LIKE ? OR username LIKE ?
            ORDER BY CASE
                WHEN full_name = ? THEN 1
                WHEN full_name LIKE ? THEN 2
                ELSE 3
            END LIMIT 1""",
            (name, f"%{name}%", name, name, f"%{name}%")).fetchone()
        con.close()
        return user['full_name'] if user else None

    task_data = detect_task_from_message(text, find_user_in_db)
    if not task_data:
        return None

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = jdatetime.date.today()
    con = get_db()
    sender = con.execute("SELECT full_name FROM users WHERE id=?", (sender_id,)).fetchone()
    sender_name = sender['full_name'] if sender else ""

    # اگر "خودم" یا "بهم" گفته شده، نام فرستنده رو قرار بده
    if task_data.get('assigned_to') == '__SELF__':
        task_data['assigned_to'] = sender_name

    # اگر مسئولی مشخص نشده و receiver_id داریم، خودکار مسئول را تنظیم کن
    if not task_data.get('assigned_to') and receiver_id:
        receiver = con.execute("SELECT full_name FROM users WHERE id=?", (receiver_id,)).fetchone()
        if receiver:
            task_data['assigned_to'] = receiver['full_name']

    # اگر هنوز مسئولی نیست، از نام استخراج شده استفاده کن
    if not task_data.get('assigned_to'):
        assigned_name = task_data.get('assigned_to', '')
        if assigned_name:
            found = find_user_in_db(assigned_name)
            if found:
                task_data['assigned_to'] = found

    # اگر تاریخی نیست، امروز باشد
    if not task_data.get('deadline'):
        task_data['deadline'] = f"{today.year}/{today.month:02d}/{today.day:02d}"

    con.execute("""INSERT INTO tasks(title,requester,assigned_to,priority,urgency,level,status,deadline,notes,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (task_data['title'], sender_name, task_data.get('assigned_to', ''),
         task_data.get('priority', 'مهم'), task_data.get('urgency', 'غیر فوری'),
         task_data.get('level', 3),
         'در حال انجام', task_data['deadline'], task_data['notes'], now, now))
    task_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.commit()

    # آلارم
    con.execute("INSERT INTO alarms(task_id,user_id,message,alarm_time) VALUES(?,?,?,?)",
                (task_id, sender_id, f"تسک خودکار: {task_data['title'][:50]}", now))
    con.commit(); con.close()
    return task_id


@app.route('/api/ai/parse-message', methods=['POST'])
@login_required
def ai_parse_message():
    """تشخیص پیام به عنوان تسک"""
    try:
        text = request.json.get('text', '')
        print(f"[AI] text={text!r}")

        # تابع جستجوی کاربر
        def find_user_in_db(name):
            con = get_db()
            user = con.execute("""SELECT full_name FROM users WHERE
                full_name LIKE ? OR full_name LIKE ? OR full_name LIKE ? OR username LIKE ?
                ORDER BY CASE
                    WHEN full_name = ? THEN 1
                    WHEN full_name LIKE ? THEN 2
                    WHEN full_name LIKE ? THEN 3
                    ELSE 4
                END LIMIT 1""",
                (name, f"%{name}%", f"%{name}%", name, name, f"{name}%", f"%{name}%")).fetchone()
            con.close()
            return user['full_name'] if user else None

        result = detect_task_from_message(text, find_user_in_db)
        print(f"[AI] result={result}")
        if result:
            return jsonify({"is_task": True, "data": result})
        return jsonify({"is_task": False})
    except Exception as e:
        print(f"[AI] ERROR: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"is_task": False, "error": str(e)})


@app.route('/api/ai/create-task-from-chat', methods=['POST'])
@login_required
def ai_create_task_from_chat():
    """ایجاد تسک از پیام چت"""
    text = request.json.get('text', '')
    receiver_id = request.json.get('receiver_id')  # مسئول خودکار
    task_id = create_task_from_message(text, request.user_id, receiver_id)
    if task_id:
        return jsonify({"ok": True, "task_id": task_id})
    return jsonify({"ok": False, "error": "پیام به عنوان تسک تشخیص داده نشد"})


@app.route('/api/ai/voice-to-task-from-chat', methods=['POST'])
@login_required
def voice_to_task_from_chat():
    """تبدیل پیام صوتی چت به وظیفه"""
    if 'voice' not in request.files:
        return jsonify({"error": "فایل صوتی یافت نشد"}), 400

    voice = request.files['voice']
    receiver_id = request.form.get('receiver_id')  # مسئول خودکار

    try:
        recognizer = sr.Recognizer()
        audio_data = BytesIO(voice.read())
        with sr.AudioFile(audio_data) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language='fa-IR')

        # تابع جستجوی کاربر
        def find_user_in_db(name):
            con = get_db()
            user = con.execute("""SELECT full_name FROM users WHERE
                full_name LIKE ? OR full_name LIKE ? OR username LIKE ?
                LIMIT 1""", (name, f"%{name}%", name)).fetchone()
            con.close()
            return user['full_name'] if user else None

        # اگر receiver_id داریم، نام کاربر را پیدا کن
        assigned_to = ''
        if receiver_id:
            con = get_db()
            receiver = con.execute("SELECT full_name FROM users WHERE id=?", (receiver_id,)).fetchone()
            con.close()
            if receiver:
                assigned_to = receiver['full_name']

        result = detect_task_from_message(text, find_user_in_db)
        if not result:
            today = jdatetime.date.today()
            result = {
                "title": text[:100] if text else "وظیفه جدید",
                "notes": text,
                "priority": "مهم",
                "urgency": "غیر فوری",
                "level": 3,
                "deadline": f"{today.year}/{today.month:02d}/{today.day:02d}",
                "assigned_to": assigned_to
            }
        else:
            # اگر مسئولی از متن استخراج نشد، از receiver استفاده کن
            if not result.get('assigned_to') and assigned_to:
                result['assigned_to'] = assigned_to

        # ایجاد تسک
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        con = get_db()
        sender = con.execute("SELECT full_name FROM users WHERE id=?", (request.user_id,)).fetchone()

        con.execute("""INSERT INTO tasks(title,requester,assigned_to,priority,urgency,level,status,deadline,notes,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (result['title'], sender['full_name'] if sender else '',
             result.get('assigned_to', ''), result.get('priority', 'مهم'),
             result.get('urgency', 'غیر فوری'), result.get('level', 3),
             'در حال انجام', result.get('deadline', ''), result.get('notes', ''), now, now))
        task_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        con.commit()

        # آلارم
        con.execute("INSERT INTO alarms(task_id,user_id,message,alarm_time) VALUES(?,?,?,?)",
                    (task_id, request.user_id, f"تسک از صدا: {result['title'][:50]}", now))
        con.commit()
        con.close()

        return jsonify({
            "ok": True,
            "task_id": task_id,
            "title": result['title'],
            "assigned_to": result.get('assigned_to', ''),
            "deadline": result.get('deadline', ''),
            "raw_text": text
        })

    except sr.UnknownValueError:
        return jsonify({"error": "صدا قابل تشخیص نیست"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════
#  ALARM هنگام تکمیل تسک
# ═══════════════════════════════════════════════

def send_completion_alarm(task_id):
    """ارسال آلارم هنگام تکمیل تسک - به مسئول انجام و مرجع"""
    con = get_db()
    task = con.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if task and task['status'] == 'تکمیل':
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        assigned = task['assigned_to'] or ''
        requester = task['requester'] or ''
        msg = f"تسک «{task['title'][:40]}» تکمیل شد"

        # آلارم برای مسئول انجام
        assignee = con.execute("SELECT id FROM users WHERE full_name=? OR username=?", (assigned, assigned)).fetchone()
        if assignee:
            con.execute("INSERT INTO alarms(task_id,user_id,message,alarm_time) VALUES(?,?,?,?)",
                        (task_id, assignee['id'], msg, now))
            socketio.emit('alarm', {"message": msg, "task_id": task_id}, room=f"user_{assignee['id']}")

        # آلارم برای مرجع
        if requester and requester != assigned:
            req_user = con.execute("SELECT id FROM users WHERE full_name=?", (requester,)).fetchone()
            if req_user:
                con.execute("INSERT INTO alarms(task_id,user_id,message,alarm_time) VALUES(?,?,?,?)",
                            (task_id, req_user['id'], msg, now))
                socketio.emit('alarm', {"message": msg, "task_id": task_id}, room=f"user_{req_user['id']}")

        # پیام تکمیل در چت (به همه اتاق‌ها)
        completion_msg = {
            "type": "task_completion",
            "task_id": task_id,
            "title": task['title'],
            "assigned_to": assigned,
            "requester": requester,
            "message": msg,
            "created_at": now
        }
        socketio.emit('task_completed_card', completion_msg)

        con.commit()
    con.close()


# ═══════════════════════════════════════════════
#  RECENT DM CONTACTS
# ═══════════════════════════════════════════════

@app.route('/api/dm/contacts')
@login_required
def get_dm_contacts():
    """لیست مخاطبین اخیر با آخرین پیام"""
    con = get_db()
    my_id = request.user_id

    rows = con.execute("""
        SELECT u.id, u.full_name, u.username, u.role,
            sub.last_content, sub.last_time, sub.last_sender, sub.unread_count
        FROM users u
        INNER JOIN (
            SELECT
                CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END as other_id,
                content as last_content,
                created_at as last_time,
                sender_id as last_sender,
                SUM(CASE WHEN sender_id != ? AND is_read = 0 THEN 1 ELSE 0 END) as unread_count
            FROM direct_messages
            WHERE sender_id = ? OR receiver_id = ?
            GROUP BY other_id
            ORDER BY last_time DESC
        ) sub ON u.id = sub.other_id
        WHERE u.is_active = 1
        ORDER BY sub.last_time DESC
        LIMIT 30
    """, (my_id, my_id, my_id, my_id)).fetchall()
    con.close()

    result = []
    for r in rows:
        d = dict(r)
        # نمایش خلاصه پیام (صوتی یا متن)
        if d.get('last_content'):
            d['preview'] = d['last_content'][:50]
        else:
            d['preview'] = '🎤 پیام صوتی'
        result.append(d)

    return jsonify(result)


# ═══════════════════════════════════════════════
#  USER SETTINGS (THEME)
# ═══════════════════════════════════════════════

@app.route('/api/settings', methods=['GET'])
@login_required
def get_user_settings():
    """دریافت تنظیمات کاربر"""
    con = get_db()
    row = con.execute("SELECT * FROM user_settings WHERE user_id=?", (request.user_id,)).fetchone()
    con.close()
    if row:
        return jsonify({"theme": row['theme'], "font_size": row['font_size']})
    return jsonify({"theme": "dark_neon", "font_size": "normal"})


@app.route('/api/settings', methods=['PUT'])
@login_required
def update_user_settings():
    """بروزرسانی تنظیمات کاربر"""
    data = request.json
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    theme = data.get('theme', 'dark_neon')
    font_size = data.get('font_size', 'normal')

    con = get_db()
    existing = con.execute("SELECT 1 FROM user_settings WHERE user_id=?", (request.user_id,)).fetchone()
    if existing:
        con.execute("UPDATE user_settings SET theme=?, font_size=?, updated_at=? WHERE user_id=?",
                    (theme, font_size, now, request.user_id))
    else:
        con.execute("INSERT INTO user_settings(user_id, theme, font_size, created_at, updated_at) VALUES(?,?,?,?,?)",
                    (request.user_id, theme, font_size, now, now))
    con.commit()
    con.close()
    return jsonify({"ok": True})


# ═══════════════════════════════════════════════
#  DEBUG LOG VIEWER
# ═══════════════════════════════════════════════

@app.route('/api/debug/log')
@login_required
def get_debug_log():
    """نمایش آخرین لاگ‌ها"""
    try:
        logger.debug("[DEBUG] log viewer called")
        if not os.path.exists(LOG_FILE):
            return jsonify({"log": f"فایل لاگ وجود ندارد: {LOG_FILE}", "path": LOG_FILE})
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        last_lines = lines[-100:] if len(lines) > 100 else lines
        return jsonify({"log": ''.join(last_lines), "total_lines": len(lines), "path": LOG_FILE})
    except Exception as e:
        return jsonify({"log": f"خطا در خواندن لاگ: {e}", "path": LOG_FILE})


@app.route('/api/debug/test')
@login_required
def debug_test():
    """تست لاگ"""
    logger.debug("[DEBUG] test endpoint called")
    logger.info("[DEBUG] this is an info message")
    logger.warning("[DEBUG] this is a warning message")
    return jsonify({"ok": True, "log_file": LOG_FILE})


# ═══════════════════════════════════════════════
#  FRONTEND
# ═══════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    # ایجاد پوشه‌های مورد نیاز
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER']), exist_ok=True)
    init_db()
    logger.info("=" * 50)
    logger.info("  مدیریت امور - بازرگانی محسنی")
    logger.info(f"  Log file: {LOG_FILE}")
    logger.info("  http://localhost:5000")
    logger.info("  کاربر: admin / admin123")
    logger.info("=" * 50)
    print("=" * 50)
    print("  مدیریت امور - بازرگانی محسنی")
    print(f"  Log file: {LOG_FILE}")
    print("  http://localhost:5000")
    print("  کاربر: admin / admin123")
    print("=" * 50)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
