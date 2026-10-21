#!/bin/bash
# =====================================================================================
# Linear decomposition of slhf using ERA5 single level data (e.g., Tanimoto etal.2003)
#  Q' = t1 + t2 + t3 + t4 (+ res)
#  t1: Wind speed term : coef * W' * (qs_c - qa_c)
#  t2: SST term        : coef * Wc * qs'
#  t3: Humidity term   : coef * Wc * (-qa')
#  t4: Nonlinear term  : coef * W' * (qs' - qa')
#  coef = QC / (Wc * (qs_c - qa_c))  (rho*L*C_E, calculated from climatology)
#
# usage: ./lh_decomp_parallel.sh [day] [maxjobs]     (default: day=12, maxjobs=6)
# =====================================================================================

#set -e -x

BASEDIR=/raid/users/imai/work_Chiba_2026
FIGSDIR="$BASEDIR"/figure/synop
DATADIR="$BASEDIR"/data
SFCDIR="$DATADIR"/single
CLMDIR="$DATADIR"/clim/single
WORKDIR="$BASEDIR"/tmp_gs          # 並列実行用の作業場所 (gs と log を変数ごとに分ける)
mkdir -p "$FIGSDIR" "$WORKDIR"

lon0=110; lon1=185; lat0=0; lat1=50
month=8
day=${1:-12}
MAXJOBS=${2:-6}
time0=00z${day}
time1=23z${day}

SALF=1.0

# -------------------------------------------------------------------------------------
# 1変数ぶんの GrADS 実行 + 画像変換
# -------------------------------------------------------------------------------------
plot_one() {
  local var=$1
  local ttl
  case $var in
    qp)  ttl="Q_anom";;
    t1)  ttl="wind";;
    t2)  ttl="SST";;
    t3)  ttl="humidity";;
    t4)  ttl="nonlinear";;
    res) ttl="residual";;
  esac

  local FIGURENAME=lh_decomp_${ttl}_${day}
  local GSFILE="$WORKDIR"/lh_decomp_${day}_${var}.gs     # 変数ごとに別ファイル (競合防止)
  local LOGFILE="$WORKDIR"/lh_decomp_${day}_${var}.log   # 出力が混ざらないようログも分ける

  echo "## Plotting ${ttl} (day=${day})"

  cat>"$GSFILE"<<eof
'reinit'

'set display color white'
'c'
'set grads off'
'set parea 1.0 5.0 1.0 5.0'
'set mpdset mres'
'set poli off'
'set annot 1 4'
'set map 1 1 5'
'set xlopts 1 4 0.14'
'set ylopts 1 4 0.14'
'set xlint 15'
'set ylint 10'

'sdfopen ${CLMDIR}/lh_monmean_1991_2020.nc'
'sdfopen ${CLMDIR}/wspd_aug_1991_2020_6h.nc'
'sdfopen ${CLMDIR}/sst_monmean_1991_2020.nc'
'sdfopen ${CLMDIR}/d2m_monmean_1991_2020.nc'
'sdfopen ${CLMDIR}/ps_monmean_1991_2020.nc'
'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'
'set t ${month}'

'set dfile 5'
'define pc=sp/100'
'set dfile 1'
'define qc=-1*slhf/86400'
'set dfile 2'
'define wc=wspd(t=1)'
'set dfile 3'
'define tsc=sst-273.15'
'define esc=6.112*exp(17.67*tsc/(tsc+243.5))'
'define qsc=${SALF}*0.622*esc/(pc-0.378*esc)'
'set dfile 4'
'define tdc=d2m-273.15'
'define eac=6.112*exp(17.67*tdc/(tdc+243.5))'
'define qac=0.622*eac/(pc-0.378*eac)'
'define dqc=qsc-qac'

'define coef=maskout(qc/(wc*dqc),abs(dqc)-0.001)'

'close 5'
'close 4'
'close 3'
'close 2'
'close 1'

'sdfopen ${SFCDIR}/lh_202608.nc'
'sdfopen ${SFCDIR}/u10m_202608.nc'
'sdfopen ${SFCDIR}/v10m_202608.nc'
'sdfopen ${SFCDIR}/sst_202608.nc'
'sdfopen ${SFCDIR}/d2m_202608.nc'
'sdfopen ${SFCDIR}/ps_202608.nc'

'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'
'set time ${time0} ${time1}'

'set dfile 1'
'define lh=slhf'
'set dfile 2'
'define u=u10'
'set dfile 3'
'define v=v10'
'set dfile 4'
'define sst=sst'
'set dfile 5'
'define d2m=d2m'
'set dfile 6'
'define ph=sp/100'


'define tsh=sst-273.15'
'define esh=6.112*exp(17.67*tsh/(tsh+243.5))'
'define qsh=${SALF}*0.622*esh/(ph-0.378*esh)'
'define tdh=d2m-273.15'
'define eah=6.112*exp(17.67*tdh/(tdh+243.5))'
'define qah=0.622*eah/(ph-0.378*eah)'

'set time ${time0}'

'define qs=ave(qsh,time=${time0},time=${time1})'
'define qa=ave(qah,time=${time0},time=${time1})'
'define q=ave(-1*lh/3600,time=${time0},time=${time1})'

'define uu=ave(u,time=${time0},time=${time1})'
'define vv=ave(v,time=${time0},time=${time1})'
'define w=ave(mag(u,v),time=${time0},time=${time1})'

* -------- decomposition --------
'define qp=q-qc'

* wind term
'define t1=coef*(w-wc)*dqc'
* SST term
'define t2=coef*wc*(qs-qsc)'
* Humidity term
'define t3=-1*coef*wc*(qa-qac)'
* Nonlinear term
'define t4=coef*(w-wc)*((qs-qsc)-(qa-qac))'
* residal term
'define res=qp-(t1+t2+t3+t4)'

'set gxout shade2'
'color -160 160 20 -kind navy->blue->skyblue->lightskyblue->white->gold->orange->red->palevioletred'
'd ${var}'

'xcbar 5.1 5.2 1.0 5.0 -line on -edge triangle -fs 2 -direction v'
'print -R ${FIGSDIR}/${FIGURENAME}.eps'
'quit'
eof

  grads -lbc "$GSFILE" > "$LOGFILE" 2>&1 || { echo "!! grads failed: ${var} (see $LOGFILE)"; return 1; }
  rm -f "$GSFILE"

  convert -density 900 -resize 800 -background white -flatten \
    ${FIGSDIR}/${FIGURENAME}.eps ${FIGSDIR}/${FIGURENAME}.png \
    || { echo "!! convert failed: ${var}"; return 1; }
}

# -------------------------------------------------------------------------------------
# 並列実行 (同時に走らせるのは最大 MAXJOBS 個)
# -------------------------------------------------------------------------------------
pids=()
for var in qp t1 t2 t3 t4 res; do
  plot_one "$var" &
  pids+=($!)
  while (( $(jobs -rp | wc -l) >= MAXJOBS )); do sleep 1; done
done

fail=0
for pid in "${pids[@]}"; do
  wait "$pid" || fail=1
done

if (( fail )); then
  echo "Some jobs failed. Check logs in $WORKDIR"
  exit 1
fi
echo "All done: day=${day}"
