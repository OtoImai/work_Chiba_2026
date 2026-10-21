import matplotlib as mpl
mpl.use('Agg')
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cf
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm, LinearSegmentedColormap, Normalize
import glob
import os
import sys
from synoptic import *

## ======== dirs & files ========
exp_name = '20260814_box_7day_1300'

base_dir = '/raid/users/imai/work_Chiba_2026'
work_dir = os.path.join(base_dir, 'Work', exp_name)
init_dir = os.path.join(work_dir, '02_init_data')

ofig_dir = os.path.join(base_dir, 'figure')

os.makedirs(ofig_dir, exist_ok=True)

ifile      = os.path.join(init_dir, 'startf.2')
ofile_hor  = os.path.join(ofig_dir, 'box_init_hor.png')
ofile_ver  = os.path.join(ofig_dir, 'box_init_ver.png')

## ======== data loading & processing ========
df = pd.read_csv(ifile, sep=r"\s+", skiprows=2)
df = df[df["time"] != "---------------------------------------"]

df_hor = df[df['p'] == 840]
df_ver = df[df['lon'] == 140]

## ======== draw setting ========
lon0, lon1 = 139.2, 141.3
lat0, lat1 =  34.5,  36.3

ax_loc = (0.1,0.1,0.8,0.8)

## ======== draw horisontal distribution ========
lon, lat_hor = df_hor['lon'], df_hor['lat']

fig = plt.figure(figsize=(15/2.54, 15/2.54), dpi=300)
ax, proj, proj_cart = draw_synoptic_chart((lon0, lon1), (lat0, lat1), ax_loc,
                        xticks=np.arange(138, lon1+1, 0.5), yticks=np.arange(34.5, lat1+1, 0.5))
sc_hor = ax.scatter(lon, lat_hor, color='red', s=20.0, alpha=0.8, 
                edgecolors='gray', transform=proj_cart)
plt.savefig(ofile_hor, bbox_inches='tight', pad_inches=0.1)
plt.close()

print(f'figure saved : {ofile_hor}')

## ======== draw vertical distribution ========
lat_ver, p = df_ver['lat'], df_ver['p']

fig = plt.figure(figsize=(15/2.54, 15/2.54), dpi=300)
ax = plt.axes(ax_loc)
sc_ver = ax.scatter(lat_ver, p, color='red', s=8.0, alpha=0.8, edgecolor='gray')

ax.set_xticks(np.arange(35.0, 36.25, 0.25))
ax.invert_yaxis()

plt.savefig(ofile_ver, bbox_inches='tight', pad_inches=0.1)
plt.close()

print(f'figure saved : {ofile_ver}')
