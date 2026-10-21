#!/bin/bash
set -e -x

BASEDIR=/raid/users/imai/work_Chiba_2026
FIGSDIR="$BASEDIR"/figure/synop
DATADIR="$BASEDIR"/data
PRSDIR="$DATADIR"/pressure
SFCDIR="$DATADIR"/single
CLMDIR="$DATADIR"/clim

mkdir -p "$FIGSDIR"


lon0=70
lon1=185
lat0=20
lat1=70
lev=3

day=09

arr1=5
arr2=15
arr3=20

sk=16

FIGURENAME=hgt300_${day}

cat>hgt.gs<<eof
'reinit'

'set display color white'
'c'
'set grads off'
'set parea 1.0 9.0 1.0 5.0'
'set mpdset mres'
'set poli off'
'set annot 1 4'
'set map 1 1 5'
'set xlopts 1 4 0.14'
'set ylopts 1 4 0.14'
'set xlint 15'
'set ylint 10'

'sdfopen ${CLMDIR}/pressure/z_monmean_1991_2020.nc'

'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'
'set lev ${lev}'
'set t 8'

'define zclm=z / 9.8'
'close 1'

'sdfopen ${PRSDIR}/z_202608.nc'
'sdfopen ${PRSDIR}/u_202608.nc'
'sdfopen ${PRSDIR}/v_202608.nc'

'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'
'set lev ${lev}'
'set time 00z${day}'

'define z=ave(z.1,time=00z${day},time=23z${day}) / 9.8'
'define u=ave(u.2,time=00z${day},time=23z${day})'
'define v=ave(v.3,time=00z${day},time=23z${day})'

'set gxout shade2'
'color -250 250 25 -kind blue->white->red'
'd z-zclm'
'xcbar 9.1 9.2 1.0 5.0 -line on -edge triangle -fs 2 -direction v'

'mg=mag(u,v)'

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

grads -lbc hgt.gs

convert -density 900 -resize 800 -background white -flatten ${FIGSDIR}/${FIGURENAME}.eps ${FIGSDIR}/${FIGURENAME}.png

rm -f hgt.gs
