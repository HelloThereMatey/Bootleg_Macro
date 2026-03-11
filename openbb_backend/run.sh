#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "Starting Bootleg Macro backend for OpenBB Pro on http://localhost:5050"
uvicorn main:app --host localhost --port 5050 --reload
