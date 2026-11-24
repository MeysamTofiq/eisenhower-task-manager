"""
مدیریت امور - بازرگانی محسنی
فایل اصلی برای کامپایل به EXE مستقل
"""
import os
import sys
import json
import subprocess
import shutil

# ═══════════════════════════════════════════════
#  مسیرها
# ═══════════════════════════════════════════════

def get_base_dir():
    """مسیر پوشه جاری (جایی که EXE اجرا شده)"""
    if getattr(sys, 'frozen', False):
        # وقتی به EXE کامپایل شده
        return os.path.dirname(sys.executable)
    else:
        # وقتی به صورت پایتون اجرا میشه
        return os.path.dirname(os.path.abspath(__file__))


def get_app_dir():
    """مسیر پوشه flask_app"""
    base = get_base_dir()
    app_dir = os.path.join(base, 'flask_app')
    if not os.path.exists(app_dir):
        os.makedirs(app_dir, exist_ok=True)
    return app_dir


# ═══════════════════════════════════════════════
#  استخراج فایل‌ها از EXE
# ═══════════════════════════════════════════════

def extract_app_files():
    """استخراج فایل‌های اپلیکیشن از منابع داخلی"""
    app_dir = get_app_dir()
    base_dir = get_base_dir()

    # اگر فایل‌ها قبلاً استخراج شده‌اند
    if os.path.exists(os.path.join(app_dir, 'app.py')):
        return True

    # مسیر منابع داخلی (وقتی با PyInstaller کامپایل شده)
    if getattr(sys, 'frozen', False):
        # PyInstaller فایل‌ها را در _MEIPASS ذخیره می‌کند
        src_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        src_dir = os.path.dirname(os.path.abspath(__file__))

    # کپی فایل‌ها
    files_to_copy = [
        ('flask_app/app.py', 'app.py'),
        ('flask_app/jalali_utils.py', 'jalali_utils.py'),
        ('flask_app/requirements.txt', 'requirements.txt'),
        ('flask_app/templates/index.html', 'templates/index.html'),
        ('flask_app/static/js/app.jsx', 'static/js/app.jsx'),
        ('flask_app/static/css/style.css', 'static/css/style.css'),
    ]

    # ایجاد پوشه‌ها
    os.makedirs(os.path.join(app_dir, 'templates'), exist_ok=True)
    os.makedirs(os.path.join(app_dir, 'static', 'js'), exist_ok=True)
    os.makedirs(os.path.join(app_dir, 'static', 'css'), exist_ok=True)
    os.makedirs(os.path.join(app_dir, 'uploads'), exist_ok=True)

    for src_rel, dst_rel in files_to_copy:
        src = os.path.join(src_dir, src_rel)
        dst = os.path.join(app_dir, dst_rel)
        if os.path.exists(src):
            shutil.copy2(src, dst)

    return True


# ═══════════════════════════════════════════════
#  تنظیمات
# ═══════════════════════════════════════════════

def load_config():
    """خواندن تنظیمات از فایل"""
    app_dir = get_app_dir()
    config_path = os.path.join(app_dir, 'config.json')

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass

    return None


def save_config(config):
    """ذخیره تنظیمات در فایل"""
    app_dir = get_app_dir()
    config_path = os.path.join(app_dir, 'config.json')

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def setup_wizard():
    """جادوی راه‌اندازی اولیه"""
    print("=" * 60)
    print("  مدیریت امور - بازرگانی محسنی")
    print("  راه‌اندازی اولیه")
    print("=" * 60)
    print()

    # ۱. پورت
    while True:
        port_str = input("شماره پورت سرور [5000]: ").strip()
        if not port_str:
            port = 5000
            break
        try:
            port = int(port_str)
            if 1 <= port <= 65535:
                break
            print("  خطا: پورت باید بین 1 تا 65535 باشد")
        except ValueError:
            print("  خطا: لطفاً یک عدد معتبر وارد کنید")

    # ۲. رمز ادمین
    while True:
        pw = input("رمز عبور ادمین [admin123]: ").strip()
        if not pw:
            admin_password = 'admin123'
            break
        if len(pw) >= 4:
            admin_password = pw
            break
        print("  خطا: رمز باید حداقل ۴ کاراکتر باشد")

    # ۳. نمایش خلاصه
    print()
    print(f"  پورت: {port}")
    print(f"  رمز ادمین: {'***' if admin_password != 'admin123' else 'admin123'}")
    print()
    confirm = input("  تایید می‌کنید؟ (y/n): ").strip().lower()
    if confirm != 'y':
        print("\n  لغو شد.")
        input("  Enter را بزنید...")
        sys.exit(0)

    # ذخیره تنظیمات
    config = {
        "port": port,
        "admin_password": admin_password,
        "host": "0.0.0.0"
    }
    save_config(config)
    print("\n  تنظیمات ذخیره شد.")
    return config


