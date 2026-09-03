#!/bin/sh
set -eu

policy=/policy/specvora-egress.nft
if [ ! -r "$policy" ]; then
  echo "Specvora egress policy is required" >&2
  exit 78
fi

nft --check --file "$policy"
nft --file "$policy"

exec setpriv \
  --reuid=nobody \
  --regid=nogroup \
  --clear-groups \
  --no-new-privs \
  --bounding-set=-all \
  -- "$@"
