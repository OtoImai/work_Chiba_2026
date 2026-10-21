#!/bin/bash
# =====================================================================================
# Linear decomposition of slhf using ERA5 single level data (e.g., Tanimoto etal.2003)
#  Q' = t1 + t2 + t3 + t4 (+ res)
#  t1: Wind speed term : coef * W' * (qs_c - qa_c)
#	 t2: SST term        : coef * Wc * qs'
#  t3: Humidity term   : coef * Wc * (-qa')
#  t4: Nonlinear term  : coef * W' * (qs' - qa')
#  coef = QC / (Wc * (qs_c - qa_c))  (rho*L*C_E, calculated from climatology)
# =====================================================================================

#set -e -x

BASEDIR=/raid/users/imai/work_Chiba_2026
FIGSDIR="$BASEDIR"/figure/synop
DATADIR="$BASEDIR"/data
SFCDIR="$DATADIR"/single
CLMDIR="$DATADIR"/clim/single
mkdir -p "$FIGSDIR"

lon0=110; lon1=185; lat0=0; lat1=50
month=8
day=13
time0=00z${day} 
time1=23z${day} 

P0=1013.25
SALF=1.0

	FIGURENAME=lh_decomp_${ttl}_${day}
	
	echo "# ====================================================================================="
	echo "# Linear decomposition of slhf using ERA5 single level data (e.g., Tanimoto etal.2003) "
	echo "#  Q' = t1 + t2 + t3 + t4 (+ res)																											 "
	echo "#  t1: Wind speed term : coef * W' * (qs_c - qa_c)																		 "
	echo "#	 t2: SST term        : coef * Wc * qs'																							 "
	echo "#  t3: Humidity term   : coef * Wc * (-qa')																						 "
	echo "#  t4: Nonlinear term  : coef * W' * (qs' - qa') 																			 "
	echo "#  coef = QC / (Wc * (qs_c - qa_c))  (rho*L*C_E, calculated from climatology)					 "
	echo "# ====================================================================================="

	echo "## Plotting ${ttl}"

	cat>lh_decomp.gs<<eof
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
'sdfopen ${CLMDIR}/wspd_monmean_1991_2020.nc'
'sdfopen ${CLMDIR}/sst_monmean_1991_2020.nc'
'sdfopen ${CLMDIR}/d2m_monmean_1991_2020.nc'
'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'
'set t ${month}'

'set dfile 1'
'define qc=-1*slhf/86400'
'set dfile 2'
'define wc=wspd'
'set dfile 3'
'define tsc=sst-273.15'
'define esc=6.112*exp(17.67*tsc/(tsc+243.5))'
'define qsc=${SALF}*0.622*esc/(${P0}-0.378*esc)'
'set dfile 4'
'define tdc=d2m-273.15'
'define eac=6.112*exp(17.67*tdc/(tdc+243.5))'
'define qac=0.622*eac/(${P0}-0.378*eac)'
'define dqc=qsc-qac'

'define coef=maskout(qc/(wc*dqc),abs(dqc)-0.001)'

'close 4'
'close 3'
'close 2'
'close 1'

'sdfopen ${SFCDIR}/lh_202608.nc'
'sdfopen ${SFCDIR}/u10m_202608.nc'
'sdfopen ${SFCDIR}/v10m_202608.nc'
'sdfopen ${SFCDIR}/sst_202608.nc'
'sdfopen ${SFCDIR}/d2m_202608.nc'

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

'define tsh=sst-273.15'
'define esh=6.112*exp(17.67*tsh/(tsh+243.5))' 
'define qsh=${SALF}*0.622*esh/(${P0}-0.378*esh)'
'define tdh=d2m-273.15'
'define eah=6.112*exp(17.67*tdh/(tdh+243.5))'
'define qah=0.622*eah/(${P0}-0.378*eah)'

'set time ${time0}'

'define qs=ave(qsh,time=${time0},time=${time1})'
'define qa=ave(qah,time=${time0},time=${time1})'
'define q=ave(-1*lh/3600,time=${time0},time=${time1})'

'define uu=ave(u,time=${time0},time=${time1})'
'define vv=ave(v,time=${time0},time=${time1})'
'define w=mag(uu,vv)'

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
'd $var'

'xcbar 5.1 5.2 1.0 5.0 -line on -edge triangle -fs 2 -direction v'
'print -R ${FIGSDIR}/${FIGURENAME}.eps'
'quit'
eof

grads -lbc lh_decomp.gs
rm -f lh_decomp.gs

convert -density 900 -resize 800 -background white -flatten ${FIGSDIR}/${FIGURENAME}.eps ${FIGSDIR}/${FIGURENAME}.png

done # var
