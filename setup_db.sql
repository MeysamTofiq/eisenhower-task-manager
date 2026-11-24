-- setup_db.sql – ایجاد دیتابیس PostgreSQL
-- این فایل را یکبار اجرا کنید: psql -U postgres -f setup_db.sql

-- ایجاد دیتابیس (اگر وجود نداشته باشد)
SELECT 'CREATE DATABASE mohseni_tasks'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mohseni_tasks')\gexec

-- اتصال به دیتابیس
\c mohseni_tasks

-- ایجاد جداول
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
    ack INTEGER DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS notes_board (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    note_date TEXT DEFAULT '',
    created_at TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    section_id INTEGER REFERENCES sections(id),
    sender_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS daily_progress (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id),
    user_id INTEGER REFERENCES users(id),
    progress_pct REAL DEFAULT 0.0,
    notes TEXT DEFAULT '',
    report_date VARCHAR(8) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- کاربر ادمین پیش‌فرض (رمز: admin123)
-- هش رمز در کد Python تولید می‌شود، اینجا فقط مثال است:
-- INSERT INTO users(username,password_hash,full_name,role)
-- VALUES('admin','pbkdf2:sha256:...','مدیر سیستم','admin')
-- برای ایجاد ادمین، برنامه را یکبار اجرا کنید (auto-create)
