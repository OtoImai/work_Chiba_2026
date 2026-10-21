import matplotlib as mpl
mpl.use('Agg')
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm, LinearSegmentedColormap, Normalize
import glob
import os
import sys
import argparse
from synoptic import *

## ======== command-line args ========

parser = argparse.ArgumentParser(
    description='Compute and plot the evaporative moisture-source contribution '
                'map for one LAGRANTO experiment directory.'
)
parser.add_argument('exp_name')
args = parser.parse_args()

## ======== dirs & files ========
exp_name = args.exp_name

base_dir = '/raid/users/imai/work_Chiba_2026'
work_dir = os.path.join(base_dir, 'Work', exp_name)
itra_dir = os.path.join(work_dir, '04_post', 'splited')

ofig_dir = os.path.join(base_dir, 'figure', exp_name)

os.makedirs(ofig_dir, exist_ok=True)

ifiles    = glob.glob(os.path.join(itra_dir, '*.csv'))
ofile     = os.path.join(ofig_dir, 'rain_contribution_thres.png')
ocov_file = os.path.join(ofig_dir, 'moisture_source_coverage.csv')  # per-trajectory mass-balance log

## ======== parameters for extracting precipitating parcels ========

time_diff         = -1.0
rh_threshold      = 80.0
p_lower_threshold = 850.0
p_upper_threshold = 500.0

## ======== parameters for moisture source tracking ========

# Confirmed intentional: no dq filtering (every fluctuation is tracked).
dq_threshold = 0.0

# --- PBL judgement -----------------------------------------------------
# No traced geometric height needed: the parcel's height is approximated
# from its pressure via the barometric formula
#     h(p) = SCALE_HEIGHT * ln(P0 / p)          [m]
# and compared against BLH_FACTOR times the traced boundary-layer height:
#     is_surface  <=>  BLH_FACTOR * BLH >= h(p)
# i.e. 1.5*BLH >= 8000*ln(1014/p).
#
# LAGRANTO must still trace the boundary-layer height at each point ->
# PBL_COL. Rename it once you know the actual field name your reconfigured
# LAGRANTO run produces.
PBL_COL      = 'PBL'    # boundary-layer height [m]
P0           = 1014.0   # reference (sea-level) pressure [hPa]
SCALE_HEIGHT = 8000.0   # [m]
BLH_FACTOR   = 1.5


def pressure_to_height(p, p0=P0, scale_height=SCALE_HEIGHT):
    """Approximate geometric height [m] from pressure [hPa] (Eq. 4)."""
    return scale_height * np.log(p0 / p)
# ------------------------------------------------------------------------

## ======== processing: precipitating parcel screening ========

def is_precipitating_parcel(df, time_diff, rh_threshold,
                            p_lower_threshold, p_upper_threshold):
    """
    Screens whether a trajectory qualifies as a "precipitating parcel"
    based on conditions at the arrival time (t=0).

    NOTE: this pressure-based screening (max pressure reached, arrival
    height) is unrelated to the PBL-based surface-source judgement below
    and has been left unchanged.
    """
    t0_data     = df[df['time'] == 0.0]
    t_prev_data = df[df['time'] == time_diff]

    if t0_data.empty or t_prev_data.empty:
        return False

    RH_t0 = t0_data['RH'].values[0]
    P_t0  = t0_data['p'].values[0]

    cond_rh             = (RH_t0 >= rh_threshold)
    #cond_lower_tropo    = (df['p'].max() >= p_lower_threshold)
    cond_arrival_height = (P_t0 >= p_upper_threshold)

    return cond_rh and cond_arrival_height


## ======== processing: moisture source tracking ========

def calculate_moisture_sources(df, dq_threshold, pbl_col=PBL_COL):
    """
    Sodemann-type moisture-source ledger tracking along a single trajectory.

    Surface-uptake judgement compares a pressure-derived approximate height
    (Eq. 4: h(p) = SCALE_HEIGHT * ln(P0/p)) against BLH_FACTOR times the
    traced boundary-layer height:  is_surface <=> BLH_FACTOR*BLH >= h(p).

    Parameters:
        df (pd.DataFrame) : single trajectory, must include time, lon, lat,
                             Q, p, and the column named by pbl_col.
        dq_threshold (float)
        pbl_col (str)      : column name for boundary-layer height [m]

    Returns:
        results (list[dict]) : one entry per retained moisture source.
        coverage (float)     : tracked_total / arrival_Q (0-1), NaN if
                                arrival_Q <= 0. Use this to report how much
                                of the arrival moisture could be traced to
                                an identified source (mass-balance check).
    """
    df_forward = df.sort_values('time', ascending=True).reset_index(drop=True)

    if pbl_col not in df_forward.columns:
        raise KeyError(
            f"Column '{pbl_col}' not found in trajectory data. "
            f"Re-run LAGRANTO with boundary-layer height traced, or update "
            f"PBL_COL to match your actual output column name."
        )

    ledger = {}
    coord_lookup = dict(zip(df_forward['time'], zip(df_forward['lon'], df_forward['lat'])))
    arrival = df_forward.iloc[-1]
    arrival_Q = arrival['Q']

    results = []

    for i in range(1, len(df_forward)):
        row      = df_forward.iloc[i]
        prev_row = df_forward.iloc[i - 1]

        q_current = row['Q']
        q_prior   = prev_row['Q']
        dq = q_current - q_prior
        t  = row['time']

        # --- surface (boundary-layer) judgement: Eq. 4 ---
        # 1.5*BLH >= 8000*ln(1014/p)  <=>  BLH_FACTOR*BLH >= h(p)
        h_prior    = pressure_to_height(prev_row['p'])
        pbl_prior  = prev_row[pbl_col]
        is_surface = (BLH_FACTOR * pbl_prior >= h_prior)

        if dq > dq_threshold:
            # moisture uptake event
            if is_surface:
                ledger[t] = dq
            else:
                ledger[f"above_bl_{t}"] = dq

        elif dq < -dq_threshold and q_prior > 0:
            # moisture loss event (precipitation / removal).
            # Previously gated on `q_current > 0`, which could leave stale
            # ledger entries when Q dropped all the way to (or below) 0.
            # Gating on `q_prior > 0` avoids a ZeroDivisionError while still
            # fully draining the ledger when the parcel dries out completely.
            keys_to_delete = []

            for src_time in ledger.keys():
                f_m = ledger[src_time] / q_prior
                ledger[src_time] += (dq * f_m)

                if ledger[src_time] <= 0:
                    keys_to_delete.append(src_time)

            for k in keys_to_delete:
                del ledger[k]

    tracked_total = sum(ledger.values())
    coverage = (tracked_total / arrival_Q) if arrival_Q > 0 else np.nan

    for src_time, mass_q in ledger.items():
        is_surface_src = not str(src_time).startswith('above_bl')

        if is_surface_src:
            raw_time = src_time
        else:
            raw_time = float(str(src_time).replace('above_bl_', ''))

        src_lon, src_lat = coord_lookup.get(raw_time, (pd.NA, pd.NA))

        results.append({
            'source_time': src_time,
            'source_lon': src_lon,
            'source_lat': src_lat,
            'contribution_q': mass_q,
            'is_surface_source': is_surface_src,
            'arrival_lon': arrival['lon'],
            'arrival_lat': arrival['lat'],
        })

    return results, coverage


