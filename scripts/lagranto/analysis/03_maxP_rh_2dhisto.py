import matplotlib as mpl
mpl.use('Agg')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

exp_name = '20260814_box_7day_1318'
base_dir = '/raid/users/imai/work_Chiba_2026'
ofig_dir = os.path.join(base_dir, 'figure', exp_name)

summary_file = os.path.join(ofig_dir, 'maxp_rh_summary.csv')
ofile        = os.path.join(ofig_dir, 'maxp_rh_2dhist.png')

# --- revised thresholds based on the 1D histograms ---
p_threshold  = 500.0   # was 700 (tentative); the real valley sits ~450-500 hPa
rh_threshold = 50.0    # confirmed by the valley at ~48-50%

df = pd.read_csv(summary_file)

fig, ax = plt.subplots(figsize=(10 / 2.54, 9 / 2.54))

h = ax.hist2d(df['max_p'], df['arrival_rh'], bins=[60, 60], cmap='viridis',
              norm=mpl.colors.LogNorm())  # log scale: makes a sparse corner cluster visible
fig.colorbar(h[3], ax=ax, label='count (log scale)')

ax.axvline(p_threshold, color='white', linestyle='--', linewidth=1)
ax.axhline(rh_threshold, color='white', linestyle='--', linewidth=1)

ax.set_xlabel('max pressure reached along trajectory [hPa]')
ax.set_ylabel('arrival (t=0) RH [%]')
ax.set_title('Joint distribution: is dry-intrusion a coherent corner cluster?')

plt.tight_layout()
plt.savefig(ofile, dpi=150)
print(f'figure saved: \n {ofile}')

# --- quick count check: how many trajectories fall in each proposed class ---
n_total          = len(df)
n_dry_intrusion  = ((df['max_p'] < p_threshold) & (df['arrival_rh'] < rh_threshold)).sum()
n_low_p_only     = ((df['max_p'] < p_threshold) & (df['arrival_rh'] >= rh_threshold)).sum()
n_low_rh_only    = ((df['max_p'] >= p_threshold) & (df['arrival_rh'] < rh_threshold)).sum()

print(f"Total: {n_total}")
print(f"Low max_p AND low RH (coherent dry-intrusion candidate): "
      f"{n_dry_intrusion} ({100*n_dry_intrusion/n_total:.1f}%)")
print(f"Low max_p but RH>=threshold (mismatch): "
      f"{n_low_p_only} ({100*n_low_p_only/n_total:.1f}%)")
print(f"Low RH but max_p>=threshold (mismatch): "
      f"{n_low_rh_only} ({100*n_low_rh_only/n_total:.1f}%)")
