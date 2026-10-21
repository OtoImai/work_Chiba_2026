#!/bin/bash
set -e -x

BASEDIR=/raid/users/imai/work_Chiba_2026
FIGSDIR="$BASEDIR"/figure/synop
DATADIR="$BASEDIR"/data
PRSDIR="$DATADIR"/pressure
SFCDIR="$DATADIR"/single
CLMDIR="$DATADIR"/clim

mkdir -p "$FIGSDIR"


lon0=135
lon1=145
lat0=33
lat1=40

day=13
for hh in 00 06 12 18; do 
	for lev in 8.5 7 5; do

		#arr1=5
		#arr2=15
		#arr3=20
		#
		#sk=16
	
		date=${hh}z${day}
	
		FIGURENAME=omega_${lev}_${date}
		
		echo ${FIGURENAME}
		cat>w.gs<<eof
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
'set xlint 2'
'set ylint 2'

'sdfopen ${PRSDIR}/w_202608.nc'
'set lon ${lon0} ${lon1}'
'set lat ${lat0} ${lat1}'
'set lev ${lev}'

'set time ${date}'
'w=w'  

'set gxout shade2'
'color -1.0 1.0 0.1 -kind green->white->orange'
'd w'
'xcbar 5.2 5.3 1.0 5.0 -line on -edge triangle -fs 2 -direction v' 

'print -R ${FIGSDIR}/${FIGURENAME}.eps'
'quit'
eof
		grads -lbc w.gs
		rm -f w.gs

		convert -density 900 -resize 800 -background white -flatten ${FIGSDIR}/${FIGURENAME}.eps ${FIGSDIR}/${FIGURENAME}.png

	done # lev
done # hh	
