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

ifiles = glob.glob(os.path.join(itra_dir, '*.csv'))
ofile  = os.path.join(ofig_dir, 'tra_all.png')

## ======== draw setting ========
lon0, lon1 = 80, 220
lat0, lat1 =  4, 65
CL = 180.0

def lon_label(v):
    v = v % 360
    if v < 180:
        return f"{v:.0f}°E"
    if v == 180:
        return "180°"
    return f"{360 - v:.0f}°W"

ax_loc = (0.05,0.1,0.8,0.8)
xticks=np.array([80,90,100,110,120,130,140,150,160,170,180,-170,-160,-150,-140,-130,-120])
fig = plt.figure(figsize=(24/2.54,12/2.54))
cax = fig.add_axes([0.85, 0.15, 0.02, 0.7])
ax, proj, proj_cart = draw_synoptic_chart((lon0,lon1),(lat0,lat1), ax_loc,
                                            xticks=xticks, 
                                            yticks=np.arange(5, 66, 10),
                                            xformatter=lon_label,
                                            yformatter=lambda v: f"{v:.0f}°N")


ax.add_feature(cfeature.LAND.with_scale('50m'), color="dimgray")
ax.add_feature(cfeature.OCEAN.with_scale('50m'), color="lightgray")

cmap = plt.cm.rainbow_r
levels = np.arange(200, 1001, 50)
norm = mpl.colors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)


## ======== data loading & processing ========
for f in ifiles: 
    df = pd.read_csv(f)
    df = df.sort_values('time')

    lon, lat = df['lon'].values, df['lat'].values
    p = df['p'].values

    points = np.array([lon, lat]).T
    segs = np.stack((points[:-1], points[1:]), axis=1)
    
    lc = LineCollection(segs, cmap=cmap, linewidth=0.8, transform=proj_cart)
    lc.set_array(p[:-1])

    ax.add_collection(lc)

    ax.scatter(lon[0], lat[0], c="black", s=2.0,
               zorder=5, transform=proj_cart)
    ax.scatter(lon[-1], lat[-1], c="black", s=2.0,
               zorder=5, transform=proj_cart)

sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
sm.set_array([])

cbar = fig.colorbar(sm, cax=cax, orientation="vertical", pad=0.02)
cbar.ax.invert_yaxis()

plt.savefig(ofile)
print(f'figure saved: \n {ofile}')
