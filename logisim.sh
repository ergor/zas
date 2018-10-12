#!/bin/bash
OUTFILE='ram'
echo "v2.0 raw" > "$OUTFILE"
xxd -ps -g 1 -c 1 "$1" >> "$OUTFILE"
unset $OUTFILE
