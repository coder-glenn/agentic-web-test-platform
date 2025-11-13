#!/usr/bin/env bash
set -euo pipefail
OUTPUT="full_canvas_project.zip"
EXCLUDES=( ".git" "node_modules" ".venv" "__pycache__" "venv" "dist" "build" )
EXCLUDE_ARGS=()
for e in "${EXCLUDES[@]}"; do
  EXCLUDE_ARGS+=( "-x" "${e}/*" )
  EXCLUDE_ARGS+=( "-x" "${e}" )
done
zip -r "${OUTPUT}" . "${EXCLUDE_ARGS[@]}"
echo "Created ${OUTPUT}"
