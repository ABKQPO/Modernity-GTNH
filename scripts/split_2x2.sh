#!/usr/bin/bash

dir="$1"
size="$2"
compact_image="$3"

echo "Usage: [WORKING DIR] [TILE SIZE] [COMPACT CTM FILE]"

if [[ -z "${dir}" ]]; then
    echo "Output directory missing. Please input the directory the files should go to as the 1st argument."

    exit 1
fi

if [[ -z "${size}" ]]; then
    echo "Tile size missing. Please input the tile size in pixels as the 2nd argument."

    exit 1
fi

if [[ -z "${compact_image}" ]]; then
    echo "Compact CTM image file name missing. Please input the file name of the image as the 3rd argument."

    exit 1
fi

compact_file="${dir}/${compact_image}"

size2d="${size}x${size}"

off__="+0+0"
offx_="+${size}+0"
off_y="+0+${size}"
offxy="+${size}+${size}"

magick -background none "${compact_file}" -crop "${size2d}${off__}" +repage "1.png"
magick -background none "${compact_file}" -crop "${size2d}${offx_}" +repage "2.png"
magick -background none "${compact_file}" -crop "${size2d}${off_y}" +repage "3.png"
magick -background none "${compact_file}" -crop "${size2d}${offxy}" +repage "4.png"
