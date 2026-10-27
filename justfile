set allow-duplicate-variables := true

import '.devbox/virtenv/pokerops.ansible-utils.molecule/justfile'

MOLECULE_REVISION_DEFAULT := `command git rev-parse --abbrev-ref HEAD`
MOLECULE_SCENARIO_DEFAULT := 'components'
MOLECULE_REVISION := env('MOLECULE_REVISION', MOLECULE_REVISION_DEFAULT)
MOLECULE_SCENARIO := env('MOLECULE_SCENARIO', MOLECULE_SCENARIO_DEFAULT)

CLOUDFLARE_IPS_URL := 'https://api.cloudflare.com/client/v4/ips'
CLOUDFLARE_IPS_FILE := 'roles/components/defaults/main/cloudflare.yml'

build-check: requirements && version-check
  ${UV} --directory . run rke2 build --check

# Sync argocd app revision with the galaxy.yml collection version
build-fix:
  ${UV} --directory . run rke2 build

update:
  ${UV} --directory . run rke2 update

# Run the collection's unit tests (tests/unit: filter plugins); extra args go to pytest
pytest *args:
  ${UV_RUN} pytest {{ args }}

# Forward the cluster-local VictoriaLogs store and open its web UI (Ctrl-C stops)
logs port="9428":
  #!/usr/bin/env bash
  set -euo pipefail
  # $KUBECONFIG, else the molecule scenario's .kubeconfig, else kubectl's default
  if ! [ -f .kubeconfig ]; then
    echo "Could not find project kubeconfig"
    exit 1
  fi
  _url="http://localhost:{{ port }}/select/vmui/"
  KUBECONFIG=.kubeconfig kubectl -n monitoring port-forward svc/victoria-logs '{{ port }}:9428' &
  _forward=$!
  trap 'kill "$_forward" 2>/dev/null || true' EXIT INT TERM
  for _ in $(seq 1 40); do
    curl -fsS --max-time 1 "http://localhost:{{ port }}/health" >/dev/null 2>&1 && break
    kill -0 "$_forward" 2>/dev/null || { echo "port-forward to victoria-logs failed" >&2; exit 1; }
    sleep 0.25
  done
  echo "VictoriaLogs at $_url (Ctrl-C to stop)"
  if command -v xdg-open >/dev/null; then
    xdg-open "$_url" >/dev/null 2>&1 || true
  elif command -v open >/dev/null; then
    open "$_url" || true
  fi
  wait "$_forward"

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
