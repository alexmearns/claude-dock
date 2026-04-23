#!/usr/bin/env bash
# Launch Claude Dock on Mac or Linux.
# Run once: chmod +x launch.sh && ./launch.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

python3 -m pip install -q -r "$DIR/requirements.txt"
python3 "$DIR/dock.py" &
disown
