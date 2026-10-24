# Project instructions

## Logging invariant

Every component this collection deploys logs JSON where it can, and every
shipped log event carries the common fields. When you add a component, or
bump one to a version that may have changed its logging:

1. **Probe for JSON logging support** against the pinned version: the chart's
   values.yaml and templates at that exact version, plus the component's own
   flags/env/config in its source at the matching tag. Don't rely on
   memory or the latest docs - options differ between versions.
2. **Enable it** when supported, in the same change that adds the component.
   If it isn't supported (or only partly), say so in a comment next to the
   component's config so the next person doesn't re-probe it.
3. **Check its events are normalized.** `logs_normalized` in
   `playbooks/templates/vector/pipeline.j2.yml` sets, on every event shipped
   to the remote sink and the cluster-local VictoriaLogs store:
   - `node`: the node the event came from
   - `log_format`: `json`, `klog`, `logfmt` or `text`
   - `level`: `trace`, `debug`, `info`, `warn`, `error`, `fatal` or `unknown`
   - `msg`: the line's own message, else the raw line
   - `log`: every parsed field, under its own key
   - `timestamp` and `kubernetes.*` (pod logs) are already set by the
     source; `.message` stays the raw line

   A `text` line still gets a real `level` and `msg` when its format is
   leveled text the remap knows (zap console, a level token after a
   timestamp, coredns's `[LEVEL]`); that is the fallback for components
   whose JSON logging can't be enabled, not a substitute for enabling it.

   Node logs (outside any pod) also carry `unit`: the systemd unit without
   `.service`, or the log file's name without `.log` (`kubelet`,
   `containerd`). Plain-text journal lines fall back to the unit's syslog
   priority for `level`.

   Run the `monitoring` scenario and confirm the new component's events get
   a real `level` and `msg`, not `unknown` and the raw line. If its level or
   message use keys the remap doesn't know yet, extend the remap.

4. **Ship host-level logs too.** A systemd unit this collection installs on
   the nodes goes in the pipeline's `node_journal` `include_units`; a log
   file written outside the journal and outside any pod (as rke2 does for
   the kubelet and containerd) goes in `node_files`, with its directory
   mounted read-only into the agent in `playbooks/templates/vector/agent.j2.yml`.
   Generic host logs (kernel, sshd, the rest of the journal) belong to the
   host OS collection, not this one.

`molecule/common/verify/monitoring.yml` asserts that every recent event at
the test ingestor carries `node`, `log_format`, `level` and `msg`, and that
kubelet and rke2 logs arrive from every node, at the ingestor and in the
local store. Components that
support JSON but don't have it enabled yet are listed under "Logging" in
`TODO.md`.
