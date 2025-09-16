#!/usr/bin/bash

generate() {
    size2d="${size}x${size}"

    echo "Generating CTM images..."
    for i in $(seq 0 46); do
        rm -f "${dir}/${i}.png"
    done

    offset_x="${OFFSET_X:-0}"
    offset_y="${OFFSET_Y:-0}"

    offset_size_x="$((${size} + ${offset_x}))"
    offset_size_y="$((${size} + ${offset_y}))"
    off__="+${offset_x}+${offset_y}"
    offx_="+${offset_size_x}+${offset_y}"
    off_y="+${offset_x}+${offset_size_y}"
    offxy="+${offset_size_x}+${offset_size_y}"

    magick -background none "${base_file}" -crop "${size2d}${off__}" +repage -strip "${dir}/0.png"

    offset_x="$(( ${offset_x} * 2 ))"
    offset_y="$(( ${offset_y} * 2 ))"

    offset_size_x="$((${size} + ${offset_x}))"
    offset_size_y="$((${size} + ${offset_y}))"
    off__="+${offset_x}+${offset_y}"
    offx_="+${offset_size_x}+${offset_y}"
    off_y="+${offset_x}+${offset_size_y}"
    offxy="+${offset_size_x}+${offset_size_y}"

    magick -background none "${compact_file}" -crop "${size2d}${off__}" +repage -strip "${dir}/1.png"
    magick -background none "${compact_file}" -crop "${size2d}${offx_}" +repage -strip "${dir}/2.png"
    magick -background none "${compact_file}" -crop "${size2d}${off_y}" +repage -strip "${dir}/3.png"
    magick -background none "${compact_file}" -crop "${size2d}${offxy}" +repage -strip "${dir}/4.png"

    echo "Done!"
    echo
}

export -f generate
