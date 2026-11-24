# مدیر وظایف ماتریس آیزنهاور (Eisenhower Task Manager)

## معرفی (فارسی)

برنامه **مدیریت وظایف** مبتنی بر **ماتریس آیزنهاور** (فوری/مهم) — نسخه تحت وب که **چت هم دارد** و کاربران به یکدیگر پیام می‌دهند. این نسخه پیش‌زمینه توسعه بعدهای سامانه AIPERSONS است و انتشار عمومی آن آزاد است.

### ویژگی‌ها

- 🎯 ماتریس آیزنهاور: وظایف در چهار ربع (فوری و مهم / فوری و غیرمهم / ...)
- 💬 چت داخلی: کاربران به هم پیام می‌دهند (SocketIO — بلادرنگ)
- 🗓 تقویم شمسی (jdatetime)
- 🎤 ورودی صوتی (Google Speech Recognition — fa-IR)
- 👥 چند کاربر با نقش‌ها و صفحه ورود
- 📥 وارد کردن وظایف از اکسل (`import_excel.py`)
- 🌐 رابط React در مرورگر + بک‌اند Flask + دیتابیس SQLite

### فناوری

Flask · SocketIO · SQLite · React (JSX) · jdatetime · Google Speech (fa-IR)

### اجرا

```bash
run_flask.bat      # یا:
pip install -r requirements.txt
python flask_app/app.py
# آدرس: http://localhost:5000  |  کاربر پیش‌فرض: admin / admin123
```

### ساختار اصلی

```
flask_app/app.py          ← بک‌اند (API + SocketIO)
flask_app/static/js/app.jsx   ← فرانت‌اند (React)
flask_app/templates/index.html
flask_app/jalali_utils.py ← توابع تقویم شمسی
```

> 📌 تاریخچه کامل نسخه‌ها در `HISTORY.md` (تا v2.2.3)

---

# Eisenhower Matrix Task Manager

## Overview (English)

A **task manager** built on the **Eisenhower Matrix** (urgent/important) — a web app that also includes **built-in chat**, so users can message each other. This project later evolved into the AIPERSONS system; publishing it publicly is intentional.

### Features

- 🎯 Eisenhower matrix: tasks across four quadrants
- 💬 Real-time chat between users (SocketIO)
- 🗓 Jalali (Persian) calendar
- 🎤 Voice input (Google Speech Recognition — fa-IR)
- 👥 Multi-user with roles and login screen
- 📥 Excel task import
- 🌐 React-in-browser frontend + Flask backend + SQLite

### Tech Stack

Flask · SocketIO · SQLite · React (JSX) · jdatetime · Google Speech (fa-IR)

### Run

```bash
pip install -r requirements.txt
python flask_app/app.py
# URL: http://localhost:5000  |  default user: admin / admin123
```
