#!/bin/bash
set -e

case "$ROLE" in
  api)
    # STEP 8: API2.py
    echo "[entrypoint] Starting API2.py on port 5000..."
    exec python /app/API2.py
    ;;
  pipeline)
    # STEP 7: daily_run.py, which calls run_all.py
    # (run_all.py = steps 2 Fetch_params -> 3 Merging -> 5 recom7_2 -> 6 Saving_recom)
    echo "[entrypoint] Starting daily_run.py (fires run_all.py at ${DAILY_RUN_TIME:-17:20} daily)..."
    mkdir -p /app/input_params/Scheduled
    # recom7_2.py writes its loose output files relative to CWD — anchor
    # that CWD in the persisted input_params volume so nothing is lost.
    cd /app/input_params
    exec python /app/daily_run.py
    ;;
  *)
    echo "[entrypoint] ERROR: set ROLE=api or ROLE=pipeline"
    exit 1
    ;;
esac