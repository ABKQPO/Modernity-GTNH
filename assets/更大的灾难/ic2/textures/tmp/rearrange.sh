#!/bin/bash

convert "$1" -define png:color-type=6 -crop 16x16@ +repage +adjoin tmp%d.png

for (( i=0; i < 16; i++ )); do
	merge=
	for (( j=$i; j < 192; j = j + 16 )); do
		
		merge="$merge tmp$j.png"
	done
	
	convert$merge +append "${1%.*}.$i.png"
done

rm tmp*.png
