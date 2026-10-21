import matplotlib as mpl
mpl.use('Agg')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os

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

oclass_file    = os.path.join(ofig_dir, 'classified_parcels.csv')   # from 16_classify_and_plot.py
ocoverage_file = os.path.join(ofig_dir, 'moisture_source_coverage_v2.csv')
ofile_hist     = os.path.join(ofig_dir, 'coverage_histogram.png')

## ======== parameters (must match the main moisture-source script) ========

dq_uptake_threshold = 0.0   # [g/kg], Sodemann et al. (2008) Delta q^0_c
dq_loss_threshold   = 0.0   # [g/kg], no threshold on the precipitation side

PBL_COL      = 'PBL'
P0           = 1014.0
SCALE_HEIGHT = 8000.0
BLH_FACTOR   = 1.5


def pressure_to_height(p, p0=P0, scale_height=SCALE_HEIGHT):
    return scale_height * np.log(p0 / p)


def calculate_moisture_source_fractions(df, dq_uptake_threshold, dq_loss_threshold,
                                        pbl_col=PBL_COL):
    """
    Same ledger logic as calculate_moisture_sources(), but returns only the
    three mass-balance fractions (Sodemann et al., 2008, section 2.2 / Fig.5):
        f_tot : fraction of arrival Q attributed to in-BL (surface) sources
        e_tot : fraction attributed to above-BL uptakes (unidentified source)
        d_tot : remaining, fully unattributed fraction (= 1 - f_tot - e_tot)
    """
    df_forward = df.sort_values('time', ascending=True).reset_index(drop=True)

    if pbl_col not in df_forward.columns:
        raise KeyError(f"Column '{pbl_col}' not found.")

    ledger = {}
    arrival_Q = df_forward.iloc[-1]['Q']

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

        if dq > dq_uptake_threshold:
            if is_surface:
                ledger[t] = dq
            else:
                ledger[f"above_bl_{t}"] = dq

        elif dq < -dq_loss_threshold and q_prior > 0:
            keys_to_delete = []
            for src_time in ledger.keys():
                f_m = ledger[src_time] / q_prior
                ledger[src_time] += (dq * f_m)
                if ledger[src_time] <= 0:
                    keys_to_delete.append(src_time)
            for k in keys_to_delete:
                del ledger[k]

    tracked_surface  = sum(v for k, v in ledger.items() if not str(k).startswith('above_bl'))
    tracked_above_bl = sum(v for k, v in ledger.items() if str(k).startswith('above_bl'))

    if arrival_Q > 0:
        f_tot = tracked_surface  / arrival_Q
        e_tot = tracked_above_bl / arrival_Q
        d_tot = max(0.0, 1.0 - f_tot - e_tot)
    else:
        f_tot = e_tot = d_tot = np.nan

    return f_tot, e_tot, d_tot


## ======== select precipitating parcels only, via the classification CSV ========

class_df = pd.read_csv(oclass_file)
precip_files = class_df.loc[class_df['class'] == 'precipitating', 'file'].tolist()
print(f"{len(precip_files)} precipitating parcels to process "
      f"(out of {len(class_df)} total).")

records      = []
n_missing_col = 0
n_read_error  = 0

for idx, fname in enumerate(precip_files):
    if idx % 500 == 0:
        print(f"{idx}/{len(precip_files)} processed", flush=True)

    fpath = os.path.join(itra_dir, fname)
    try:
        df = pd.read_csv(fpath)
    except Exception:
        n_read_error += 1
        continue
    df = df.sort_values('time')

    try:
        f_tot, e_tot, d_tot = calculate_moisture_source_fractions(
            df, dq_uptake_threshold, dq_loss_threshold)
    except KeyError:
        n_missing_col += 1
        continue

    records.append({'file': fname, 'f_tot': f_tot, 'e_tot': e_tot, 'd_tot': d_tot})

print(f"Done. {len(records)} processed successfully, "
      f"{n_missing_col} skipped (missing '{PBL_COL}' column), "
      f"{n_read_error} skipped (read error).")

cov_df = pd.DataFrame(records)
cov_df.to_csv(ocoverage_file, index=False)
print(f"Per-trajectory coverage saved: {ocoverage_file}")

## ======== summary stats ========

for col in ['f_tot', 'e_tot', 'd_tot']:
    print(f"{col}: mean={cov_df[col].mean()*100:.1f}%, "
          f"median={cov_df[col].median()*100:.1f}%")

## ======== plot: Sodemann et al. (2008) Fig.5-style validation histogram ========

bins  = np.linspace(0, 1, 21)
width = np.diff(bins)
mids  = bins[:-1] + width / 2
n     = len(cov_df)

fig, ax = plt.subplots(figsize=(16 / 2.54, 9 / 2.54))

counts_f, _ = np.histogram(cov_df['f_tot'].dropna(), bins=bins)
ax.bar(bins[:-1], 100 * counts_f / n, width=width, align='edge',
       color='gray', alpha=0.5, label='f_tot (attributed, in-BL)')

counts_e, _ = np.histogram(cov_df['e_tot'].dropna(), bins=bins)
ax.plot(mids, 100 * counts_e / n, color='black', linestyle='-',
        label='e_tot (attributed, above-BL)')

counts_d, _ = np.histogram(cov_df['d_tot'].dropna(), bins=bins)
ax.plot(mids, 100 * counts_d / n, color='black', linestyle=':',
        label='d_tot (unknown source)')

ax.set_xlabel('Fraction')
ax.set_ylabel('Frequency (%)')
ax.set_title('Method validation histogram\n(cf. Sodemann et al. 2008, Fig. 5)')
ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig(ofile_hist, dpi=150)
print(f'figure saved: \n {ofile_hist}')
