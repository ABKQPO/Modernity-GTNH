dir="$1"
size="$2"
compact_image="$3"
base_image="$4"
method="$5"

exiting=""

if [[ -z "${dir}" ]]; then
    echo "Output directory missing. Please input the directory the files should go to as the 1st argument." >&2
    exiting=1
fi

if [[ -z "${size}" ]]; then
    echo "Tile size missing. Please input the tile size in pixels as the 2nd argument." >&2
    exiting=1
fi

if [[ -z "${compact_image}" ]]; then
    echo "Compact CTM image file name missing. Please input the file name of the image as the 3rd argument." >&2
    exiting=1
fi

if [[ -z "${base_image}" ]]; then
    echo "Base tile texture file name missing. Please input the file name of the image as the 4th argument." >&2
    exiting=1
fi

if [[ -z "${method}" ]]; then
    echo "CTM method missing. Please input the CTM method to generate as the 5th argument." >&2
    exiting=1
fi

if [[ "${exiting}" ]]; then
    echo "Usage: [WORKING DIR] [TILE SIZE] [COMPACT CTM FILE] [BASE TEXTURE IMAGE FILE] [METHOD]"
    echo
    exit 1
fi

script_dir="$(dirname "$0")"
case "${method}" in
    "full")
        TILE_LAST_INDEX=46
        . "${script_dir}/ctm_full.sh"
    ;;

    "compact")
        TILE_LAST_INDEX=4
        . "${script_dir}/ctm_compact.sh"
    ;;

    *)
        echo "Incorrect method input. Valid methods: full, compact." >&2
        exit 1
    ;;
esac

echo "Working dir: ${dir}"

if [[ ! -d "${dir}" ]]; then
    echo "Working dir doesn't exist! Aborted." >&2
    echo "Working dir: '${dir}'." >&2
    exit 1
fi

base_file="${dir}/${base_image}"
compact_file="${dir}/${compact_image}"

if [[ ! -f "${base_file}" ]]; then
    echo "Base tile texture file doesn't exist! Aborted." >&2
    echo "Working dir: '${dir}'." >&2
    exit 1
fi


if [[ ! -f "${compact_file}" ]]; then
    echo "Compact CTM image file doesn't exist! Aborted." >&2
    echo "Working dir: '${dir}'." >&2
    exit 1
fi



id_override_file="${dir}/id_override"
if [[ -f "${id_override_file}" ]]; then
    tile_id=$(cat "${id_override_file}")
else
    tile_id=$(basename "${dir}" | cut -d "@" -f 1)
fi
if [[ -z "${tile_id}" ]]; then
    echo "Tile ID is missing from directory structure." >&2
    echo "Working dir: '${dir}'." >&2
    exit 1
fi
echo "Tile ID: ${tile_id}"

mod_id=$(basename "$(dirname "${dir}")")
if [[ -z "${mod_id}" ]]; then
    echo "Mod ID is missing from directory structure." >&2
    echo "Working dir: '${dir}'." >&2
    exit 1
fi
echo "Mod ID: ${mod_id}"
echo



override_properties="$(cat "${dir}/properties" 2>/dev/null)"
if [[ -n "${override_properties}" ]]; then
    echo "Override properties:
---
${override_properties}
---
"

    override_properties="
${override_properties}"

fi

ctm_properties="matchBlocks=${mod_id}:${tile_id}
tiles=0-${TILE_LAST_INDEX}
method=ctm${override_properties}"

echo "Generated CTM Properties file:
---
${ctm_properties}
---
"

echo "${ctm_properties}" > "${dir}/ctm.properties"




animation_mcmeta_file="${dir}/animation_mcmeta"
animation_frames_file="${dir}/animation_frames"

export dir
export size
export base_file
export compact_file
export animation_mcmeta_file

if [[ -f "${animation_mcmeta_file}" && -f "${animation_frames_file}" ]]; then
    animation_frames="$(cat "${animation_frames_file}" || exit 1)"
    echo "Animation detected! The generated CTM will be animated according to the frame count of ${animation_frames}."

    export animation_frames

    prepare_frame() {
        local frame="$1"
        local frame_dir="${dir}/frame${frame}"

        mkdir "${frame_dir}"
        OFFSET_Y="$(( ${frame} * ${size} ))" dir="${frame_dir}" generate
    }
    export -f prepare_frame

    make_frame() {
        local i="$1"
        local animated_files=""
        for frame in $(seq 0 $(( $animation_frames - 1 ))); do
            local frame_dir="${dir}/frame${frame}"

            local animated_files="${animated_files} ${frame_dir}/${i}.png"
        done

        montage -background none -tile "1x${animation_frames}" -geometry +0+0 $(echo "${animated_files}" | xargs) +repage "${dir}/${i}.png"
        cp "${animation_mcmeta_file}" "${dir}/${i}.png.mcmeta"
    }
    export -f make_frame

    finish_frame() {
        local frame="$1"
        local frame_dir="${dir}/frame${frame}"

        rm -rf "${frame_dir}"
    }
    export -f finish_frame

    echo "$(seq 0 $(( $animation_frames - 1 )))" | parallel prepare_frame
    echo "$(seq 0 ${TILE_LAST_INDEX})" | parallel make_frame
    echo "$(seq 0 $(( $animation_frames - 1 )))" | parallel finish_frame
else
    generate
fi
