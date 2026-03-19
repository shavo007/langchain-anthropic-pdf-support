#!/usr/bin/env bash
# fetch_merged_prs.sh — Fetch PRs merged in the last N days (default: 7)
# Usage: ./fetch_merged_prs.sh [days] [--repo owner/repo]
#
# Outputs JSON array of merged PRs with: number, title, author, mergedAt, url, labels, body
# Requires: gh CLI authenticated

set -euo pipefail

DAYS="${1:-7}"
REPO_FLAG=""

# Parse optional --repo flag
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO_FLAG="--repo $2"; shift 2 ;;
    --days) DAYS="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# Compute cutoff date (works on both macOS and Linux)
if date --version &>/dev/null 2>&1; then
  # GNU date (Linux)
  SINCE=$(date -d "-${DAYS} days" --iso-8601=seconds)
else
  # BSD date (macOS)
  SINCE=$(date -v-"${DAYS}"d -u +"%Y-%m-%dT%H:%M:%SZ")
fi

echo "Fetching PRs merged since: $SINCE" >&2

gh pr list \
  $REPO_FLAG \
  --state merged \
  --limit 100 \
  --json number,title,author,mergedAt,url,labels,body \
  --jq "[.[] | select(.mergedAt >= \"$SINCE\")]"
