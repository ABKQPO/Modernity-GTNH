#!/usr/bin/bash

# Angelica doesn't support ctm_compact yet, so use the full ctm generation script instead.
# https://github.com/GTNewHorizons/Angelica/issues/1020
# https://github.com/ABKQPO/Modernity-GTNH/issues/55

echo "Note:"
echo "1. Run the script in the root folder! Don't run it in the 'scripts' folder."
echo "2. The generation scripts make use of ImageMagick, please have it installed on your system."
echo "3. This script uses 'GNU Parallel' (command 'parallel') to run the generation scripts in parallel, in order to speed up generation."
echo

SCRIPT="$PWD/scripts/ctm/gen.sh"
echo "Using generation script:"
echo "$SCRIPT"
echo

DEFAULT_LOG_FILE="$PWD/scripts/ctm.log"
LOG_FILE="${LOG_FILE:-"$DEFAULT_LOG_FILE"}"
if [[ -n "$LOG_FILE" ]]; then
    touch "$LOG_FILE"
    printf "" > "$LOG_FILE"
else
    LOG_FILE="/dev/null"
fi
echo "Script log file:"
echo "$LOG_FILE"
echo

if [[ -z "$TARGETS" ]]; then
    TARGETS="$(cat "$PWD/scripts/targets.txt")"
fi
TARGETS="$(echo "$TARGETS" | tr " " "\n")"

dir="$PWD/assets/minecraft/mcpatcher/ctm/Modernity-GTNH/gtnh"
echo "Project dir:"
echo "$dir"
echo

cd "$dir" || exit

GLOBBED_TARGETS=""
while read line; do
    if [[ "$line" ]]; then
        GLOBBED_TARGETS="$GLOBBED_TARGETS $(echo $line)"
    fi
done <<< "$TARGETS"
GLOBBED_TARGETS="${GLOBBED_TARGETS:1}"
GLOBBED_TARGETS="$(echo "$GLOBBED_TARGETS" | tr " " "\n")"

export SCRIPT
export LOG_FILE
generate() {
    local f="$1"

    if [[ -n "$f" ]]; then
        OUTPUT=$("$SCRIPT" "$f" 16 "ctm.png" "base.png" "full" 2>&1)

        echo "---------
$OUTPUT
---------
" >> "$LOG_FILE"
    fi
}
export -f generate

echo "Generating..."
echo "$GLOBBED_TARGETS" | parallel --bar generate
echo
echo "Done!"
