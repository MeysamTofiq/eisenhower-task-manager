import jdatetime

d = jdatetime.date.today()
print(f"today = {d}")
print(f"weekday() = {d.weekday()}")
print(f"isoweekday() = {d.isoweekday()}")

# weekday map test
days = {0:'شنبه', 1:'یکشنبه', 2:'دوشنبه', 3:'سه‌شنبه', 4:'چهارشنبه', 5:'پنجشنبه', 6:'جمعه'}
print(f"\nweekdays (0-6):")
for i in range(7):
    marker = " <-- TODAY" if d.weekday() == i else ""
    print(f"  {i} = {days[i]}{marker}")

# test shanbe calculation
target_wd = 5  # شنبه in my mapping
today_wd = d.weekday()
days_ahead = (target_wd - today_wd) % 7
if days_ahead == 0:
    days_ahead = 7
target = d + jdatetime.timedelta(days=days_ahead)
print(f"\n--- شنبه test ---")
print(f"today weekday = {today_wd}")
print(f"target_wd (شنبه) = {target_wd}")
print(f"days_ahead = {days_ahead}")
print(f"target date = {target}")

# try ALL mappings to see which one gives correct result
print(f"\n--- trying all possible شنبه values ---")
for val in range(7):
    da = (val - today_wd) % 7
    if da == 0: da = 7
    t = d + jdatetime.timedelta(days=da)
    print(f"  شنبه={val}: days_ahead={da}, result={t}")

# what should shanbe be?
# If today is Thursday(3), shanbe(5) -> (5-3)%7 = 2 days
# If today is Thursday(3), shanbe(0) -> (0-3)%7 = 4 days
# If today is Thursday(3), shanbe(4) -> (4-3)%7 = 1 day
# If today is Thursday(3), shanbe(6) -> (6-3)%7 = 3 days
