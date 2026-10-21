import matplotlib as mpl
mpl.use('Agg')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import cartopy.crs as ccrs
import os
from synoptic import *

## ======== dirs & files ========
base_dir   = '/raid/users/imai/work_Chiba_2026'
input_dir  = os.path.join(base_dir, 'data', 'amedas', 'chiba_1hour')

ofig_dir = os.path.join(base_dir, 'figure', 'amedas')
os.makedirs(ofig_dir, exist_ok=True)

ofile_map    = os.path.join(ofig_dir, 'precip_1314aug_ranking_map.png')
ofile_ranking = os.path.join(ofig_dir, 'precip_1314aug_ranking.csv')

start_date_str = '2026-08-01'
end_date_str   = '2026-08-20'  # must match the date range used when downloading

## ======== accumulation period ========
target_days = [(2026, 8, 13), (2026, 8, 14)]

## ======== stations (same list/coords used to download the data) ========
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

## ======== read each station's CSV, sum precip over the target days ========

records = []

for st in stations:
    fpath = os.path.join(
        input_dir,
        f"{st['block_no']:05d}_{st['name']}_prec_1hour_"
        f"{start_date_str}_{end_date_str}.csv"
    )

    if not os.path.exists(fpath):
        print(f"[WARN] file not found for {st['name']}: {fpath}")
        records.append({**st, 'total_precip': np.nan, 'n_hours': 0})
        continue

    df = pd.read_csv(fpath)

    mask = df.apply(lambda row: (row['y'], row['m'], row['d']) in target_days, axis=1)
    sub = df[mask]

    total_precip = sub['prec'].sum()
    n_hours = len(sub)

    records.append({**st, 'total_precip': total_precip, 'n_hours': n_hours})

    expected_hours = len(target_days) * 24
    if n_hours != expected_hours:
        print(f"[WARN] {st['name']}: expected {expected_hours} hourly rows "
              f"in the target period, found {n_hours}")

result_df = pd.DataFrame(records)

## ======== ranking ========

ranking_df = result_df.sort_values('total_precip', ascending=False).reset_index(drop=True)
ranking_df.index = ranking_df.index + 1  # 1-indexed rank

print("\n=== Accumulated precipitation, 13-14 Aug 2026 (ranking) ===")
print(ranking_df[['name', 'block_no', 'type', 'total_precip', 'n_hours']].to_string())

ranking_df.to_csv(ofile_ranking)
print(f"\nranking saved: {ofile_ranking}")

## ======== draw settings (colormap matches the reference JAS-95ptile script) ========

lon0, lon1 = 139.2, 141.3
lat0, lat1 = 34.5, 36.3

ax_loc  = (0.1, 0.1, 0.8, 0.8)
cax_loc = [0.92, 0.15, 0.02, 0.7]

# Levels re-scaled for a 2-day event accumulation (mm), instead of the
# reference script's JJA daily-95th-percentile range (10-80 mm/day).
# Check the actual value range in `ranking_df` once run and adjust these
# breakpoints if most stations fall inside a single bin.
levels = [20, 40, 60, 100, 150, 200, 300, 400]

colors = np.array(
    [
        [255, 250, 252, 1],  # 20
        [255, 236, 220, 1],  # 40
        [245, 225, 160, 1],  # 60
        [190, 215, 140, 1],  # 100
        [120, 190, 120, 1],  # 150
        [  0, 150, 130, 1],  # 200  <- darker from here
        [  0, 100, 140, 1],  # 300
        [ 20,  40, 120, 1],  # 400
    ],
    dtype=np.float32
)

colors[:, :3] /= 255
cmap = ListedColormap(colors)
norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)

## ======== draw ========

fig = plt.figure(figsize=(10 / 2.54, 10 / 2.54), dpi=300)

ax, proj, proj_cart = draw_synoptic_chart((lon0, lon1), (lat0, lat1), ax_loc,
                    xticks=np.arange(138, 143, 0.5), yticks=np.arange(33.5, 36.5, 0.5))

valid = result_df.dropna(subset=['total_precip'])

sc = ax.scatter(valid['lon'], valid['lat'], c=valid['total_precip'], cmap=cmap, norm=norm,
                s=20, edgecolors='gray', linewidth=0.2, transform=proj_cart)

# Mark the sea-box used for the earlier IVT time series (140-141E, 35-36N),
# for visual cross-reference between the AMeDAS and IVT analyses.
draw_rectangle(ax, 139.8, 140.9, 34.9, 35.9, c='red', lw=0.8, ls='-')

cbar = fig.colorbar(sc, cax=plt.axes(cax_loc), ticks=levels, extend='max')
cbar.ax.tick_params(labelsize=8)

plt.savefig(ofile_map, bbox_inches='tight', pad_inches=0.1)
print(f'figure saved: \n {ofile_map}')
