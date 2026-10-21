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

## ======== dirs & files ========
exp_name = '20260814_box_7day_1300'

base_dir = '/raid/users/imai/work_Chiba_2026'
work_dir = os.path.join(base_dir, 'Work', exp_name)
itra_dir = os.path.join(work_dir, '04_post', 'splited')

ofig_dir = os.path.join(base_dir, 'figure', exp_name)

os.makedirs(ofig_dir, exist_ok=True)

ifiles = glob.glob(os.path.join(itra_dir, '*.csv'))
ofile  = os.path.join(ofig_dir, 'maxP_rh_histo.png')

print(f'found {len(ifiles)} trajectory files.')

## ======== data loading & processing ========
max_p_list      = []
arrival_rh_list = []
n_skipped       = 0

for idx, f in enumerate(ifiles):
    if idx % 1000 == 0:
        print(f"{idx}/{len(ifiles)} files processed", flush=True)

    try:
        df = pd.read_csv(f)
    except Exception as e:
        n_skipped += 1
        continue
    
    t0_data = df[df['time'] == 0.0]
    if t0_data.empty:
        n_skipped += 1
        continue

    max_p_list.append(df['p'].max())
    arrival_rh_list.append(t0_data['RH'].values[0])

print(f"Collected {len(max_p_list)} trajectories ({n_skipped} skipped: "
      f"read error or missing t=0 row).")

max_p_arr      = np.array(max_p_list)
arrival_rh_arr = np.array(arrival_rh_list)
## ======== save raw summary stats for later re-plotting / re-thresholding ========
summary_df = pd.DataFrame({
    'max_p': max_p_arr,
    'arrival_rh': arrival_rh_arr,
})
osummary_file = os.path.join(ofig_dir, 'maxp_rh_summary.csv')
summary_df.to_csv(osummary_file, index=False)
print(f"Per-trajectory summary saved: {osummary_file}")
 
## ======== plot ========
 
fig, axes = plt.subplots(2, 1, figsize=(15 / 2.54, 15 / 2.54))
 
# --- max pressure reached along trajectory ---
axes[0].hist(max_p_arr, bins=60, color='steelblue', edgecolor='dimgray', rwidth=0.85, linewidth=0.5)
axes[0].grid(axis='y')
axes[0].set_xlabel('max pressure reached along trajectory [hPa]')
axes[0].set_ylabel('number of trajectories')
axes[0].set_xlim(100, 1101)
axes[0].set_ylim(0,121)
axes[0].set_title('Max p')
#axes[0].axvline(700, color='gray', linestyle='--', linewidth=1,
#                label='700 hPa (tentative)')
#axes[0].legend(fontsize=8, loc='upper left')
 
# --- arrival RH ---
axes[1].hist(arrival_rh_arr, bins=60, color='indianred', edgecolor='dimgray', rwidth=0.85, linewidth=0.5)
axes[1].grid(axis='y')
axes[1].set_xlabel('arrival (t=0) RH [%]')
axes[1].set_ylabel('number of trajectories')
axes[1].set_xlim(10, 121)
axes[1].set_ylim(0,76)
axes[1].set_title('Arrival RH')
#axes[1].axvline(80, color='gray', linestyle='--', linewidth=1,
#                label='80% (precipitating threshold)')
#axes[1].axvline(50, color='black', linestyle=':', linewidth=1,
#                label='50% (tentative DI threshold)')
#axes[1].legend(fontsize=8, loc='upper left')
 
plt.tight_layout()
plt.savefig(ofile, dpi=150)
print(f'figure saved: \n {ofile}')
