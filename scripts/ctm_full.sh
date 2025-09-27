#!/usr/bin/bash

generate() {
    base="mpr:base"
    base_00="mpr:base_tl"
    base_x0="mpr:base_tr"
    base_0y="mpr:base_bl"
    base_xy="mpr:base_br"

    center="mpr:center"
    center_00="mpr:center_tl"
    center_x0="mpr:center_tr"
    center_0y="mpr:center_bl"
    center_xy="mpr:center_br"

    vertical="mpr:vertical"
    vertical_00="mpr:vertical_tl"
    vertical_x0="mpr:vertical_tr"
    vertical_0y="mpr:vertical_bl"
    vertical_xy="mpr:vertical_br"

    horizontal="mpr:horizontal"
    horizontal_00="mpr:horizontal_tl"
    horizontal_x0="mpr:horizontal_tr"
    horizontal_0y="mpr:horizontal_bl"
    horizontal_xy="mpr:horizontal_br"

    cross="mpr:cross"
    cross_00="mpr:cross_tl"
    cross_x0="mpr:cross_tr"
    cross_0y="mpr:cross_bl"
    cross_xy="mpr:cross_br"



    size2d="${size}x${size}"
    halfsize="$((${size} / 2))"
    halfsize2d="${halfsize}x${halfsize}"

    b_offset_x="${OFFSET_X:-0}"
    b_offset_y="${OFFSET_Y:-0}"

    #b_offset_size_x="$((${size} + ${b_offset_x}))"
    #b_offset_size_y="$((${size} + ${b_offset_y}))"
    b_off__="+${b_offset_x}+${b_offset_y}"
    #b_offx_="+${b_offset_size_x}+${b_offset_y}"
    #b_off_y="+${b_offset_x}+${b_offset_size_y}"
    #b_offxy="+${b_offset_size_x}+${b_offset_size_y}"

    c_offset_x="$(( ${b_offset_x} * 2 ))"
    c_offset_y="$(( ${b_offset_y} * 2 ))"

    c_offset_size_x="$((${size} + ${c_offset_x}))"
    c_offset_size_y="$((${size} + ${c_offset_y}))"
    c_off__="+${c_offset_x}+${c_offset_y}"
    c_offx_="+${c_offset_size_x}+${c_offset_y}"
    c_off_y="+${c_offset_x}+${c_offset_size_y}"
    c_offxy="+${c_offset_size_x}+${c_offset_size_y}"

    off__="+0+0"
    offx_="+${halfsize}+0"
    off_y="+0+${halfsize}"
    offxy="+${halfsize}+${halfsize}"

    geometry="${halfsize2d}${off__}"

    echo "Generating CTM images..."
    for i in $(seq 0 46); do
        rm -f "${dir}/${i}.png"
    done

    grid() {
        echo \( "${1}" "${2}" +append \) \( "${3}" "${4}" +append \) -append -geometry "${geometry}"
    }

    magick \
        -background none -filter Point \
        -respect-parentheses \
            \( "${base_file}"    -crop "${size2d}${b_off__}" +repage +write "${base}"        \) \
            \( "${compact_file}" -crop "${size2d}${c_off__}" +repage +write "${center}"      \) \
            \( "${compact_file}" -crop "${size2d}${c_offx_}" +repage +write "${vertical}"    \) \
            \( "${compact_file}" -crop "${size2d}${c_off_y}" +repage +write "${horizontal}"  \) \
            \( "${compact_file}" -crop "${size2d}${c_offxy}" +repage +write "${cross}"       \) \
            \
            \
            \( "${base}" -crop "${halfsize2d}${off__}" +write "${base_00}" \) \
            \( "${base}" -crop "${halfsize2d}${offx_}" +write "${base_x0}" \) \
            \( "${base}" -crop "${halfsize2d}${off_y}" +write "${base_0y}" \) \
            \( "${base}" -crop "${halfsize2d}${offxy}" +write "${base_xy}" \) \
            \
            \( "${center}" -crop "${halfsize2d}${off__}" +write "${center_00}" \) \
            \( "${center}" -crop "${halfsize2d}${offx_}" +write "${center_x0}" \) \
            \( "${center}" -crop "${halfsize2d}${off_y}" +write "${center_0y}" \) \
            \( "${center}" -crop "${halfsize2d}${offxy}" +write "${center_xy}" \) \
            \
            \( "${vertical}" -crop "${halfsize2d}${off__}" +write "${vertical_00}" \) \
            \( "${vertical}" -crop "${halfsize2d}${offx_}" +write "${vertical_x0}" \) \
            \( "${vertical}" -crop "${halfsize2d}${off_y}" +write "${vertical_0y}" \) \
            \( "${vertical}" -crop "${halfsize2d}${offxy}" +write "${vertical_xy}" \) \
            \
            \( "${horizontal}" -crop "${halfsize2d}${off__}" +write "${horizontal_00}" \) \
            \( "${horizontal}" -crop "${halfsize2d}${offx_}" +write "${horizontal_x0}" \) \
            \( "${horizontal}" -crop "${halfsize2d}${off_y}" +write "${horizontal_0y}" \) \
            \( "${horizontal}" -crop "${halfsize2d}${offxy}" +write "${horizontal_xy}" \) \
            \
            \( "${cross}" -crop "${halfsize2d}${off__}" +write "${cross_00}" \) \
            \( "${cross}" -crop "${halfsize2d}${offx_}" +write "${cross_x0}" \) \
            \( "${cross}" -crop "${halfsize2d}${off_y}" +write "${cross_0y}" \) \
            \( "${cross}" -crop "${halfsize2d}${offxy}" +write "${cross_xy}" \) \
            \
            \
            \( "${base}" -geometry +0+0 -strip +write "${dir}/0.png" \) \
    `# horizontal row` \
            \( $( grid "${base_00}" "${horizontal_x0}" "${base_0y}" "${horizontal_xy}" ) -strip +write "${dir}/1.png" \) \
            \( "${horizontal}" -geometry +0+0 -strip +write "${dir}/2.png" \) \
            \( $( grid "${horizontal_00}" "${base_x0}" "${horizontal_0y}" "${base_xy}" ) -strip +write "${dir}/3.png" \) \
    `# corners 1` \
            \( $( grid "${base_00}" "${horizontal_x0}" "${vertical_0y}" "${cross_xy}"     ) -strip +write  "${dir}/4.png" \) \
            \( $( grid "${horizontal_00}" "${base_x0}" "${cross_0y}" "${vertical_xy}"     ) -strip +write  "${dir}/5.png" \) \
            \( $( grid "${vertical_00}" "${cross_x0}" "${base_0y}" "${horizontal_xy}"     ) -strip +write "${dir}/16.png" \) \
            \( $( grid "${cross_00}" "${vertical_x0}" "${horizontal_0y}" "${base_xy}"     ) -strip +write "${dir}/17.png" \) \
    `# corners 2` \
            \( $( grid "${vertical_00}" "${cross_x0}" "${vertical_0y}" "${cross_xy}"      ) -strip +write "${dir}/6.png"  \) \
            \( $( grid "${horizontal_00}" "${horizontal_x0}" "${cross_0y}" "${cross_xy}"  ) -strip +write "${dir}/7.png"  \) \
            \( $( grid "${cross_00}" "${cross_x0}" "${horizontal_0y}" "${horizontal_xy}"  ) -strip +write "${dir}/18.png" \) \
            \( $( grid "${cross_00}" "${vertical_x0}" "${cross_0y}" "${vertical_xy}"      ) -strip +write "${dir}/19.png" \) \
    `# corners 3` \
            \( $( grid "${vertical_00}" "${cross_x0}" "${vertical_0y}" "${center_xy}"     ) -strip +write "${dir}/28.png" \) \
            \( $( grid "${horizontal_00}" "${horizontal_x0}" "${center_0y}" "${cross_xy}" ) -strip +write "${dir}/29.png" \) \
            \( $( grid "${cross_00}" "${center_x0}" "${horizontal_0y}" "${horizontal_xy}" ) -strip +write "${dir}/40.png" \) \
            \( $( grid "${center_00}" "${vertical_x0}" "${cross_0y}" "${vertical_xy}"     ) -strip +write "${dir}/41.png" \) \
    `# corners 4` \
            \( $( grid "${vertical_00}" "${center_x0}" "${vertical_0y}" "${cross_xy}"     ) -strip +write "${dir}/30.png" \) \
            \( $( grid "${horizontal_00}" "${horizontal_x0}" "${cross_0y}" "${center_xy}" ) -strip +write "${dir}/31.png" \) \
            \( $( grid "${center_00}" "${cross_x0}" "${horizontal_0y}" "${horizontal_xy}" ) -strip +write "${dir}/42.png" \) \
            \( $( grid "${cross_00}" "${vertical_x0}" "${center_0y}" "${vertical_xy}"     ) -strip +write "${dir}/43.png" \) \
    `# cross dots` \
            \( $( grid "${cross_00}" "${center_x0}" "${cross_0y}" "${cross_xy}"   ) -strip +write  "${dir}/8.png" \) \
            \( $( grid "${cross_00}" "${cross_x0}" "${cross_0y}" "${center_xy}"   ) -strip +write  "${dir}/9.png" \) \
            \( $( grid "${center_00}" "${cross_x0}" "${cross_0y}" "${cross_xy}"   ) -strip +write "${dir}/20.png" \) \
            \( $( grid "${cross_00}" "${cross_x0}" "${center_0y}" "${cross_xy}"   ) -strip +write "${dir}/21.png" \) \
    `# cross bars` \
            \( $( grid "${center_00}" "${cross_x0}" "${center_0y}" "${cross_xy}"  ) -strip +write "${dir}/10.png" \) \
            \( $( grid "${center_00}" "${center_x0}" "${cross_0y}" "${cross_xy}"  ) -strip +write "${dir}/11.png" \) \
            \( $( grid "${cross_00}" "${cross_x0}" "${center_0y}" "${center_xy}"  ) -strip +write "${dir}/22.png" \) \
            \( $( grid "${cross_00}" "${center_x0}" "${cross_0y}" "${center_xy}"  ) -strip +write "${dir}/23.png" \) \
    `# cross corners` \
            \( $( grid "${center_00}" "${center_x0}" "${center_0y}" "${cross_xy}" ) -strip +write "${dir}/32.png" \) \
            \( $( grid "${center_00}" "${center_x0}" "${cross_0y}" "${center_xy}" ) -strip +write "${dir}/33.png" \) \
            \( $( grid "${center_00}" "${cross_x0}" "${center_0y}" "${center_xy}" ) -strip +write "${dir}/44.png" \) \
            \( $( grid "${cross_00}" "${center_x0}" "${center_0y}" "${center_xy}" ) -strip +write "${dir}/45.png" \) \
    `# cross diagnoals` \
            \( $( grid "${cross_00}" "${center_x0}" "${center_0y}" "${cross_xy}" ) -strip +write "${dir}/34.png" \) \
            \( $( grid "${center_00}" "${cross_x0}" "${cross_0y}" "${center_xy}" ) -strip +write "${dir}/35.png" \) \
            \( "${cross}" -geometry +0+0 -strip +write "${dir}/46.png" \) \
    `# vertical column` \
            \( $( grid "${base_00}" "${base_x0}" "${vertical_0y}" "${vertical_xy}" ) -strip +write "${dir}/12.png" \) \
            \( "${vertical}" -geometry +0+0 -strip +write "${dir}/24.png" \) \
            \( $( grid "${vertical_00}" "${vertical_x0}" "${base_0y}" "${base_xy}" ) -strip +write "${dir}/36.png" \) \
    `# panel` \
            \( $( grid "${base_00}" "${horizontal_x0}" "${vertical_0y}" "${center_xy}"     ) -strip +write "${dir}/13.png" \) \
            \( $( grid "${horizontal_00}" "${horizontal_x0}" "${center_0y}" "${center_xy}" ) -strip +write "${dir}/14.png" \) \
            \( $( grid "${horizontal_00}" "${base_x0}" "${center_0y}" "${vertical_xy}"     ) -strip +write "${dir}/15.png" \) \
            \( $( grid "${vertical_00}" "${center_x0}" "${vertical_0y}" "${center_xy}"     ) -strip +write "${dir}/25.png" \) \
            \( "${center}" -geometry +0+0 -strip +write "${dir}/26.png" \) \
            \( $( grid "${center_00}" "${vertical_x0}" "${center_0y}" "${vertical_xy}"     ) -strip +write "${dir}/27.png" \) \
            \( $( grid "${vertical_00}" "${center_x0}" "${base_0y}" "${horizontal_xy}"     ) -strip +write "${dir}/37.png" \) \
            \( $( grid "${center_00}" "${center_x0}" "${horizontal_0y}" "${horizontal_xy}" ) -strip +write "${dir}/38.png" \) \
            \( $( grid "${center_00}" "${vertical_x0}" "${horizontal_0y}" "${base_xy}"     ) -strip +write "${dir}/39.png" \) \
        null:

    echo "Done!"
    echo
}

export -f generate
