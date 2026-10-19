# Roadmap

## Monitoring

These have no ServiceMonitor/PodMonitor and no chart metrics flag enabled:

- **cert-manager** — highest value; certificate expiry is the usual reason to
  want this at all
- keel, reflector — operators/agents, lower value

## Logging

Move supporting components to json logs. Options below were verified against
each pinned chart version's values/templates and the component's source.

- **argocd** — `global.logging.format: json` in `rke2_argocd_values`; covers
  server, controller, repo-server, applicationset, notifications and dex
  (redis has no json option)
- **cert-manager** — `config.logging.format`, `webhook.config.logging.format`
  and `cainjector.config.logging.format: json` (`roles/components/tasks/certmanager.yml`)
- **traefik** — `log.format: json` (`playbooks/templates/traefik.yml`); also
  drops the ANSI color codes. Access logs: `accessLog.format: json`
- **velero** — `configuration.logFormat: json`; covers velero and node-agent
- **sealed-secrets** — `logFormat: json`
- **postgres-operator** — `enableJsonLogging: true`; the postgres-exporter
  sidecar takes `args: ["--log.format=json"]` in `configGeneral.sidecars`
- **alloy** — `logging { format = "json" }` block in the config
  (`playbooks/templates/alloy.yml`); its config-reloader sidecar needs
  `spec.configReloader.customArgs` restating `--watched-dir=/etc/alloy` and
  `--reload-url=http://localhost:12345/-/reload` plus `--log-format=json`
  (customArgs replaces the defaults)
- **vector agent** — `spec.agent.env: VECTOR_LOG_FORMAT=json`
  (`playbooks/templates/vector.j2.yml`)
- **vector-operator** — chart `args: [--zap-encoder=json]`
- **seaweedfs-logs** — env `WEED_LOG_JSON=true` on master/filer/volume in
  `playbooks/templates/seaweedfs-logs/cluster.yml` (`extraArgs` lands after
  the subcommand, too late for this global flag). The host `weed mount`
  takes the same `-log_json`
- **strimzi** — chart `logConfiguration` with a full log4j2.properties using
  `JsonTemplateLayout`; operator only, Kafka clusters set their own logging

## SeaweedFS mount write cost

Upstream bug, not yet reported - **file a SeaweedFS issue** (with the
benchmark below) before working around it further.

`weed mount` (4.48, unchanged on master) keeps one
`page_writer.ChunkWrittenInterval` per write in each 2 MB chunk, never
merges adjacent ones, and walks the whole list twice per write
(`addInterval`, then `IsComplete` via `maybeMoveToSealed`). Vector's file
sink does one write per log line, so each write costs O(writes already in
the chunk). Profiled live: ~80% of weed's CPU in those two functions; a
busy agent node spends 7-17% steady, and log bursts outgrow any fixed CPU
share (`weed-mount.service.j2` now uses `CPUWeight`, not `CPUQuota`, so
it slows down instead of freezing).

- Benchmark: one held-open fd on the mount, 1000 appends of ~145 bytes.
  Default mount: 65.7s wall. With `-writebackCache`: 0.23s.
- `-writebackCache` is not usable here: lines in a file still held open
  aren't visible from other nodes until it's closed (measured: nothing in
  110s of appends, all of it right after close), and Vector keeps busy
  files open all day.
- Upstream fix shape: scan from the tail for appends (O(1) for sequential
  writes) and track coverage incrementally instead of walking in
  `IsComplete`.

## Deprecations

- `playbooks/templates/vector-pipeline.j2.yml` drops longhorn-manager's
  "v1 Endpoints is deprecated" warning (the `k8s_logs_filtered` transform),
  because Longhorn calls the deprecated API from its own code. Upstream fix:
  longhorn/longhorn#10796, planned for **Longhorn v1.14.0**. Once the Longhorn
  chart pin in `playbooks/templates/longhorn.yml` reaches v1.14.0 and the
  warning is confirmed gone from longhorn-manager's own logs, delete the
  transform and point the sinks back at `k8s_logs`.

## Alerting

Architectural gap, not just missing files — the pieces currently contradict
each other:

- `prometheus-crds.yml` enables the `prometheusrules` CRD
- nothing in `alloy.yml` reads it — no `mimir.rules.kubernetes` /
  `loki.rules.kubernetes` component, so any PrometheusRule created would sit
  inert
- no in-cluster Prometheus server/ruler; alloy only `remote_write`s to
  `rke2_monitoring_endpoint`
- `alertmanagers` / `alertmanagerconfigs` CRDs are explicitly disabled

All three monitor-optional exemptions (`strimzi/monitors.yml`,
`zalando/monitors.yml`, and mariadb's operator-created monitor) justify
themselves by pointing at "alerting on the `kube_*_created` series." That
series is now verified to arrive in all three scenarios — the missing piece
is a consumer for it.

**Needs a decision before any code:** do rules ship to the remote tenant's
ruler via alloy (`mimir.rules.kubernetes`), or get evaluated somewhere else
entirely? That decision gates the actual task — alerting when a
`pokerops.net/monitor-optional` cluster exists but emits no `kube_*_created`
series.
