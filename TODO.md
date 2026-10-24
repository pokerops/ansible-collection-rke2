# Roadmap

## Monitoring

These have no ServiceMonitor/PodMonitor and no chart metrics flag enabled:

- **cert-manager** — highest value; certificate expiry is the usual reason to
  want this at all
- keel, reflector — operators/agents, lower value

## Logging

Text only at the pinned versions (the remap still parses their level and
message):

- argocd's **redis** (no JSON option)
- **reflector** (JSON breaks on exceptions; see `argocd/applications/reflector.yml`).
- **seaweedfs-operator** (no JSON logging support from operator chart)
- **strimzi-operator** (incomplete support, see `argocd/applications/strimzi.yml`)
- metallb's **frr** and **reloader** (no JSON option)
- longhorn's **instance-manager** (logfmt formatter hardcoded in
  longhorn-instance-manager; its tgtd lines carry no level)

## Traffic visibility

Add access logs for the following traffic flows

- Ingress
- DNS queries
- HTTP queries
- HTTPS queries

## Deprecations

- Drop longhorn deprecated endpoints transform from `playbooks/templates/vector/pipeline.j2.yml`
  once Longhorn v1.14.0 lands in the repository and the deprecation fixes have been verified
  to ship in that release

## Security

- Implement an optional registration mechanism for clusters configured by the collection
- Implement an optional secure access mechanisms for clusters and

## Testing

- Add molecule scenario for Sealed Secrets backup and restore
