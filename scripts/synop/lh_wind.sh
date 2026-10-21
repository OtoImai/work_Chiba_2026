#!/bin/bash
set -e -x

BASEDIR=/raid/users/imai/work_Chiba_2026
FIGSDIR="$BASEDIR"/figure/synop
DATADIR="$BASEDIR"/data
PRSDIR="$DATADIR"/presure
SFCDIR="$DATADIR"/single
CLMDIR="$DATADIR"/clim

mkdir -p "$FIGSDIR"

lon0=110
lon1=185
lat0=0
lat1=50

day=7
time0=00z${day}
time1=23z${day}

arr1=0
arr2=0
arr3=3

sk=18

#FIGURENAME=lh_${day}
FIGURENAME=lh_clm

cat>lh.gs<<eof
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

'sdfopen ${CLMDIR}/single/lh_monmean_1991_2020.nc'
'sdfopen ${CLMDIR}/single/u10m_monmean_1991_2020.nc'
'sdfopen ${CLMDIR}/single/v10m_monmean_1991_2020.nc'
'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'
'set t 8'
'set dfile 1'
'define lhclm=-slhf/86400'
'set dfile 2'
'define uclm=u10'
'set dfile 3'
'define vclm=v10'

'define mgclm=mag(uclm,vclm)'
'close 3'
'close 2'
'close 1'

'sdfopen ${SFCDIR}/lh_202608.nc'
'sdfopen ${SFCDIR}/u10m_202608.nc'
'sdfopen ${SFCDIR}/v10m_202608.nc'
'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'
'set time ${time0}'

'set dfile 1'
'define lh=ave(-1*slhf/3600,time=${time0},time=${time1})'
'set dfile 2'
'define u=ave(u10,time=${time0},time=${time1})'
'set dfile 3'
'define v=ave(v10,time=${time0},time=${time1})'

'define mg=mag(u,v)'

'define lhanm=lh-lhclm'
'define uanm=u-uclm'
'define vanm=v-vclm'
'define mganm=mg-mgclm'


'set gxout shade2'
#'color -160 160 20 -kind navy->blue->skyblue->lightskyblue->white->gold->orange->red->palevioletred'
'color 0 160 5 -kind white->skyblue->blue->green->lime->yellow->orange->red->pink'
#'d lhanm'
'd lhclm'
'xcbar 5.1 5.2 1.0 5.0 -line on -edge triangle -fs 4 -direction v'

'set gxout vector'
'set cthick 3'
'set arrowhead 0.08'
'set arrscl 0.5 30'
'set ccolor 1'
#'d skip(maskout(maskout(uanm,mganm-${arr1}),${arr3}-mganm),${sk});vanm'
'd skip(maskout(maskout(uclm,mgclm-${arr1}),${arr3}-mgclm),${sk});vclm'
'set cthick 10'
'set arrowhead 0.08'
'set arrscl 0.5 30'
'set ccolor 0'

#'d skip(maskout(uanm,mganm-${arr3}),${sk});vanm'
'd skip(maskout(uclm,mgclm-${arr3}),${sk});vclm'
'set cthick 5'
'set arrowhead 0.08'
'set arrscl 0.5 30'
'set ccolor 1'
#'d skip(maskout(uanm,mganm-${arr3}),${sk});vanm'
'd skip(maskout(uclm,mgclm-${arr3}),${sk});vclm'

'print -R ${FIGSDIR}/${FIGURENAME}.eps'
'quit'
eof

grads -lbc lh.gs

convert -density 900 -resize 800 -background white -flatten ${FIGSDIR}/${FIGURENAME}.eps ${FIGSDIR}/${FIGURENAME}.png

rm -f lh.gs
