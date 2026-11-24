"""
نصب‌کننده مدیریت امور - بازرگانی محسنی
این اسکریپت برنامه را در پوشه مورد نظر نصب می‌کند
"""
import os
import sys
import shutil
import json
import subprocess
import getpass

# ═══════════════════════════════════════════════
#  رنگ‌ها برای کنسول
# ═══════════════════════════════════════════════
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*50}")
    print(f"  {text}")
    print(f"{'='*50}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")


# ═══════════════════════════════════════════════
#  فایل‌هایی که باید کپی شوند
# ═══════════════════════════════════════════════
SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
FLASK_APP_DIR = os.path.join(SOURCE_DIR, 'flask_app')

FILES_TO_COPY = [
    'flask_app/app.py',
    'flask_app/jalali_utils.py',
    'flask_app/requirements.txt',
    'flask_app/templates/index.html',
    'flask_app/static/js/app.jsx',
    'flask_app/static/css/style.css',
    'db.py',
    'jalali_utils.py',
    'import_excel.py',
    'requirements.txt',
]

DIRS_TO_CREATE = [
    'flask_app/uploads',
    'flask_app/static/js',
    'flask_app/static/css',
    'flask_app/templates',
]


def get_install_dir():
    """دریافت مسیر نصب از کاربر"""
    default_dir = os.path.join(os.path.expanduser('~'), 'Aizenhaver')
    print_info(f"مسیر پیش‌فرض: {default_dir}")
    path = input(f"مسیر نصب را وارد کنید (Enter = پیش‌فرض): ").strip()
    if not path:
        path = default_dir
    return path


def get_port():
    """دریافت شماره پورت از کاربر"""
    while True:
        port = input("شماره پورت سرور را وارد کنید (Enter = 5000): ").strip()
        if not port:
            return 5000
        try:
            port = int(port)
            if 1 <= port <= 65535:
                return port
            print_error("پورت باید بین 1 تا 65535 باشد")
        except ValueError:
            print_error("لطفاً یک عدد معتبر وارد کنید")


def get_admin_password():
    """دریافت رمز عبور ادمین از کاربر"""
    while True:
        pw = input("رمز عبور ادمین را وارد کنید (Enter = admin123): ").strip()
        if not pw:
            return 'admin123'
        if len(pw) >= 4:
            return pw
        print_error("رمز عبور باید حداقل ۴ کاراکتر باشد")


