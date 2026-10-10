#!/bin/bash
cd "$(dirname "$0")/.."
INTERVAL=${1:-1800}
while true; do
  sleep "$INTERVAL"
  python3 -m scrapebench.auto_push "periodic results sync $(date +%Y%m%d-%H%M%S)" >> logs/watch_push.log 2>&1 || true
done
