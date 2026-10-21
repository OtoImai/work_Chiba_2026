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
from matplotlib.lines import Line2D
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

ifiles = glob.glob(os.path.join(itra_dir, '*.csv'))

ofile_map    = os.path.join(ofig_dir, 'classified_trajectories.png')
ofile_bar    = os.path.join(ofig_dir, 'classification_counts.png')
oclass_file  = os.path.join(ofig_dir, 'classified_parcels.csv')
## ======== parameters for extracting ========

time_diff         = -1.0
rh_threshold      = 80.0
di_rh_threshold   = 50.0
p_lower_threshold = 850.0
p_upper_threshold = 500.0

## ======== processing ========

def is_precipitating_parcel(df, time_diff, rh_threshold, p_upper_threshold):
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

def classify_parcel(df, rh_threshold, p_upper_threshold, di_rh_threshold):
    """
    'precipitating' : RH>=rh_threshold and arrival p>=p_upper_threshold
    'dry_intrusion' : arrival RH < dry_intrusion_rh_threshold
    'other'         : everything else
    """
    t0_data = df[df['time'] == 0.0]
    if t0_data.empty:
        return 'other', np.nan, np.nan, np.nan
 
    RH_t0 = t0_data['RH'].values[0]
    lon_t0 = t0_data['lon'].values[0]
    lat_t0 = t0_data['lat'].values[0]
 
    if is_precipitating_parcel(df, time_diff, rh_threshold, p_upper_threshold):
        return 'precipitating', lon_t0, lat_t0, RH_t0
 
    if RH_t0 < di_rh_threshold:
        return 'dry_intrusion', lon_t0, lat_t0, RH_t0
 
    return 'other', lon_t0, lat_t0, RH_t0

## ======== classify all trajectories, collect segments + summary records ========
 
lines_by_class = {'other': [], 'dry_intrusion': [], 'precipitating': []}
counts         = {'other': 0, 'dry_intrusion': 0, 'precipitating': 0}
records        = []
 
for idx, f in enumerate(ifiles):
    if idx % 2000 == 0:
        print(f"{idx}/{len(ifiles)} files processed", flush=True)
 
    try:
        df = pd.read_csv(f)
    except Exception:
        continue
    df = df.sort_values('time')
 
    cls, lon_t0, lat_t0, RH_t0 = classify_parcel(
        df, rh_threshold, p_upper_threshold, di_rh_threshold)
 
    counts[cls] += 1
    lines_by_class[cls].append(df[['lon', 'lat']].values)
 
    records.append({
        'file': os.path.basename(f),
        'arrival_lon': lon_t0,
        'arrival_lat': lat_t0,
        'arrival_rh': RH_t0,
        'class': cls,
    })
 
print("Classification counts:", counts)
 
pd.DataFrame(records).to_csv(oclass_file, index=False)
print(f"Per-parcel classification saved: {oclass_file}")
 
## ======== plot 1: trajectories colored by class ========
 
lon0, lon1 = 90, 210
lat0, lat1 = 4, 55
CL = 180.0 

ax_loc = (0.05, 0.1, 0.8, 0.8)
def lon_label(v):
    v = v % 360
    if v < 180:
        return f"{v:.0f}°E"
    if v == 180:
        return "180°"
    return f"{360 - v:.0f}°W"

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
 
style = {
    'other':         dict(color='lightgray',  alpha=0.15, linewidth=0.4, zorder=1),
    'dry_intrusion': dict(color='tab:orange', alpha=0.35, linewidth=0.5, zorder=2),
    'precipitating': dict(color='tab:blue',   alpha=0.45, linewidth=0.6, zorder=3),
}
 
# draw order: back to front, so 'precipitating' stays visible on top
for cls in ['other', 'dry_intrusion', 'precipitating']:
    segs = lines_by_class[cls]
    if not segs:
        continue
    lc = LineCollection(segs, transform=proj_cart, **style[cls])
    ax.add_collection(lc)
 
n_total = sum(counts.values())
legend_elements = [
    Line2D([0], [0], color=style[c]['color'], lw=2,
           label=f"{c} (n={counts[c]}, {100*counts[c]/n_total:.1f}%)")
    for c in ['precipitating', 'dry_intrusion', 'other']
]
ax.legend(handles=legend_elements, loc='lower left', fontsize=8, framealpha=0.9)

plt.savefig(ofile_map, dpi=150)
print(f'figure saved: \n {ofile_map}')
 
## ======== plot 2: bar chart of counts ========
 
fig2, ax2 = plt.subplots(figsize=(10 / 2.54, 8 / 2.54))
labels = ['precipitating', 'dry_intrusion', 'other']
values = [counts[l] for l in labels]
colors = [style[l]['color'] for l in labels]
 
bars = ax2.bar(labels, values, color=colors, edgecolor='black')
for b, v in zip(bars, values):
    ax2.text(b.get_x() + b.get_width() / 2, v, f"{v}\n({100*v/n_total:.1f}%)",
             ha='center', va='bottom', fontsize=9)
 
ax2.set_ylabel('number of trajectories')
ax2.set_title('Parcel classification counts')
plt.tight_layout()
plt.savefig(ofile_bar, dpi=150)
print(f'figure saved: \n {ofile_bar}')
