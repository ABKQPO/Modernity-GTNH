#!/bin/bash

for (( i=0; i < 256; i++ )); do
	if [[ ! -f block$i.png ]]; then
		continue
	fi
	
	row=$((i / 16))
	col=$((i % 16))
	
	color=
	type=
	
	case "$col" in
	0) color=;;
	1) color=red;;
	2) color=green;;
	3) color=brown;;
	4) color=blue;;
	5) color=purple;;
	6) color=cyan;;
	7) color=lightGray;;
	8) color=gray;;
	9) color=pink;;
	10) color=lime;;
	11) color=yellow;;
	12) color=lightBlue;;
	13) color=magenta;;
	14) color=orange;;
	15) color=white;;
	esac
	
	case "$row" in
	0) type=Cable;;
	1) type=CableO;;
	2) type=GoldCable;;
	3) type=GoldCableI;;
	4) type=GoldCableII;;
	5) type=IronCable;;
	6) type=IronCableI;;
	7) type=IronCableII;;
	8) type=IronCableIIII;;
	9) type=GlassCable;;
	10) type=TinCable;;
	11) type=DetectorCable;;
	12) type=SplitterCable;;
	esac
	
	if [[ -z $color ]]; then
		mv block$i.png block.block$type.png
	else
		mv block$i.png block.block$type.$color.png
	fi
done
