#!/bin/bash
set -e -x

BASEDIR=/raid/users/imai/work_Chiba_2026
FIGSDIR="$BASEDIR"/figure/synop
DATADIR="$BASEDIR"/data
MSWEPDIR="$DATADIR"/mswep

mkdir -p "$FIGSDIR"


lon0=129
lon1=148
lat0=23
lat1=48

day=13
time=202608$day

FIGURENAME=prec_${day}

cat>prec.gs<<eof
'reinit'

'set display color white'
'c'
'set grads off'
'set parea 1.0 5.0 1.0 5.0'
'set mpdset hires'
'set poli off'
'set annot 1 4'
'set map 1 1 5'
'set xlopts 1 4 0.14'
'set ylopts 1 4 0.14'
'set xlint 5'
'set ylint 5'

'sdfopen ${MSWEPDIR}/${time}.nc'

'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'

'set rgb 21 255 255 255'
'set rgb 22 255 219 175'
'set rgb 23 222 207 101'
'set rgb 24 137 193 83'
'set rgb 25   0 172 116'
'set rgb 26   0 143 135'
'set rgb 27   0 109 136'
'set rgb 28  47  69 139'

'set gxout shade2'
#'set clevs 10 15 20 30 40 60 80 100 120'
'set clevs 0.1 0.5 1 5 10 30 50 70 90'
'set ccols 21 21 21 22 23 24 25 26 27 28 28'

'd precipitation'
'xcbar 5.1 5.2 1.0 5.0 -line on -fs 1 -direction v'

'print -R ${FIGSDIR}/${FIGURENAME}.eps'
'quit'
eof

grads -lbc prec.gs

convert -density 900 -resize 800 -background white -flatten ${FIGSDIR}/${FIGURENAME}.eps ${FIGSDIR}/${FIGURENAME}.png

rm -f prec.gs
