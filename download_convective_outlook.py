import requests
import csv
import zipfile
import io
import os
import time
import sys

url = 'https://spc.noaa.gov/products/outlook/archive/'
output_dir = 'convective_outlooks'
os.makedirs(output_dir, exist_ok=True)

# This is the same as the read_convective_outlook_api.py the only difference is that
# You can specify the year month date to start downloading from
# Or if you leave it blank then it auto detects your directory and see what you need to download for
# when you left it interrupted and it haven't finished downloading everything

# ─────────────────────────────────────────────────────────────────────────────
# Parse command-line arguments:
#
# - If you call “python3 read_convective_outlook.py 2025 4 7”, sys.argv == ['read_convective_outlook.py', '2025', '4', '7'].
#   We treat that as: start_year=2025, start_month=4, start_day=7.
# - If you call “python3 read_convective_outlook.py 2025”, sys.argv == ['read_convective_outlook.py', '2025'].
#   We treat that as: download only year 2025, starting from Jan 1 of that year.
# - If you call “python3 read_convective_outlook.py all” (or no args), sys.argv length is 1 or ['read_convective_outlook.py','all'].
#   We treat that as “download everything (2025 → 2001) starting from Jan 1, 2025.”
# ─────────────────────────────────────────────────────────────────────────────

start_year = None
start_month = None
start_day = None

if len(sys.argv) == 2 and sys.argv[1].lower() != 'all':
    # Only one numeric argument: that’s the year
    try:
        start_year = int(sys.argv[1])
        start_month = 1
        start_day = 1
    except ValueError:
        print(f"Invalid year: {sys.argv[1]}")
        sys.exit(1)

elif len(sys.argv) == 4:
    # Three arguments: year, month, day
    try:
        start_year  = int(sys.argv[1])
        start_month = int(sys.argv[2])
        start_day   = int(sys.argv[3])
    except ValueError:
        print(f"Invalid arguments: {sys.argv[1:]}")
        sys.exit(1)

else:
    # Either “all” or no args → download full range
    start_year  = None
    start_month = 1
    start_day   = 1

if start_year is None:
    years_to_download = range(2025, 2000, -1)
else:
    # If user gave a starting year, run from that year down to 2001
    years_to_download = range(start_year, 2000, -1)

for year_use in years_to_download:
    year_dir = os.path.join(output_dir, str(year_use))
    os.makedirs(year_dir, exist_ok=True)

    #Detect highest existing month-folder under convective_outlooks/<year_use>/
    existing_months = []
    for name in os.listdir(year_dir):
        if name.isdigit():
            existing_months.append(int(name))
    if existing_months:
        first_month_index = max(existing_months) - 1
        print(f"Resuming Year {year_use} at month {max(existing_months)} (zero‐based index {first_month_index})")
    else:
        first_month_index = 0
        print(f"No existing months for Year {year_use}; starting at month 1")


    for month_index in range(first_month_index, 12):
        month_use = month_index
        month_dir = os.path.join(year_dir, str(month_use + 1))
        os.makedirs(month_dir, exist_ok=True)

        for day_index in range(0, 31):
            date_script = (
                f"{year_use:04d}"
                f"{month_index+1:02d}"
                f"{day_index+1:02d}"
            )
            print(f"Processing → Year {year_use}, Month {month_index+1}, Day {day_index+1}")
