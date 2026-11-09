#!/usr/bin/env bash

set -u
MAX_ATTEMPTS=5
SLEEP_SECONDS=3

if [ $# -lt 1 ]; then
    echo "Upotreba: $0 <URL>" >&2
    echo "Primer: $0 http://localhost:8080" >&2
    exit 1
fi

BASE_URL="${1%/}"
HEALTH_URL="${BASE_URL}/health"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
    status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$HEALTH_URL")
    log "Pokušaj ${attempt}/${MAX_ATTEMPTS} - HTTP ${status}"

    if [ "$status" = "200" ]; then
        log "Aplikacija je zdrava."
        exit 0
    fi

    if [ "$attempt" -lt "$MAX_ATTEMPTS" ]; then
        sleep "$SLEEP_SECONDS"
    fi
done

log "Aplikacija nije zdrava ni posle ${MAX_ATTEMPTS} pokušaja."
exit 1