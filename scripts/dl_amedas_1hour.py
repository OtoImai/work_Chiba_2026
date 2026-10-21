#!/usr/bin/env python3
"""
Download JMA AMeDAS/observation-station hourly data for a date range,
by scraping https://www.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php

Adapted from an existing csh+heredoc script; rewritten as a single Python
script (no repeated subprocess/heredoc regeneration) for robustness over an
18-station x ~20-day, day-by-day scraping loop.

Stations: all 18 Chiba prefecture (fuken_id=45) stations -- both S (main
observatory) and A (AMeDAS) type -- confirmed against obs_stations.csv (the
official JMA station list) and embedded directly below.
"""

import os
import time
import datetime
import csv
import urllib.request

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

## ======== stations & period ========
# All Chiba prefecture (fuken_id=45) stations, both S (main/官署) and
# A (AMeDAS) type, from obs_stations.csv (the official JMA station list).
# Embedded directly here so this script doesn't depend on that CSV being
# present on the machine that runs it.

prec_no = 45   # Chiba prefecture

stations = [
    {'block_no': 47682, 'name': '千葉',   'type': 'S', 'lat': 35.601667, 'lon': 140.103333},
    {'block_no': 47674, 'name': '勝浦',   'type': 'S', 'lat': 35.150000, 'lon': 140.311667},
    {'block_no': 47672, 'name': '館山',   'type': 'S', 'lat': 34.986667, 'lon': 139.865000},
    {'block_no': 47648, 'name': '銚子',   'type': 'S', 'lat': 35.738333, 'lon': 140.856667},
    {'block_no':   375, 'name': '香取',   'type': 'A', 'lat': 35.858333, 'lon': 140.501667},
    {'block_no':  1236, 'name': '船橋',   'type': 'A', 'lat': 35.711667, 'lon': 140.043333},
    {'block_no':  1004, 'name': '大多喜', 'type': 'A', 'lat': 35.251667, 'lon': 140.215000},
    {'block_no':  1003, 'name': '横芝光', 'type': 'A', 'lat': 35.656667, 'lon': 140.480000},
    {'block_no':   916, 'name': '佐倉',   'type': 'A', 'lat': 35.728333, 'lon': 140.211667},
    {'block_no':   384, 'name': '鴨川',   'type': 'A', 'lat': 35.111667, 'lon': 140.100000},
    {'block_no':  1238, 'name': '牛久',   'type': 'A', 'lat': 35.396667, 'lon': 140.148333},
    {'block_no':   383, 'name': '鋸南',   'type': 'A', 'lat': 35.121667, 'lon': 139.836667},
    {'block_no':   381, 'name': '茂原',   'type': 'A', 'lat': 35.416667, 'lon': 140.310000},
    {'block_no':   378, 'name': '成田',   'type': 'A', 'lat': 35.763333, 'lon': 140.385000},
    {'block_no':   377, 'name': '東庄',   'type': 'A', 'lat': 35.821667, 'lon': 140.685000},
    {'block_no':   376, 'name': '我孫子', 'type': 'A', 'lat': 35.863333, 'lon': 140.110000},
    {'block_no':   382, 'name': '木更津', 'type': 'A', 'lat': 35.361667, 'lon': 139.940000},
    {'block_no':  1241, 'name': '坂畑',   'type': 'A', 'lat': 35.235000, 'lon': 140.098333},
]

start_date = datetime.date(2026, 8, 1)
end_date   = datetime.date(2026, 8, 20)

request_interval_sec = 1.0   # politeness delay between requests

## ======== dirs ========

base_dir   = '/raid/users/imai/work_Chiba_2026'
output_dir = os.path.join(base_dir, 'data', 'amedas', 'chiba_1hour')
os.makedirs(output_dir, exist_ok=True)

fields = ["station_id", "station_name", "ymd", "h", "prec"]


