set allow-duplicate-variables := true

import '.devbox/virtenv/pokerops.ansible-utils.molecule/justfile'

MOLECULE_REVISION := `command git rev-parse --abbrev-ref HEAD`
MOLECULE_SCENARIO := 'components'

CLOUDFLARE_IPS_URL := 'https://api.cloudflare.com/client/v4/ips'
CLOUDFLARE_IPS_FILE := 'roles/components/defaults/main/cloudflare.yml'

build-check: requirements && version-check
  ${UV} --directory . run rke2 build --check

# Sync argocd app revision with the galaxy.yml collection version
build-fix:
  ${UV} --directory . run rke2 build

update:
  ${UV} --directory . run rke2 update

# Refresh cloudflare edge ip ranges from the cloudflare api
cloudflare-acl:
  #!/usr/bin/env bash
  set -euo pipefail
  _query='[.result.ipv4_cidrs[], .result.ipv6_cidrs[]]'
  _response="$(curl -fsS --max-time 30 '{{ CLOUDFLARE_IPS_URL }}')"
  if [ "$(printf '%s' "$_response" | jq -r '.success')" != "true" ]; then
    printf '%s' "$_response" | jq -r '.errors' >&2
    echo "cloudflare ip range request failed" >&2
    exit 1
  fi
  _count="$(printf '%s' "$_response" | jq -r "$_query | length")"
  if [ "$_count" -lt 1 ]; then
    echo "cloudflare returned no ip ranges, refusing to write {{ CLOUDFLARE_IPS_FILE }}" >&2
    exit 1
  fi
  printf '%s\n' \
    '---' \
    'rke2_cloudflare_ip_ranges:' > '{{ CLOUDFLARE_IPS_FILE }}'
  printf '%s' "$_response" | jq -r "$_query | sort | .[] | \"  - \" + ." >> '{{ CLOUDFLARE_IPS_FILE }}'
