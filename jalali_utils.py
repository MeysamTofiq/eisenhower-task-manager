# jalali_utils.py – تبدیل تاریخ شمسی
from datetime import date

MONTHS_FA = [
    "فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
    "مهر","آبان","آذر","دی","بهمن","اسفند"
]
DAYS_FA = ["شنبه","یکشنبه","دوشنبه","سه‌شنبه","چهارشنبه","پنج‌شنبه","جمعه"]


def j2g(jy, jm, jd):
    """Jalali → Gregorian"""
    jy -= 979; jm -= 1; jd -= 1
    jdn = 365*jy + (jy//33)*8 + (jy%33+3)//4
    for i in range(jm): jdn += [31,31,31,31,31,31,30,30,30,30,30,29][i]
    jdn += jd
    gdn = jdn + 79
    gy = 1600 + 400*(gdn//146097); gdn %= 146097
    lp = True
    if gdn >= 36525:
        gdn -= 1; gy += 100*(gdn//36524); gdn %= 36524
        lp = gdn >= 365; gdn += int(lp)
    gy += 4*(gdn//1461); gdn %= 1461
    if gdn >= 366: lp = False; gdn -= 1; gy += gdn//365; gdn %= 365
    dm = [31, 29 if lp else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = gd = 1
    for i, d in enumerate(dm):
        if gdn < d: gm = i+1; gd = gdn+1; break
        gdn -= d
    return gy, gm, gd


def g2j(gy, gm, gd):
    """Gregorian → Jalali"""
    gdn = 365*gy + (gy+3)//4 - (gy+99)//100 + (gy+399)//400
    for i in range(gm-1): gdn += [0,31,28,31,30,31,30,31,31,30,31,30,31][i+1]
    if gm > 2 and ((gy%4==0 and gy%100!=0) or gy%400==0): gdn += 1
    gdn += gd
    jdn = gdn - 79
    jnp = jdn // 12053; jdn %= 12053
    jy = 979 + 33*jnp + 4*(jdn//1461); jdn %= 1461
    if jdn >= 366: jy += (jdn-1)//365; jdn = (jdn-1)%365
    dm = [31,31,31,31,31,31,30,30,30,30,30,29]
    jm = 12; jd = jdn+1
    for i, d in enumerate(dm):
        if jdn < d: jm = i+1; jd = jdn+1; break
        jdn -= d
    return jy, jm, jd


def today_j():
    t = date.today()
    return g2j(t.year, t.month, t.day)


def parse_date(s):
    """'14040807' → (1404,8,7)"""
    if not s: return None
    d = ''.join(c for c in str(s) if c.isdigit())
    if len(d) == 8:
        try:
            y, m, dd = int(d[:4]), int(d[4:6]), int(d[6:8])
            if 1300 < y < 1500 and 1 <= m <= 12 and 1 <= dd <= 31:
                return (y, m, dd)
        except: pass
    return None


def fmt_j(y, m, d):
    return f"{y}/{m:02d}/{d:02d}"


def fmt_fa(y, m, d):
    mn = MONTHS_FA[m-1] if 1 <= m <= 12 else "?"
    return f"{d} {mn} {y}"


def days_left(deadline_str):
    """روزهای مانده تا موعد – منفی = عقب افتاده"""
    p = parse_date(deadline_str)
    if not p: return None
    try:
        gy, gm, gd = j2g(*p)
        return (date(gy, gm, gd) - date.today()).days
    except: return None


def dl_color(days):
    if days is None:  return "#5555aa"
    if days < 0:      return "#ff1744"
    if days == 0:     return "#ff4444"
    if days <= 3:     return "#ff6d00"
    if days <= 7:     return "#ffd600"
    return "#00e676"


def dl_label(days):
    if days is None:  return "بدون موعد"
    if days < 0:      return f"{abs(days)} روز عقب"
    if days == 0:     return "امروز!"
    if days == 1:     return "فردا"
    return f"{days} روز مانده"
