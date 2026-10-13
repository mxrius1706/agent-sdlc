#!/usr/bin/env bash
# Start the project's dev server with its output in a log file, for the handlauf skill.
# Run with run_in_background: the script stays alive as long as the server does, and
# prints READY once the health endpoint answers.
#
# Usage:  bash <handlauf skill dir>/scripts/start-dev-logged.sh <logfile>
#
# The project's values come from the handlauf / dev server row in the root CLAUDE.md
# section "Project references" and are passed as environment variables. The script
# itself stays global; a project copy would stop receiving toolkit updates.
#
#   HL_DIR           directory to run in            default: the repository root
#   HL_CMD           the dev server command         default: npm run dev
#   HL_PORT          port it listens on             default: 3000
#   HL_HEALTH        URL that answers 200 when up   default: http://localhost:$HL_PORT/
#   HL_BUILD_MARKER  a production build artifact     default: .next/BUILD_ID
#                    whose presence breaks dev mode; leave empty to skip the check
#
# Exit codes before start:
#   2  the port is already taken (somebody else's server; ask before stopping it)
#   3  a production build is in the way; dev mode would serve broken routes
set -uo pipefail

LOG="${1:?usage: start-dev-logged.sh <logfile>}"

DIR="${HL_DIR:-$(git rev-parse --show-toplevel)}"
CMD="${HL_CMD:-npm run dev}"
PORT="${HL_PORT:-3000}"
HEALTH="${HL_HEALTH:-http://localhost:$PORT/}"
BUILD_MARKER="${HL_BUILD_MARKER-.next/BUILD_ID}"

cd "$DIR" || exit 1

# Someone else's server on the port is the most common way a run starts against the
# wrong build without anyone noticing.
if (netstat -ano 2>/dev/null || ss -ltn 2>/dev/null) | grep -E "[:.]$PORT[^0-9]" >/dev/null; then
    echo "PORT_TAKEN: port $PORT is in use; ask the user before restarting their server"
    exit 2
fi

if [ -n "$BUILD_MARKER" ] && [ -f "$BUILD_MARKER" ]; then
    echo "BUILD_PRESENT: $BUILD_MARKER exists; a production build breaks dev routes. Ask the user."
    exit 3
fi

: > "$LOG"
# shellcheck disable=SC2086
$CMD < /dev/null >> "$LOG" 2>&1 &
SERVER=$!

for _ in $(seq 1 90); do
    code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH" || true)
    if [ "$code" = "200" ]; then echo "READY pid=$SERVER log=$LOG"; break; fi
    if ! kill -0 "$SERVER" 2>/dev/null; then echo "SERVER_EXITED, see $LOG"; exit 1; fi
    sleep 2
done

wait "$SERVER"
