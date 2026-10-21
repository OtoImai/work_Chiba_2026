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
ofile  = os.path.join(ofig_dir, 'density_rain_parcels.png')

## ======== parameters for extracting ========

time_diff         = -1.0
rh_threshold      = 80.0
p_lower_threshold = 850.0
p_upper_threshold = 500.0

## ======== processing ========

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

## ======== draw setting ========
lon0, lon1 = 129, 210
lat0, lat1 = 9, 45
CL = 180.0

ax_loc = (0.05,0.1,0.8,0.8)

cmap = plt.cm.YlOrRd
levels = np.arange(0, 80, 2.5)
norm = mpl.colors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)

def lon_label(v):
    v = v % 360
    if v < 180:
        return f"{v:.0f}°E"
    if v == 180:
        return "180°"
    return f"{360 - v:.0f}°W"

## ======== draw ========
if __name__ == "__main__":
    grid_size = 1.0
    lon_bins = np.arange(lon0, lon1 + grid_size, grid_size)
    lat_bins = np.arange(lat0, lat1 + grid_size, grid_size)

    all_lons = []
    all_lats = []
    extracted_count = 0

    for f in ifiles:
        df = pd.read_csv(f)
        df = df.sort_values('time')
    
        if is_precipitating_parcel(df, time_diff, rh_threshold, 
                                   p_lower_threshold, p_upper_threshold):
            all_lons.extend(df['lon'].values)
            all_lats.extend(df['lat'].values)
            extracted_count += 1

    fig = plt.figure(figsize=(24/2.54,12/2.54))
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
        density, xedges, yedges = np.histogram2d(all_lons, all_lats, bins=[lon_bins, lat_bins])
        
        density = density.T
        
        density_masked = np.ma.masked_where(density == 0, density)
        density_pct = density_masked / extracted_count * 100

        cmap_density = plt.cm.YlOrRd 
        
        mesh = ax.pcolormesh(xedges, yedges, density_pct, transform=proj_cart, 
                             cmap=cmap, norm=norm, shading='flat')

        cbar = fig.colorbar(mesh, cax=cax, orientation="vertical", ticks=levels[::2], extend='max', pad=0.02)
        
        print(f"Extracted {extracted_count} parcels.")

    plt.savefig(ofile)
    print(f'figure saved: \n {ofile}')