# ═══════════════════════════════════════════════
#  نصب وابستگی‌ها
# ═══════════════════════════════════════════════

def install_dependencies():
    """نصب وابستگی‌های مورد نیاز"""
    app_dir = get_app_dir()
    req_path = os.path.join(app_dir, 'requirements.txt')

    if not os.path.exists(req_path):
        return

    print("\n  در حال بررسی وابستگی‌ها...")

    # لیست وابستگی‌های مورد نیاز
    required = ['flask', 'flask-socketio', 'werkzeug', 'openpyxl', 'jdatetime', 'speechrecognition']

    # بررسی نصب بودن
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)

    if not missing:
        print("  تمام وابستگی‌ها نصب هستند.")
        return

    print(f"  در حال نصب {len(missing)} بسته...")
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install'] + missing + ['-q'],
            capture_output=True,
            timeout=180
        )
        print("  وابستگی‌ها نصب شدند.")
    except Exception as e:
        print(f"  خطا در نصب وابستگی‌ها: {e}")
        print("  لطفاً دستی نصب کنید:")
        print(f"    pip install {' '.join(missing)}")


# ═══════════════════════════════════════════════
#  اجرای سرور
# ═══════════════════════════════════════════════

def run_server(config):
    """اجرای سرور Flask"""
    app_dir = get_app_dir()

    # تغییر مسیر کاری به پوشه flask_app
    os.chdir(app_dir)

    # اضافه کردن مسیر به sys.path
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    # ایجاد پوشه uploads
    uploads_dir = os.path.join(app_dir, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

    port = config.get('port', 5000)
    admin_password = config.get('admin_password', 'admin123')

    print()
    print("=" * 60)
    print("  مدیریت امور - بازرگانی محسنی")
    print("=" * 60)
    print(f"  آدرس سرور: http://localhost:{port}")
    print(f"  آدرس شبکه: http://0.0.0.0:{port}")
    print(f"  کاربر: admin")
    print(f"  رمز: {'***' if admin_password != 'admin123' else 'admin123'}")
    print("=" * 60)
    print()
    print("  مرورگر را باز کنید: http://localhost:" + str(port))
    print("  برای توقف: Ctrl+C")
    print()

    # وارد کردن و اجرای اپ
    try:
        # وارد کردن ماژول‌های مورد نیاز
        import flask
        import flask_socketio
        import werkzeug
        import openpyxl
        import jdatetime

        # حالا app.py رو اجرا کن
        app_module_path = os.path.join(app_dir, 'app.py')
        with open(app_module_path, 'r', encoding='utf-8') as f:
            app_code = f.read()

        # اجرای کد app.py
        exec(compile(app_code, app_module_path, 'exec'), {'__name__': '__main__', '__file__': app_module_path})

    except KeyboardInterrupt:
        print("\n  سرور متوقف شد.")
    except Exception as e:
        print(f"\n  خطا در اجرای سرور: {e}")
        import traceback
        traceback.print_exc()
        input("\n  Enter را بزنید...")


# ═══════════════════════════════════════════════
#  اصلی
# ═══════════════════════════════════════════════

def main():
    """تابع اصلی"""
    try:
        # ۱. استخراج فایل‌ها
        extract_app_files()

        # ۲. خواندن تنظیمات
        config = load_config()

        # ۳. اگر تنظیمات نیست، جادوی راه‌اندازی
        if not config:
            config = setup_wizard()

        # ۴. نصب وابستگی‌ها
        install_dependencies()

        # ۵. اجرای سرور
        run_server(config)

    except Exception as e:
        print(f"\nخطای غیرمنتظره: {e}")
        import traceback
        traceback.print_exc()
        input("\nEnter را بزنید...")


if __name__ == '__main__':
    main()
