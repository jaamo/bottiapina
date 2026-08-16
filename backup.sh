#!/usr/bin/env bash
# Back up the production database from the Raspberry Pi to this folder.
set -euo pipefail

REMOTE="pi@192.168.1.75"
REMOTE_DIR="/home/pi/bottiapina"

cd "$(dirname "$0")"

echo "Backing up bottiapina.db from ${REMOTE} ..."
# The database runs in WAL mode, so recent commits may still live in the
# bottiapina.db-wal file. The glob picks those up too when they exist.
rsync -av "${REMOTE}:${REMOTE_DIR}/bottiapina.db*" .

echo "Done. Saved to ./bottiapina.db"
