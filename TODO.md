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
  drops the ANSI color codes. Access logs: see "Traffic visibility" below
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
  (`playbooks/templates/vector/agent.j2.yml`)
- **vector-operator** — chart `args: [--zap-encoder=json]`
- **strimzi** — chart `logConfiguration` with a full log4j2.properties using
  `JsonTemplateLayout`; operator only, Kafka clusters set their own logging

### Traffic visibility

For incident response: who talked to what. Today neither sink records DNS
queries or HTTP requests. CoreDNS's Corefile has `errors` but no `log`, and
Hubble keeps flows in the agents' memory only (no `hubble-export-*` in
`cilium-config`, no L7 policy, so DNS and HTTP aren't parsed).

1. **Ingress access logs** — cheapest; covers all north-south HTTP with
   client IP, host, path, status and backend service.
   - traefik: access logs are off by default (chart 41.5.0); needs
     `accessLog.enabled: true` as well as `accessLog.format: json`
   - ingress-nginx: access logs are on, as text; JSON takes a `controller.config`
     `log-format-upstream` JSON template plus `log-format-escape-json: "true"`
2. **DNS query visibility** — answers "which pod resolved this domain".
   - CoreDNS `log . { class denial error }` (HelmChartConfig for
     `rke2-coredns`) is a cheap first step: NXDOMAIN and error answers only.
     Clients are pod IPs, which get reused, so attribution after the fact is
     weak; logging every query has the same problem and far more volume
   - Hubble DNS visibility attributes each query to its pod (namespace, name,
     labels): a cluster-wide CiliumClusterwideNetworkPolicy with a
     `rules.dns` `matchPattern: "*"` rule sends all DNS through Cilium's
     per-node DNS proxy, plus Hubble flow export (DNS events only) to a node
     file the vector agent mounts and ships. The proxy becomes a dependency of
     every pod's DNS; needs a design pass before code
3. **L7 HTTP inspection (opt-in, per service)** — same mechanism as Hubble
   DNS visibility, through Envoy: method, URL, status and latency with
   source and destination pods. Plaintext HTTP only (TLS stays opaque
   without TLS interception, not recommended). Rules name specific endpoints
   and ports, an L7 ingress rule default-denies the pod unless
   `enableDefaultDeny: false`, and Envoy adds latency and per-node resources.
   Use Hubble's redaction for URL query, user info and headers. Not
   cluster-wide; only for services where it's needed

## Deprecations

- `playbooks/templates/vector/pipeline.j2.yml` drops longhorn-manager's
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

## Testing

- No Molecule scenario covers Sealed Secrets backup/restore
