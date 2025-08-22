#!/usr/bin/env bash
set -euo pipefail

for file in /work/*.template; do
  [ -f "$file" ] || continue
  out="/galaxy/server/config/$(basename "${file%.template}")"
  envsubst <"$file" >"$out"
  echo "Rendered $file → $out"
  cat "$out"
done
