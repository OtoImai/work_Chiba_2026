import matplotlib
matplotlib.use('Agg')
from datetime import datetime
import matplotlib.dates as mdates
from common_imports import *

########
datadir = '../../data/amedas/chiba_1hour'
figdir  = '../../figure/amedas'
os.makedirs(figdir, exist_ok=True)

ifile = os.path.join(datadir, '47682_千葉_prec_1hour_2026-08-01_2026-08-20.csv')
ofile = os.path.join(figdir, 'chiba_202608.png')
df = pd.read_csv(ifile)

df['date'] = pd.to_datetime(dict(year=df['y'], month=df['m'], day=df['d'])) \
                + pd.to_timedelta(df['h'], unit='h')
df['prec'] = df['prec'].fillna(0)

start = pd.Timestamp('2026-08-13 00:00')
end = pd.Timestamp('2026-08-15 00:00')
df = df[(df['date'] >= start) & (df['date'] <= end)].copy()

df['cum_prec'] = df['prec'].cumsum()

fig, ax1 = plt.subplots(figsize=(20/2.54, 12/2.54))

ax1.bar(df['date'], df['prec'], width=0.038, color='steelblue', edgecolor='dimgray', linewidth=0.7)

ax1.set_ylabel('Hourly precipitation [mm h$^{-1}$]')
ax1.set_ylim(0,120)

ax2 = ax1.twinx()
ax2.set_ylim(0,400)
ax2.plot(df['date'], df['cum_prec'], linewidth=3, color='firebrick')

ax1.xaxis.set_major_locator(mdates.DayLocator())
ax1.xaxis.set_major_formatter(
    mdates.DateFormatter('%m/%d')
)

ax1.xaxis.set_minor_locator(
    mdates.HourLocator(byhour=[0,6,12,18])
)
ax1.xaxis.set_minor_formatter(
    mdates.DateFormatter('%H')
)

ax1.xaxis.set_major_formatter(
    mdates.DateFormatter('%m/%d\n%H')
)

ax1.tick_params(
    axis='x',
    which='minor',
    labelsize=9
)

plt.setp(
    ax1.get_xticklabels(),
    ha='center'
)
ax1.grid(
    True,
    linestyle=':',
    alpha=0.5
)


plt.tight_layout()

plt.savefig(ofile, bbox_inches='tight', dpi=200)
plt.close()

print(f'figure saved: \n {ofile}')
