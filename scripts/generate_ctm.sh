#!/usr/bin/bash

# Angelica doesn't support ctm_compact yet, so use the full ctm generation script instead.
# https://github.com/GTNewHorizons/Angelica/issues/1020
# https://github.com/ABKQPO/Modernity-GTNH/issues/55

echo "Note:"
echo "1. Run the script in the root folder! Don't run it in the 'scripts' folder."
echo "2. The generation scripts make use of ImageMagick, please have it installed on your system."
echo "3. This script uses 'GNU Parallel' (command 'parallel') to run the generation scripts in parallel, in order to speed up generation."
echo

SCRIPT="${PWD}/scripts/ctm.sh"
echo "Using generation script: ${SCRIPT}"
echo

if [[ -z "$TARGETS" ]]; then
    TARGETS="$(cat "${PWD}/scripts/targets.txt")"
fi
TARGETS="$(echo "${TARGETS}" | tr ' ' '\n')"

dir="${PWD}/assets/minecraft/mcpatcher/ctm/Modernity-GTNH/"
echo "Project dir: ${dir}"
echo

cd "${dir}" || exit

GLOBBED_TARGETS=""
while read line; do
    if [[ "${line}" ]]; then
        GLOBBED_TARGETS="${GLOBBED_TARGETS} $(echo ${line})"
    fi
done <<< "${TARGETS}"
GLOBBED_TARGETS="${GLOBBED_TARGETS:1}"
GLOBBED_TARGETS="$(echo "${GLOBBED_TARGETS}" | tr " " "\n")"

echo "List of targets:"
echo "${GLOBBED_TARGETS}"
echo

export SCRIPT
generate() {
    local f="$1"
    if [[ -n "${f}" ]]; then
        "${SCRIPT}" "${f}" 16 "ctm.png" "base.png" "full" > /dev/null
   fi
}
export -f generate

echo "Generating..."

echo "${GLOBBED_TARGETS}" | parallel --bar generate
echo
echo "Done!"
