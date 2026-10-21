import numpy as np
import pandas as pd
import xarray as xr
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

## ======== dirs & files (same convention as the bash/GrADS script) ========
BASEDIR = '/raid/users/imai/work_Chiba_2026'
DATADIR = os.path.join(BASEDIR, 'data')
SFCDIR  = os.path.join(DATADIR, 'single')
PRSDIR  = os.path.join(DATADIR, 'pressure')

FIGSDIR = os.path.join(BASEDIR, 'figure', 'synop')
os.makedirs(FIGSDIR, exist_ok=True)

f_w = os.path.join(PRSDIR, 'w_202608.nc')  # vertical integral of eastward water vapour flux

ofile = os.path.join(FIGSDIR, 'omega_timeseries_500.png')

## ======== dimension / variable names ========
LON_DIM  = 'longitude'
LAT_DIM  = 'latitude'
PRS_DIM  = 'pressure_level' 
TIME_DIM = 'valid_time'
W_VAR    = 'w'

## ======== target box (area-average) ========
lon0, lon1 = 139.8, 140.9
lat0, lat1 = 34.9, 35.9
lev = 500

time0, time1 = '2026-08-10T00:00', '2026-08-15T00:00'

## ======== load ========

ds_w = xr.open_dataset(f_w)

def lat_slice(ds, lat_a, lat_b):
    if ds[LAT_DIM].values[0] > ds[LAT_DIM].values[-1]:
        return slice(max(lat_a, lat_b), min(lat_a, lat_b))
    else:
        return slice(min(lat_a, lat_b), max(lat_a, lat_b))

w = ds_w[W_VAR].sel({
    TIME_DIM: slice(time0, time1),
    LON_DIM : slice(lon0, lon1),
    LAT_DIM : lat_slice(ds_w, lat0, lat1),
    PRS_DIM : lev
})

## ======== area-average over the small target box (cos-lat weighted) ========

def box_average(da, lon_a, lon_b, lat_a, lat_b):
    sub = da.sel({LON_DIM: slice(lon_a, lon_b),
                  LAT_DIM: lat_slice(da, lat_a, lat_b)})
    weights = np.cos(np.deg2rad(sub[LAT_DIM]))
    return sub.weighted(weights).mean(dim=[LAT_DIM, LON_DIM])

w_avg = box_average(w, lon0, lon1, lat0, lat1)
w_vals = w_avg.values
time_vals = pd.to_datetime(w_avg[TIME_DIM].values)

fig, ax = plt.subplots(figsize=(18/2.54, 8/2.54))
ax.plot(time_vals, w_vals, color='tab:blue', linewidth=2)
ax.tick_params(axis='y', labelcolor='black')
ax.set_ylim(-2.0, 2.0)

ax.axhline(0, color='black', linewidth=1, linestyle='-', zorder=0)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d%b'))
ax.xaxis.set_major_locator(mdates.DayLocator())

fig.tight_layout()
plt.savefig(ofile, dpi=150)
print(f'figure saved: \n {ofile}')
