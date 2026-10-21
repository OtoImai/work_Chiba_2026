#!/bin/bash
set -e -x

BASEDIR=/raid/users/imai/work_Chiba_2026
FIGSDIR="$BASEDIR"/figure/synop
DATADIR="$BASEDIR"/data
PRSDIR="$DATADIR"/pressure
SFCDIR="$DATADIR"/single
CLMDIR="$DATADIR"/clim

mkdir -p "$FIGSDIR"


lon0=110
lon1=195
lat0=10
lat1=60
lev=8.5
arr1=1
arr2=5
arr3=5
day=14
time=00z$day
sk=16

FIGURENAME=slp_wind850_${day}
cat>slp.gs<<eof
'reinit'

'set display color white'
'c'
'set grads off'
'set parea 1.0 7.0 1.0 5.0'
'set mpdset mres'
'set poli off'
'set annot 1 4'
'set map 1 1 5'
'set xlopts 1 4 0.14'
'set ylopts 1 4 0.14'
'set xlint 15'
'set ylint 10'

'sdfopen ${CLMDIR}/single/slp_monmean_1991_2020.nc'
'sdfopen ${CLMDIR}/pressure/u_monmean_1991_2020.nc'
'sdfopen ${CLMDIR}/pressure/v_monmean_1991_2020.nc'

'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'
'set t 8'
'set z 1'

'define slpclm=msl.1/100'

'define uclm=u.2(lev=${lev})'
'define vclm=v.3(lev=${lev})'

'define mgclm=mag(uclm,vclm)'

'close 3'
'close 2'
'close 1'

'sdfopen ${SFCDIR}/slp_202608.nc'
'sdfopen ${PRSDIR}/u_202608.nc'
'sdfopen ${PRSDIR}/v_202608.nc'

'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'
'set time ${time}'
'set z 1'

'define slp=ave(msl.1,time=00z$day,time=23z$day)/100'
'define u=ave(u.2(lev=${lev}),time=00z$day,time=23z$day)'
'define v=ave(v.3(lev=${lev}),time=00z$day,time=23z$day)'

'define mg=mag(u,v)'

'set gxout shade2'
'color -8 8 0.8 -kind blue->dodgerblue->skyblue->white->white->gold->darkorange->red'
'd slp-slpclm'
'xcbar 7.1 7.2 1.0 5.0 -line on -edge triangle -fs 2 -direction v'

'set gxout contour'
'set ccolor 0'
'set cthick 7'
'set cint 4'
'set clab off'
'd slp'
'set ccolor 1'
'set cthick 4'
'set clab masked'
'set cint 4'
'd slp'

'set gxout vector'
'set cthick 3'
'set arrowhead 0.08'
'set arrscl 0.5 40'
'set ccolor 1'
'd skip(maskout(maskout(u,mg-${arr1}),${arr3}-mg),${sk});v'
'set cthick 10'
'set arrowhead 0.08'
'set arrscl 0.5 40'
'set ccolor 0'
'd skip(maskout(u,mg-${arr3}),${sk});v'
'set cthick 5'
'set arrowhead 0.08'
'set arrscl 0.5 40'
'set ccolor 1'
'd skip(maskout(u,mg-${arr3}),${sk});v'


'print -R ${FIGSDIR}/${FIGURENAME}.eps'
'quit'
eof


grads -lbc slp.gs

convert -density 900 -resize 800 -background white -flatten ${FIGSDIR}/${FIGURENAME}.eps ${FIGSDIR}/${FIGURENAME}.png

rm -f slp.gs