def scrape_one_day(block_no, station_name, date):
    """Return a list of per-hour rows (list of lists) for one station/date.
    Always returns 24 rows (hours 1-24), using NaN for missing/unparseable
    values, so downstream accumulation can detect gaps explicitly.
    """
    block_str = str(block_no)

    if block_str.startswith('47'):
        # main observatory (S-type) station page
        url = ("https://www.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php?"
               f"prec_no={prec_no}&block_no={block_str}"
               f"&year={date.year}&month={date.month}&day={date.day}&view=")
        prec_idx = 3
    else:
        # AMeDAS-only (A-type) station page: different endpoint, block_no
        # zero-padded to 4 digits in the URL, and precipitation is in a
        # different table column (no pressure/humidity columns on this page).
        block_str_url = block_str.zfill(4)
        url = ("https://www.data.jma.go.jp/obd/stats/etrn/view/hourly_a1.php?"
               f"prec_no={prec_no}&block_no={block_str_url}"
               f"&year={date.year}&month={date.month}&day={date.day}&view=")
        prec_idx = 1

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

    try:
        html = urllib.request.urlopen(req, timeout=30).read()
    except Exception as e:
        print(f"    [WARN] request failed for {station_name} {date}: {e}")
        return [[block_no, station_name, date, h, np.nan] for h in range(1, 25)]

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find("table", {"class": "data2_s"})
    if table is None:
        print(f"    [WARN] no data table found for {station_name} {date}")
        return [[block_no, station_name, date, h, np.nan] for h in range(1, 25)]

    prec_values = []
    for tr in table.find_all('tr')[2:]:
        tds = tr.find_all('td')
        if not tds:
            continue

        val_str = tds[prec_idx].text.strip()
        # JMA marks uncertain/missing values with these characters
        val_str = (val_str.replace(')', '').replace(']', '')
                          .replace('×', '').replace('--', ''))

        if val_str == '' or val_str == '0.0':
            prec = 0.0
        else:
            try:
                prec = float(val_str)
            except ValueError:
                prec = np.nan

        prec_values.append(prec)

    if len(prec_values) < 24:
        prec_values += [np.nan] * (24 - len(prec_values))
    prec_values = prec_values[:24]

    return [[block_no, station_name, date, h + 1, prec_values[h]] for h in range(24)]


## ======== main loop: one output file per station, saved as each finishes ========

n_days     = (end_date - start_date).days + 1
n_stations = len(stations)
saved_files = []

for s_idx, st in enumerate(stations, start=1):
    print(f"=== station [{s_idx}/{n_stations}] {st['name']} "
          f"(block_no={st['block_no']}, {st['type']}) ===", flush=True)

    station_rows = []
    date = start_date
    day_idx = 0
    while date <= end_date:
        day_idx += 1
        print(f"  [{day_idx}/{n_days}] fetching {date} ...", flush=True)

        station_rows.extend(scrape_one_day(st['block_no'], st['name'], date))

        date += datetime.timedelta(days=1)
        time.sleep(request_interval_sec)

    ## ---- save this station's full-period data now, before moving on ----
    df = pd.DataFrame(station_rows, columns=fields)

    if len(df) > 0:
        df["ymd"] = pd.to_datetime(df["ymd"])
        df["y"] = df["ymd"].dt.year
        df["m"] = df["ymd"].dt.month
        df["d"] = df["ymd"].dt.day
        df = df.reindex(columns=['station_id', 'station_name', 'y', 'm', 'd', 'h', 'prec'])
    else:
        df = pd.DataFrame(columns=['station_id', 'station_name', 'y', 'm', 'd', 'h', 'prec'])
        print(f"  [WARN] no rows collected for {st['name']} -- saving an empty file.")

    station_file = os.path.join(
        output_dir,
        f"{st['block_no']:05d}_{st['name']}_prec_1hour_"
        f"{start_date.isoformat()}_{end_date.isoformat()}.csv"
    )
    df.to_csv(station_file, index=False)
    saved_files.append(station_file)
    print(f"  saved: {station_file} ({len(df)} rows)")

print(f"Done. {len(saved_files)}/{n_stations} station files saved.")