## ======== draw setting ========
lon0, lon1 = 129, 210
lat0, lat1 = 9, 45
CL = 180.0

ax_loc = (0.05, 0.1, 0.8, 0.8)

cmap = plt.cm.YlGnBu
levels = np.arange(0, 1.6, 0.1)
norm = mpl.colors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)

def lon_label(v):
    v = v % 360
    if v < 180:
        return f"{v:.0f}°E"
    if v == 180:
        return "180°"
    return f"{360 - v:.0f}°W"

## ======== main ========

if __name__ == "__main__":
    grid_size = 1.0
    lon_bins = np.arange(lon0, lon1 + grid_size, grid_size)
    lat_bins = np.arange(lat0, lat1 + grid_size, grid_size)

    all_source_lons    = []
    all_source_lats    = []
    all_source_weights = []
    extracted_count    = 0

    coverage_log = []  # per-trajectory mass-balance coverage records

    for f in ifiles:
        df = pd.read_csv(f)
        df = df.sort_values('time')

        if is_precipitating_parcel(df, time_diff, rh_threshold,
                                   p_lower_threshold, p_upper_threshold):

            sources, coverage = calculate_moisture_sources(df, dq_threshold=dq_threshold)

            for src in sources:
                if src['is_surface_source'] and not pd.isna(src['source_lon']):
                    all_source_lons.append(src['source_lon'])
                    all_source_lats.append(src['source_lat'])
                    all_source_weights.append(src['contribution_q'])

            coverage_log.append({
                'file': os.path.basename(f),
                'coverage_pct': coverage * 100 if not np.isnan(coverage) else np.nan,
            })

            extracted_count += 1

    # --- save & report mass-balance coverage statistics ---------------------
    if coverage_log:
        cov_df = pd.DataFrame(coverage_log)
        cov_df.to_csv(ocov_file, index=False)
        mean_cov   = cov_df['coverage_pct'].mean()
        median_cov = cov_df['coverage_pct'].median()
        print(f"Moisture-source coverage: mean={mean_cov:.1f}%, "
              f"median={median_cov:.1f}%  (per-trajectory log: {ocov_file})")
    # --------------------------------------------------------------------------

    fig = plt.figure(figsize=(24 / 2.54, 12 / 2.54))
    cax = fig.add_axes([0.85, 0.15, 0.02, 0.7])
    xticks=np.array([80,90,100,110,120,130,140,150,160,170,180,-170,-160,-150,-140,-130,-120]) 
    ax, proj, proj_cart = draw_synoptic_chart((lon0,lon1),(lat0,lat1), ax_loc,
                                            xticks=xticks,
                                            yticks=np.arange(5, 66, 10),
                                            xformatter=lon_label,
                                            yformatter=lambda v: f"{v:.0f}°N")

    ax.add_feature(cfeature.LAND.with_scale('50m'), color="dimgray")
    ax.add_feature(cfeature.OCEAN.with_scale('50m'), color="lightgray")

    if extracted_count > 0:
        density, xedges, yedges = np.histogram2d(all_source_lons, all_source_lats,
                                                 bins=[lon_bins, lat_bins], weights=all_source_weights)
        density = density.T

        total_moisture = np.sum(density)
        if total_moisture > 0:
            density_percent = (density / total_moisture) * 100.0
        else:
            density_percent = density

        density_masked = np.ma.masked_where(density_percent < 0.1, density_percent)

        if np.max(density_percent) > 0:
            mesh = ax.pcolormesh(xedges, yedges, density_masked,
                                 transform=proj_cart, cmap=cmap, norm=norm, shading='flat')

            cbar = fig.colorbar(mesh, cax=cax, orientation="vertical", pad=0.02)
            cbar.set_label('Evaporative Source Contribution (%)')

    plt.savefig(ofile)
    print(f'figure saved: \n {ofile}')
