# Roadmap

## Remaining component monitoring coverage

Verified against current master — these have no ServiceMonitor/PodMonitor and
no chart metrics flag enabled:

- **cert-manager** — highest value; certificate expiry is the usual reason to
  want this at all
- keel, reflector — operators/agents, lower value

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

## Local log retention

A local, short-retention log destination — so logs are queryable for
debugging even without the remote endpoint configured — would need its own
internal object store plus a decision on the admin-facing UX

## Testing

- No Molecule scenario covers Sealed Secrets backup/restore
