import matplotlib as mpl
mpl.use('Agg')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import glob
import os
import sys
import argparse
from synoptic import *

## ======== command-line args ========

parser = argparse.ArgumentParser(
    description='Evaporative moisture-source contribution maps, split into '
                '1-day bins of source time (days before arrival).'
)
parser.add_argument('exp_name')
parser.add_argument('--bin-hours', type=float, default=24.0,
                    help='width of one time bin in hours (default 24)')
parser.add_argument('--vmax', type=float, default=0.8,
                    help='upper end of the colorbar in %% of the total (default 0.8)')
parser.add_argument('--mask-below', type=float, default=0.02,
                    help='cells below this %% are left blank (default 0.02)')
args = parser.parse_args()

## ======== dirs & files ========
exp_name = args.exp_name

base_dir = '/raid/users/imai/work_Chiba_2026'
work_dir = os.path.join(base_dir, 'Work', exp_name)
itra_dir = os.path.join(work_dir, '04_post', 'splited')

ofig_dir = os.path.join(base_dir, 'figure', exp_name)
os.makedirs(ofig_dir, exist_ok=True)

ifiles     = glob.glob(os.path.join(itra_dir, '*.csv'))
ofile_fmt  = os.path.join(ofig_dir, 'rain_contribution_day{day:02d}.png')
ofile_bar  = os.path.join(ofig_dir, 'rain_contribution_daily_total.png')
ofile_csv  = os.path.join(ofig_dir, 'rain_contribution_daily_total.csv')

## ======== parameters for extracting precipitating parcels ========

time_diff         = -1.0
rh_threshold      = 80.0
p_lower_threshold = 850.0
p_upper_threshold = 500.0

## ======== parameters for moisture source tracking ========

dq_threshold = 0.0

PBL_COL      = 'PBL'    # boundary-layer height [m]
P0           = 1014.0   # reference (sea-level) pressure [hPa]
SCALE_HEIGHT = 8000.0   # [m]
BLH_FACTOR   = 1.5


def pressure_to_height(p, p0=P0, scale_height=SCALE_HEIGHT):
    """Approximate geometric height [m] from pressure [hPa] (Eq. 4)."""
    return scale_height * np.log(p0 / p)

## ======== processing: precipitating parcel screening ========

def is_precipitating_parcel(df, time_diff, rh_threshold,
                            p_lower_threshold, p_upper_threshold):
    t0_data     = df[df['time'] == 0.0]
    t_prev_data = df[df['time'] == time_diff]

    if t0_data.empty or t_prev_data.empty:
        return False

    RH_t0 = t0_data['RH'].values[0]
    P_t0  = t0_data['p'].values[0]

    cond_rh             = (RH_t0 >= rh_threshold)
    cond_arrival_height = (P_t0 >= p_upper_threshold)

    return cond_rh and cond_arrival_height

## ======== processing: moisture source tracking ========

def calculate_moisture_sources(df, dq_threshold, pbl_col=PBL_COL):
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

        h_prior    = pressure_to_height(prev_row['p'])
        pbl_prior  = prev_row[pbl_col]
        is_surface = (BLH_FACTOR * pbl_prior >= h_prior)

        if dq > dq_threshold:
            if is_surface:
                ledger[t] = dq
            else:
                ledger[f"above_bl_{t}"] = dq

        elif dq < -dq_threshold and q_prior > 0:
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
            'raw_time': raw_time,            # [h] relative to arrival (<= 0)
            'source_lon': src_lon,
            'source_lat': src_lat,
            'contribution_q': mass_q,
            'is_surface_source': is_surface_src,
            'arrival_lon': arrival['lon'],
            'arrival_lat': arrival['lat'],
        })

    return results, coverage


def time_to_bin(raw_time_h, bin_hours):
    """0 = [0, bin_hours) h before arrival, 1 = next bin, ..."""
    return max(int(np.ceil(-raw_time_h / bin_hours)) - 1, 0)


## ======== draw setting ========
lon0, lon1 = 129, 210
lat0, lat1 = 9, 45
CL = 180.0

ax_loc = (0.05, 0.1, 0.8, 0.8)
cmap   = plt.cm.YlGnBu
levels = np.linspace(0, args.vmax, 17)
norm   = mpl.colors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)

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

    lons, lats, weights, bins_ = [], [], [], []
    extracted_count = 0

    for f in ifiles:
        df = pd.read_csv(f).sort_values('time')

        if is_precipitating_parcel(df, time_diff, rh_threshold,
                                   p_lower_threshold, p_upper_threshold):
            sources, coverage = calculate_moisture_sources(df, dq_threshold=dq_threshold)

            for src in sources:
                if src['is_surface_source'] and not pd.isna(src['source_lon']):
                    lons.append(src['source_lon'])
                    lats.append(src['source_lat'])
                    weights.append(src['contribution_q'])
                    bins_.append(time_to_bin(src['raw_time'], args.bin_hours))

            extracted_count += 1

    if extracted_count == 0 or len(weights) == 0:
        sys.exit('no precipitating parcels / no surface sources found')

    lons    = np.asarray(lons, dtype=float)
    lats    = np.asarray(lats, dtype=float)
    weights = np.asarray(weights, dtype=float)
    bins_   = np.asarray(bins_, dtype=int)

    n_bins = bins_.max() + 1
    total_all = weights.sum()

    # --- per-bin totals (share of the grand total, so that all bins sum to 100 %) ---
    bin_totals = np.array([weights[bins_ == b].sum() for b in range(n_bins)])
    bin_pct    = bin_totals / total_all * 100.0
    bin_label  = [f"{int(b * args.bin_hours)}-{int((b + 1) * args.bin_hours)} h before"
                  for b in range(n_bins)]

    pd.DataFrame({'bin': range(n_bins), 'label': bin_label,
                  'sum_contribution_q': bin_totals,
                  'share_pct': bin_pct}).to_csv(ofile_csv, index=False)
    print(pd.DataFrame({'label': bin_label, 'share_pct': bin_pct.round(1)}).to_string(index=False))

    # --- one figure per bin (day) ---
    for b in range(n_bins):
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

        m = bins_ == b
        density, xedges, yedges = np.histogram2d(lons[m], lats[m],
                                                 bins=[lon_bins, lat_bins], weights=weights[m])
        density_percent = density.T / total_all * 100.0
        density_masked = np.ma.masked_where(density_percent < args.mask_below, density_percent)

        mesh = ax.pcolormesh(xedges, yedges, density_masked,
                             transform=proj_cart, cmap=cmap, norm=norm, shading='flat')
        cbar = fig.colorbar(mesh, cax=cax, orientation="vertical", pad=0.02, extend='max')
        cbar.set_label('Evaporative Source Contribution (% of total)')
        ax.set_title(f"{exp_name}: {bin_label[b]}  [{bin_pct[b]:.1f}% of total]", fontsize=9)

        ofile = ofile_fmt.format(day=b + 1)
        fig.savefig(ofile, dpi=150)
        plt.close(fig)
        print(f'figure saved: {ofile}')

    # --- daily share bar chart ---
    fig2, ax2 = plt.subplots(figsize=(5, 3))
    ax2.bar(np.arange(n_bins) + 1, bin_pct, color='steelblue')
    ax2.set_xlabel(f'days before arrival (bin = {args.bin_hours:g} h)')
    ax2.set_ylabel('share of total (%)')
    ax2.grid(axis='y', alpha=0.3)
    fig2.tight_layout()
    fig2.savefig(ofile_bar, dpi=150)
    print(f'figure saved: \n {ofile_bar}')
