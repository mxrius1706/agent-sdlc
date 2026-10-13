#!/usr/bin/env bash
# Filter the dev server log for the handlauf skill: one line per event worth looking at.
# Meant as the command of a Monitor, where each stdout line becomes a notification.
#
# Usage:  bash <handlauf skill dir>/scripts/watch-dev-log.sh <logfile>
#
# Emits:
#   LOG  <level line> <message line>  structured logger objects at level error or warn
#                                     (loggers print them over several lines, with the
#                                     message following the level)
#   HTTP <line>                       requests answered with 4xx or 5xx
#   ERR  <line>                       uncaught errors, framework error markers, missing
#                                     environment variables at start
#
# Extend HL_ERR_PATTERN with the markers from the handlauf / dev server row in
# "Project references" (database client errors, a bundler's failure line) rather
# than editing the awk below:
#
#   HL_ERR_PATTERN='PrismaClient|SequelizeError'
LOG="${1:?usage: watch-dev-log.sh <logfile>}"

BASE='⨯|Uncaught|Unhandled|TypeError|ReferenceError|MISSING REQUIRED|Error \[|\[browser\]'
PATTERN="${HL_ERR_PATTERN:+$BASE|$HL_ERR_PATTERN}"
PATTERN="${PATTERN:-$BASE}"

tail -n 0 -F "$LOG" 2>/dev/null | awk -v errpat="$PATTERN" '
    /level: .(error|warn)./ { pending = 4; level = $0; next }
    pending > 0 {
        pending--
        if ($0 ~ /message:/) { print "LOG " level " " $0; fflush(); pending = 0 }
        next
    }
    / [45][0-9][0-9] in [0-9]/ { print "HTTP " $0; fflush(); next }
    $0 ~ errpat { print "ERR " $0; fflush() }
'
