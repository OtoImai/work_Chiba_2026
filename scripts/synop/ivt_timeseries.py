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

FIGSDIR = os.path.join(BASEDIR, 'figure', 'synop')
os.makedirs(FIGSDIR, exist_ok=True)

f_u = os.path.join(SFCDIR, 'viwve_202608.nc')  # vertical integral of eastward water vapour flux
f_v = os.path.join(SFCDIR, 'viwvn_202608.nc')  # vertical integral of northward water vapour flux

ofile = os.path.join(FIGSDIR, 'ivt_timeseries.png')

## ======== dimension / variable names ========
# Adjust these if your netCDF uses different names (e.g. 'lat'/'lon' instead
# of ERA5 CDS-convention 'latitude'/'longitude').
LON_DIM = 'longitude'
LAT_DIM = 'latitude'
TIME_DIM = 'valid_time'
U_VAR = 'viwve'
V_VAR = 'viwvn'

## ======== target box (area-average) ========
lon0, lon1 = 139.8, 140.9
lat0, lat1 = 34.9, 35.9

## ======== wider domain for computing the spatial derivatives ========
# hdivg (and any centered-difference divergence) needs neighboring grid
# points on both sides. Restricting the domain to the 1x1 deg target box
# BEFORE computing the derivative starves it of neighbors and the result is
# undefined almost everywhere (this was the bug in the GrADS script).
# Load an extra 5-degree margin on each side and only average down to the
# target box at the very end.
PAD = 5.0
lon0_wide, lon1_wide = lon0 - PAD, lon1 + PAD
lat0_wide, lat1_wide = lat0 - PAD, lat1 + PAD

time0, time1 = '2026-08-10T00:00', '2026-08-15T00:00'

## ======== load ========

ds_u = xr.open_dataset(f_u)
ds_v = xr.open_dataset(f_v)

# ERA5 latitude is often stored descending (90 -> -90); handle either order.
def lat_slice(ds, lat_a, lat_b):
    if ds[LAT_DIM].values[0] > ds[LAT_DIM].values[-1]:
        return slice(max(lat_a, lat_b), min(lat_a, lat_b))
    else:
        return slice(min(lat_a, lat_b), max(lat_a, lat_b))

u = ds_u[U_VAR].sel({
    TIME_DIM: slice(time0, time1),
    LON_DIM: slice(lon0_wide, lon1_wide),
    LAT_DIM: lat_slice(ds_u, lat0_wide, lat1_wide),
})
v = ds_v[V_VAR].sel({
    TIME_DIM: slice(time0, time1),
    LON_DIM: slice(lon0_wide, lon1_wide),
    LAT_DIM: lat_slice(ds_v, lat0_wide, lat1_wide),
})

print(f"Loaded u: {u.shape}, v: {v.shape}, time range {u[TIME_DIM].values[0]} .. {u[TIME_DIM].values[-1]}")

## ======== compute IVT magnitude ========

mag = np.sqrt(u**2 + v**2)

## ======== compute horizontal divergence on the wide domain (spherical) ========
# div(F) = (1/(R cosphi)) * [ dFu/dlambda + d(Fv*cosphi)/dphi ]
# u.differentiate(coord) returns d/d(coord), with coord in its native units
# (degrees here); multiply by (180/pi) to convert to d/d(radians).

R = 6371000.0  # Earth radius [m]
deg2rad_factor = 180.0 / np.pi

lat_rad = np.deg2rad(u[LAT_DIM])
cos_lat = np.cos(lat_rad)

du_dlambda   = u.differentiate(LON_DIM) * deg2rad_factor
dvcos_dphi   = (v * cos_lat).differentiate(LAT_DIM) * deg2rad_factor

div = (du_dlambda + dvcos_dphi) / (R * cos_lat)

## ======== area-average over the small target box (cos-lat weighted) ========

def box_average(da, lon_a, lon_b, lat_a, lat_b):
    sub = da.sel({LON_DIM: slice(lon_a, lon_b),
                  LAT_DIM: lat_slice(da, lat_a, lat_b)})
    weights = np.cos(np.deg2rad(sub[LAT_DIM]))
    return sub.weighted(weights).mean(dim=[LAT_DIM, LON_DIM])


mag_avg = box_average(mag, lon0, lon1, lat0, lat1)
div_avg = box_average(div, lon0, lon1, lat0, lat1)

time_vals = pd.to_datetime(mag_avg[TIME_DIM].values)
mag_vals = mag_avg.values
div_vals = div_avg.values          # [kg m^-2 s^-1], positive = divergence

## ======== find the peak convergence time (most negative divergence), ========
## ======== excluding the period suspected to be typhoon-influenced      ========

div_series = pd.Series(div_vals, index=time_vals)

typhoon_period_start = '2026-08-10T18:00'
typhoon_period_end   = '2026-08-11T18:00'
mask_exclude_typhoon = ~((div_series.index >= typhoon_period_start) &
                          (div_series.index <= typhoon_period_end))

candidate = div_series[mask_exclude_typhoon]
peak_time  = candidate.idxmin()
peak_value = candidate.min()

print(f"Peak convergence (excluding {typhoon_period_start} - "
      f"{typhoon_period_end}, suspected typhoon period):")
print(f"  time = {peak_time}")
print(f"  div  = {peak_value:.3e} kg m^-2 s^-1")

## ======== plot ========

fig, ax1 = plt.subplots(figsize=(18 / 2.54, 8 / 2.54))

ax1.plot(time_vals, mag_vals, color='tab:blue', linewidth=2)
ax1.set_ylabel('IVT [kg m$^{-1}$ s$^{-1}$]', color='black')
ax1.tick_params(axis='y', labelcolor='black')
ax1.set_ylim(0, 1000)

ax2 = ax1.twinx()
ax2.plot(time_vals, div_vals, color='tab:red', linewidth=2)
ax2.set_ylabel('Divergence [kg m$^{-2}$ s$^{-1}$]', color='black')
ax2.tick_params(axis='y', labelcolor='black')

vmax = float(np.nanmax(np.abs(div_vals))) * 1.1
ax2.set_ylim(-vmax, vmax)
ax2.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
ax2.axhline(0, color='black', linewidth=1, linestyle='-', zorder=0)

ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d%b'))
ax1.xaxis.set_major_locator(mdates.DayLocator())

ax1.axvline(peak_time, color='black', linewidth=1, linestyle='--', zorder=0)

fig.tight_layout()
plt.savefig(ofile, dpi=150)
print(f'figure saved: \n {ofile}')
