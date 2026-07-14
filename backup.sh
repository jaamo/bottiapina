#!/usr/bin/env bash
# Back up the production database from the Raspberry Pi to this folder.
set -euo pipefail

REMOTE="pi@192.168.1.75"
REMOTE_DIR="/home/pi/bottiapina"

cd "$(dirname "$0")"

echo "Backing up bottiapina.db from ${REMOTE} ..."
rsync -av "${REMOTE}:${REMOTE_DIR}/bottiapina.db" .

echo "Done. Saved to ./bottiapina.db"