def copy_files(install_dir):
    """کپی فایل‌ها به پوشه نصب"""
    print_info("در حال کپی فایل‌ها...")

    # ایجاد پوشه‌ها
    for d in DIRS_TO_CREATE:
        os.makedirs(os.path.join(install_dir, d), exist_ok=True)

    # کپی فایل‌ها
    copied = 0
    for f in FILES_TO_COPY:
        src = os.path.join(SOURCE_DIR, f)
        dst = os.path.join(install_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied += 1
        else:
            print_error(f"فایل یافت نشد: {f}")

    print_success(f"{copied} فایل کپی شد")
    return copied


def create_config(install_dir, port, admin_password):
    """ایجاد فایل config.json"""
    config = {
        "port": port,
        "admin_password": admin_password,
        "host": "0.0.0.0"
    }
    config_path = os.path.join(install_dir, 'flask_app', 'config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print_success(f"فایل تنظیمات ایجاد شد: {config_path}")


def create_batch_file(install_dir, port):
    """ایجاد فایل bat برای اجرای برنامه"""
    bat_content = f'''@echo off
chcp 65001 >nul
title مدیریت امور - بازرگانی محسنی
echo ========================================
echo   مدیریت امور - بازرگانی محسنی
echo   پورت: {port}
echo   آدرس: http://localhost:{port}
echo ========================================
echo.
echo در حال راه‌اندازی سرور...
echo مرورگر را باز کنید: http://localhost:{port}
echo.
cd /d "{install_dir}\\flask_app"
python app.py
pause
'''
    bat_path = os.path.join(install_dir, 'run.bat')
    with open(bat_path, 'w', encoding='utf-8-sig') as f:
        f.write(bat_content)
    print_success(f"فایل اجرا ایجاد شد: {bat_path}")


def create_task_scheduler_bat(install_dir, port):
    """ایجاد فایل bat برای Task Scheduler"""
    bat_content = f'''@echo off
chcp 65001 >nul
cd /d "{install_dir}\\flask_app"
start /B python app.py > nul 2>&1
'''
    bat_path = os.path.join(install_dir, 'start_silent.bat')
    with open(bat_path, 'w', encoding='utf-8-sig') as f:
        f.write(bat_content)
    print_success(f"فایل Task Scheduler ایجاد شد: {bat_path}")


def create_startup_registry(install_dir, port):
    """ایجاد فایل رجیستری برای اجرای خودکار در startup"""
    bat_path = os.path.join(install_dir, 'start_silent.bat')
    reg_content = f'''Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run]
"Aizenhaver"="{bat_path}"
'''
    reg_path = os.path.join(install_dir, 'add_to_startup.reg')
    with open(reg_path, 'w', encoding='utf-8-sig') as f:
        f.write(reg_content)
    print_success(f"فایل رجیستری startup ایجاد شد: {reg_path}")


def create_task_scheduler_xml(install_dir, port):
    """ایجاد فایل XML برای import در Task Scheduler"""
    bat_path = os.path.join(install_dir, 'start_silent.bat').replace('\\', '\\\\')
    xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>مدیریت امور - بازرگانی محسنی</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{bat_path}</Command>
    </Exec>
  </Actions>
</Task>'''
    xml_path = os.path.join(install_dir, 'task_scheduler.xml')
    with open(xml_path, 'w', encoding='utf-16') as f:
        f.write(xml_content)
    print_success(f"فایل Task Scheduler XML ایجاد شد: {xml_path}")


def install_requirements(install_dir):
    """نصب وابستگی‌ها"""
    print_info("در حال نصب وابستگی‌ها...")
    req_path = os.path.join(install_dir, 'flask_app', 'requirements.txt')
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', req_path, '-q'],
                      capture_output=True, timeout=120)
        print_success("وابستگی‌ها نصب شدند")
    except Exception as e:
        print_error(f"خطا در نصب وابستگی‌ها: {e}")
        print_info("دستور زیر را دستی اجرا کنید:")
        print_info(f"  pip install -r {req_path}")


def print_mikrotik_guide(port):
    """نمایش راهنمای تنظیم MikroTik"""
    print_header("راهنمای تنظیم MikroTik برای دسترسی از خارج شبکه")
    print(f"""
{Colors.CYAN}۱. پورت فوروارد در MikroTik:{Colors.ENDC}

   وارد WinBox شوید و دستورات زیر را اجرا کنید:

   /ip firewall nat add chain=dstnat protocol=tcp dst-port={port} \\
       action=dst-nat to-addresses=IP_کامپیوتر_سرور to-port={port}

   مثال اگر IP کامپیوتر 192.168.1.100 باشد:
   /ip firewall nat add chain=dstnat protocol=tcp dst-port={port} \\
       action=dst-nat to-addresses=192.168.1.100 to-port={port}

{Colors.CYAN}۲. فایروال (اختیاری ولی توصیه شده):{Colors.ENDC}

   /ip firewall filter add chain=input protocol=tcp dst-port={port} \\
       action=accept place-before=0

{Colors.CYAN}۳. تست دسترسی:{Colors.ENDC}

   از خارج شبکه مرورگر را باز کنید:
   http://IP_عمومی_مودم:{port}

   برای پیدا کردن IP عمومی مودم:
   - وارد مودم شوید (معمولاً 192.168.1.1)
   - بخش Status یا WAN IP را ببینید
   - یا از سایت whatismyip.com استفاده کنید

{Colors.CYAN}۴. نکته امنیتی:{Colors.ENDC}

   حتماً رمز ادمین را تغییر دهید!
   فقط پورت {port} را فوروارد کنید، پورت‌های دیگر را باز نگذارید.

{Colors.CYAN}۵. DynDNS (اگر IP متغیر دارید):{Colors.ENDC}

   اگر IP عمومی مودم شما متغیر است، از سرویس DynDNS استفاده کنید:
   - No-IP: https://www.noip.com (رایگان)
   - Dynu: https://www.dynu.com (رایگان)
   - در MikroTik: /ip dns set allow-remote-requests=yes
""")


def print_summary(install_dir, port):
    """نمایش خلاصه نصب"""
    print_header("نصب با موفقیت انجام شد!")
    print(f"""
{Colors.GREEN}مسیر نصب:{Colors.ENDC} {install_dir}

{Colors.GREEN}فایل‌های ایجاد شده:{Colors.ENDC}
  • run.bat              → اجرای دستی برنامه
  • start_silent.bat     → اجرای بی‌صدا (برای Task Scheduler)
  • add_to_startup.reg   → اجرای خودکار در Startup
  • task_scheduler.xml   → فایل XML برای import در Task Scheduler
  • flask_app/config.json → تنظیمات پورت و رمز

{Colors.GREEN}نحوه اجرا:{Colors.ENDC}
  ۱. دستی: روی run.bat دوبار کلیک کنید
  ۲. خودکار: فایل add_to_startup.reg را اجرا کنید
  ۳. Task Scheduler: فایل task_scheduler.xml را import کنید

{Colors.GREEN}آدرس دسترسی:{Colors.ENDC}
  • داخل شبکه: http://localhost:{port}
  • از خارج: http://IP_عمومی_مودم:{port}

{Colors.GREEN}لاگین پیش‌فرض:{Colors.ENDC}
  • نام کاربری: admin
  • رمز عبور: admin123 (تغییر دهید!)
""")


def main():
    print_header("نصب‌کننده مدیریت امور - بازرگانی محسنی")

    # دریافت اطلاعات از کاربر
    install_dir = get_install_dir()
    port = get_port()
    admin_password = get_admin_password()

    # تأیید
    print(f"\n{Colors.WARNING}تنظیمات:{Colors.ENDC}")
    print(f"  مسیر نصب: {install_dir}")
    print(f"  پورت: {port}")
    print(f"  رمز ادمین: {'***' if admin_password != 'admin123' else 'admin123'}")
    confirm = input(f"\n{Colors.WARNING}آیا مطمئن هستید؟ (y/n): {Colors.ENDC}").strip().lower()
    if confirm != 'y':
        print("نصب لغو شد.")
        return

    # شروع نصب
    print_header("در حال نصب...")

    # ۱. ایجاد پوشه نصب
    os.makedirs(install_dir, exist_ok=True)
    print_success(f"پوشه نصب ایجاد شد: {install_dir}")

    # ۲. کپی فایل‌ها
    copy_files(install_dir)

    # ۳. ایجاد فایل تنظیمات
    create_config(install_dir, port, admin_password)

    # ۴. ایجاد فایل‌های Bat
    create_batch_file(install_dir, port)
    create_task_scheduler_bat(install_dir, port)

    # ۵. ایجاد فایل رجیستری startup
    create_startup_registry(install_dir, port)

    # ۶. ایجاد فایل XML Task Scheduler
    create_task_scheduler_xml(install_dir, port)

    # ۷. نصب وابستگی‌ها
    install_requirements(install_dir)

    # ۸. نمایش خلاصه
    print_summary(install_dir, port)

    # ۹. راهنمای MikroTik
    show_mikrotik = input(f"\n{Colors.CYAN}آیا راهنمای MikroTik نمایش داده شود؟ (y/n): {Colors.ENDC}").strip().lower()
    if show_mikrotik == 'y':
        print_mikrotik_guide(port)


if __name__ == '__main__':
    main()
