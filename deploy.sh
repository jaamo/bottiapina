#!/usr/bin/env bash
# Deploy the bot to the production Raspberry Pi.
# Syncs Python source files; does NOT touch the remote database or .env.
set -euo pipefail

REMOTE="pi@192.168.1.75"
REMOTE_DIR="/home/pi/bottiapina"

cd "$(dirname "$0")"

echo "Deploying to ${REMOTE}:${REMOTE_DIR} ..."
rsync -av ./*.py "${REMOTE}:${REMOTE_DIR}/"
rsync -av ./extensions/*.py "${REMOTE}:${REMOTE_DIR}/extensions/"

echo "Done. Remember to restart the bot on the server."
