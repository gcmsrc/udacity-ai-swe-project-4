#!/usr/bin/env bash

ENV_FILE="$(dirname "$0")/../.env"
if [ -f "$ENV_FILE" ]; then
    # shellcheck source=/dev/null
    source "$ENV_FILE"
fi

if [ -z "${TRACE_FILE:-}" ]; then
    echo "TRACE_FILE not set in .env" >&2
    exit 1
fi

# Read transcript_path from stdin JSON provided by the Stop hook
TRANSCRIPT_PATH=$(jq -r '.transcript_path // empty')

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0
fi

# Wait for the assistant text entry to be flushed to disk (Stop hook fires before JSONL write)
MAX_WAIT=5
WAITED=0
while [ "$WAITED" -lt "$MAX_WAIT" ]; do
    HAS_TEXT=$(jq -rs '[.[] | select(.type == "assistant")] | last | .message.content | map(select(.type == "text")) | length' "$TRANSCRIPT_PATH" 2>/dev/null)
    [ "${HAS_TEXT:-0}" -gt 0 ] && break
    sleep 1
    WAITED=$((WAITED + 1))
done

# Slurp JSONL into array, extract last human user message text
# Tool results are also stored as type=="user" but with array content; filter them out
LAST_USER=$(jq -rs \
    '[.[] | select(.type == "user") | select((.message.content | type) == "string") | select(.message.content | length > 0)] | last |
     .message.content' \
    "$TRANSCRIPT_PATH" 2>/dev/null)

# Extract last assistant message text
LAST_ASSISTANT=$(jq -rs \
    '[.[] | select(.type == "assistant")] | last |
     .message.content |
     if type == "array" then map(select(.type == "text") | .text) | join("\n")
     else . end' \
    "$TRANSCRIPT_PATH" 2>/dev/null)

if [ -z "$LAST_USER" ] && [ -z "$LAST_ASSISTANT" ]; then
    exit 0
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
SESSION_SHA=$(basename "$TRANSCRIPT_PATH" .jsonl | cut -c1-8)

{
    printf "\n\n"
    printf "## Session: %s [%s]\n\n" "$TIMESTAMP" "$SESSION_SHA"
    printf "**User Request:**\n\n%s\n\n" "$LAST_USER"
    printf "**Claude Response:**\n\n%s\n" "$LAST_ASSISTANT"
} >> "$TRACE_FILE"
