#!/bin/bash
set -e -x

BASEDIR=/raid/users/imai/work_Chiba_2026
FIGSDIR="$BASEDIR"/figure/synop
DATADIR="$BASEDIR"/data
PRSDIR="$DATADIR"/pressure
SFCDIR="$DATADIR"/single
CLMDIR="$DATADIR"/clim

mkdir -p "$FIGSDIR"

lon0=100
lon1=185
lat0=5
lat1=55

day=12
time=00z$day

arr1=100
arr2=200
arr3=400

sk=16

FIGURENAME=ivt_${day}
cat>ivt.gs<<eof
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

'sdfopen ${CLMDIR}/single/viwve_monmean_1991_2020.nc'
'sdfopen ${CLMDIR}/single/viwvn_monmean_1991_2020.nc'

'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'
'set t 8'

'define uwclm=viwve.1'
'define vwclm=viwvn.2'
'define mgclm=mag(uwclm,vwclm)'

'close 2'
'close 1'

'sdfopen ${SFCDIR}/viwve_202608.nc'
'sdfopen ${SFCDIR}/viwvn_202608.nc'

'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'
'set time ${time}'

'define uw=viwve.1'
'define vw=viwvn.2'
'define mg=mag(uw,vw)'

'set gxout shade2'
'color 0 1200 100 -kind white->limegreen->green->darkgreen'
'd mg-mgclm'
'xcbar 5.1 5.2 1.0 5.0 -line on -edge triangle -fs 2 -direction v'

'set gxout vector'
#'set cthick 3'
#'set arrowhead 0.08'
#'set arrscl 0.3 1500'
#'set ccolor 15'
#'d skip(maskout(maskout(uw,mg-${arr1}),${arr2}-mg),${sk});vw'
'set cthick 3'
'set arrowhead 0.08'
'set arrscl 0.3 1500'
'set ccolor 1'
#'d skip(maskout(maskout(uw,mg-${arr1}),${arr3}-mg),${sk});vw'
'd skip(maskout(maskout(uw-uwclm,mg-${arr1}),${arr3}-mg+mgclm),${sk});(vw-vwclm)'
'set cthick 10'
'set arrowhead 0.08'
'set arrscl 0.3 1500'
'set ccolor 0'
#'d skip(maskout(uw,mg-${arr3}),${sk});vw'
'd skip(maskout(uw-uwclm,mg-mgclm-${arr3}),${sk});(vw-vwclm)'
'set cthick 5'
'set arrowhead 0.08'
'set arrscl 0.3 1500'
'set ccolor 1'
'd skip(maskout(uw-uwclm,mg-mgclm-${arr3}),${sk});(vw-vwclm)'


'print -R ${FIGSDIR}/${FIGURENAME}.eps'
'quit'
eof

grads -lbc ivt.gs

convert -density 900 -resize 800 -background white -flatten ${FIGSDIR}/${FIGURENAME}.eps ${FIGSDIR}/${FIGURENAME}.png

rm -f ivt.gs
