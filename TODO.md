# Roadmap

## Logging

Metrics have a shipping pipeline end to end; logs do not, despite the test
scaffolding being built for both:

- `argocd/applications/vector.yml` deploys the **vector-operator** controller
  to every cluster already — this part is live in production
- no `Vector` / `VectorPipeline` custom resource has ever been committed, so
  the operator has nothing to reconcile and ships nothing
- `molecule/common/ingestor.yml` already declares a `logs_in` vector source
  (port 8989) and a `logs_file` sink (`/data/logs.log`) alongside the metrics
  ones — built to receive logs, never exercised by anything
- no verify playbook anywhere asserts `logs.log` receives a line
- no `rke2_logging_endpoint`-equivalent var exists to configure where a
  pipeline would ship, unlike `rke2_monitoring_endpoint` for metrics

The stale `origin/vector` branch (2026-08-28, 7 commits behind master) is not
this feature waiting to be revived — its `playbooks/templates/vector.yml` is
an earlier draft of deploying the _operator itself_, applied directly via an
ansible task rather than through the argocd app-of-apps glob. That approach
was superseded by what actually shipped to master, so the branch predates the
real gap rather than closing it. Safe to delete once this is scoped.

The shape of the fix mirrors the metrics path closely enough to reuse: a
`VectorPipeline` CR analogous to `strimzi/kafka-metrics.yml`, an
`rke2_logging_endpoint` var, and a verify assertion against `logs.log`
modeled on the existing `kube_*_created` checks.

## Remaining component monitoring coverage

Verified against current master — these have no ServiceMonitor/PodMonitor and
no chart metrics flag enabled:

- **cert-manager** — highest value; certificate expiry is the usual reason to
  want this at all
- **seaweedfs** — the Velero backup target since #93
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
entirely? That decision shapes everything else here.
