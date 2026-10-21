#!/usr/bin/env python
"""
usage:
    python 21_plot_regions.py                  # output: regions_map.png
    python 21_plot_regions.py --out my.png --no-coast
"""
import matplotlib as mpl
mpl.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.patches import Rectangle
import argparse

from regions import REGIONS

parser = argparse.ArgumentParser()
parser.add_argument('--out', default='regions_map.png')
parser.add_argument('--extent', nargs=4, type=float, default=[129, 200, 9, 45],
                    metavar=('LON0', 'LON1', 'LAT0', 'LAT1'))
parser.add_argument('--no-coast', action='store_true', help='skip Natural Earth land/ocean (offline)')
args = parser.parse_args()

lon0, lon1, lat0, lat1 = args.extent
CL = 180.0                                  # dateline-centred projection so 129-200E is continuous
proj = ccrs.PlateCarree(central_longitude=CL)

fig = plt.figure(figsize=(18 / 2.54, 10 / 2.54))
ax = fig.add_axes((0.08, 0.1, 0.84, 0.8), projection=proj)
ax.set_extent([lon0 - CL, lon1 - CL, lat0, lat1], crs=proj)

if not args.no_coast:
    ax.add_feature(cfeature.LAND.with_scale('50m'), color="dimgray", zorder=1)
    ax.add_feature(cfeature.OCEAN.with_scale('50m'), color="lightgray", zorder=0)
else:
    ax.set_facecolor('lightgray')

# axes in the same (lon - 180) coordinates -> label back to real longitudes
xt = np.arange(130, 201, 10)
ax.set_xticks(xt - CL, crs=proj)
def lon_label(v):
    if v < 180:
        return f"{v:.0f}°E"
    if v == 180:
        return "180°"
    return f"{360 - v:.0f}°W"


ax.set_xticklabels([lon_label(v) for v in xt], fontsize=8)
yt = np.arange(10, 46, 5)
ax.set_yticks(yt, crs=proj)
ax.set_yticklabels([f"{v}°N" for v in yt], fontsize=8)
ax.grid(alpha=0.3, lw=0.5)

for k, (name, (x0, x1, y0, y1), color) in enumerate(REGIONS, start=1):
    ax.add_patch(Rectangle((x0 - CL, y0), x1 - x0, y1 - y0, transform=proj,
                           facecolor=color, alpha=0.28, edgecolor=color, lw=2, zorder=3))
    ax.add_patch(Rectangle((x0 - CL, y0), x1 - x0, y1 - y0, transform=proj,
                           facecolor='none', edgecolor=color, lw=2, zorder=4))
#    ax.text((x0 + x1) / 2 - CL, (y0 + y1) / 2, f"{k}\n{name}", transform=proj,
#            ha='center', va='center', fontsize=8, color='k', zorder=5,
#            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec=color, alpha=0.85))

## Chiba (arrival point) for reference
#ax.plot(140.1 - CL, 35.6, marker='*', color='gold', mec='k', ms=11, transform=proj, zorder=6)
#ax.text(140.1 - CL + 0.8, 36.3, 'Chiba', transform=proj, fontsize=8, zorder=6)

ax.set_title("Source regions (first matching box wins; overlaps go to the earlier one)", fontsize=9)
fig.savefig(args.out, dpi=150)
print(f"figure saved: {args.out}")
