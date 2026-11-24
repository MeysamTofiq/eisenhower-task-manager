"""
نسخه ساده Setup برای تبدیل به EXE
"""
import os
import sys
import shutil
import json
import subprocess

def main():
    print("=" * 50)
    print("  نصب‌کننده مدیریت امور - بازرگانی محسنی")
    print("=" * 50)
    print()

    # ۱. مسیر نصب
    default_dir = os.path.join(os.path.expanduser('~'), 'Aizenhaver')
    install_dir = input(f"مسیر نصب [{default_dir}]: ").strip()
    if not install_dir:
        install_dir = default_dir

    # ۲. پورت
    port_str = input("شماره پورت [5000]: ").strip()
    port = int(port_str) if port_str.isdigit() else 5000

    # ۳. رمز ادمین
    admin_pw = input("رمز عبور ادمین [admin123]: ").strip()
    if not admin_pw:
        admin_pw = 'admin123'

    print()
    print(f"مسیر: {install_dir}")
    print(f"پورت: {port}")
    print(f"رمز: {'***' if admin_pw != 'admin123' else admin_pw}")
    print()

    confirm = input("تایید می‌کنید؟ (y/n): ").strip().lower()
    if confirm != 'y':
        print("لغو شد.")
        input("Enter را بزنید...")
        return

    # شروع نصب
    print("\nدر حال نصب...")

    # مسیر سورس (جایی که setup_gui.py اجرا شده)
    if getattr(sys, 'frozen', False):
        source_dir = os.path.dirname(sys.executable)
    else:
        source_dir = os.path.dirname(os.path.abspath(__file__))

    flask_app_src = os.path.join(source_dir, 'flask_app')

    # ایجاد پوشه‌ها
    dirs = [
        os.path.join(install_dir, 'flask_app'),
        os.path.join(install_dir, 'flask_app', 'uploads'),
        os.path.join(install_dir, 'flask_app', 'static'),
        os.path.join(install_dir, 'flask_app', 'static', 'js'),
        os.path.join(install_dir, 'flask_app', 'static', 'css'),
        os.path.join(install_dir, 'flask_app', 'templates'),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # کپی فایل‌ها
    files_to_copy = [
        ('flask_app/app.py', 'flask_app/app.py'),
        ('flask_app/jalali_utils.py', 'flask_app/jalali_utils.py'),
        ('flask_app/requirements.txt', 'flask_app/requirements.txt'),
        ('flask_app/templates/index.html', 'flask_app/templates/index.html'),
        ('flask_app/static/js/app.jsx', 'flask_app/static/js/app.jsx'),
        ('flask_app/static/css/style.css', 'flask_app/static/css/style.css'),
    ]

    copied = 0
    for src_rel, dst_rel in files_to_copy:
        src = os.path.join(source_dir, src_rel)
        dst = os.path.join(install_dir, dst_rel)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied += 1
            print(f"  ✓ {src_rel}")
        else:
            print(f"  ✗ {src_rel} (یافت نشد)")

    print(f"\n{copied} فایل کپی شد")

    # ایجاد config.json
    config = {"port": port, "admin_password": admin_pw, "host": "0.0.0.0"}
    config_path = os.path.join(install_dir, 'flask_app', 'config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print("✓ فایل تنظیمات ایجاد شد")

    # ایجاد run.bat
    bat = f'''@echo off
chcp 65001 >nul
title مدیریت امور - بازرگانی محسنی
echo ========================================
echo   مدیریت امور - بازرگانی محسنی
echo   پورت: {port}
echo   آدرس: http://localhost:{port}
echo ========================================
echo.
cd /d "{install_dir}\\flask_app"
python app.py
pause
'''
    with open(os.path.join(install_dir, 'run.bat'), 'w', encoding='utf-8-sig') as f:
        f.write(bat)
    print("✓ فایل run.bat ایجاد شد")

    # ایجاد start_silent.bat برای Task Scheduler
    silent_bat = f'''@echo off
chcp 65001 >nul
cd /d "{install_dir}\\flask_app"
start /B python app.py > nul 2>&1
'''
    with open(os.path.join(install_dir, 'start_silent.bat'), 'w', encoding='utf-8-sig') as f:
        f.write(silent_bat)
    print("✓ فایل start_silent.bat ایجاد شد")

    # ایجاد فایل رجیستری startup
    reg = f'''Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run]
"Aizenhaver"="{os.path.join(install_dir, 'start_silent.bat')}"
'''
    with open(os.path.join(install_dir, 'add_to_startup.reg'), 'w', encoding='utf-8-sig') as f:
        f.write(reg)
    print("✓ فایل add_to_startup.reg ایجاد شد")

    # نصب وابستگی‌ها
    print("\nدر حال نصب وابستگی‌ها...")
    req_path = os.path.join(install_dir, 'flask_app', 'requirements.txt')
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', req_path, '-q'],
                      capture_output=True, timeout=120)
        print("✓ وابستگی‌ها نصب شدند")
    except:
        print("! خطا در نصب وابستگی‌ها - دستی نصب کنید")

    # خلاصه
    print("\n" + "=" * 50)
    print("  نصب با موفقیت انجام شد!")
    print("=" * 50)
    print(f"""
مسیر نصب: {install_dir}

نحوه اجرا:
  1. دستی: روی run.bat کلیک کنید
  2. خودکار: add_to_startup.reg را اجرا کنید
  3. Task Scheduler: start_silent.bat را schedule کنید

آدرس: http://localhost:{port}
لاگین: admin / {admin_pw}

برای دسترسی از خارج شبکه:
  - MikroTik: پورت {port} را فوروارد کنید
  - آدرس: http://IP_عمومی_مودم:{port}
""")
    input("Enter را بزنید...")


if __name__ == '__main__':
    main()
