# Ansible Collection - pokerops.rke2

[![Build Status](https://github.com/pokerops/ansible-collection-rke2/actions/workflows/molecule.yml/badge.svg)](https://github.com/pokerops/ansible-collection-rke2/actions/wofklows/molecule.yml)
[![Ansible Galaxy](http://img.shields.io/badge/ansible--galaxy-pokerops.rke2-blue.svg)](https://galaxy.ansible.com/ui/repo/published/pokerops/rke2/)

An opinionated [ansible collection](https://galaxy.ansible.com/ui/repo/published/pokerops/rke2/) to install and manage rke2 clusters matching standard components:

- [MetalLB](https://metallb.universe.tf/)
- [Longhorn](https://longhorn.io/)
- [CertManager](https://cert-manager.io/docs/)
- [Ingress Nginx](https://kubernetes.github.io/ingress-nginx/)
- [Traefik Ingress](https://doc.traefik.io/traefik/reference/install-configuration/providers/kubernetes/kubernetes-ingress/)
- [ArgoCD](https://argo-cd.readthedocs.io/en/stable/)
- [KSM](https://github.com/kubernetes/kube-state-metrics)
- [Vector](https://vector.dev/)
- [VictoriaLogs](https://github.com/VictoriaMetrics/VictoriaLogs)

Default installation uses [ArgoCD Applications](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/) to deploy and manage the following components:

- [Keel](https://keel.sh/)
- [Kubernetes Reflector](https://github.com/emberstack/kubernetes-reflector)
- [SeaweedFS Operator](https://github.com/seaweedfs/seaweedfs-operator)
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
- [Strimzi Operator](https://strimzi.io/)
- [Velero](https://velero.io/)
- [Zalando Postgres Operator](https://github.com/zalando/postgres-operator)
- [Kube State Metrics](https://github.com/kubernetes/kube-state-metrics)
- [Grafana Alloy Operator](https://github.com/grafana/alloy-operator)
- [SeaweedFS Operator](https://github.com/seaweedfs/seaweedfs-operator)

## Collection Variables

The following is the list of parameters intended for end-user manipulation:

Cluster wide parameters

| Parameter                                 |                            Default | Type   | Description                                                                                                      | Required |
| :---------------------------------------- | ---------------------------------: | :----- | :--------------------------------------------------------------------------------------------------------------- | :------- |
| rke2_cluster_name                         |                                n/a | string | Cluster name, immutable after creation                                                                           | yes      |
| rke2_version                              |                     v1.33.9+rke2r1 | string | RKE2 version to deploy                                                                                           | no       |
| rke2_nolog                                |                               true | bool   | Toggle flag for logging sensitive statements                                                                     | no       |
| rke2_config_hostnames                     |                               true | bool   | Toggle flag for cluster hostfile entry configuration                                                             | no       |
| rke2_retry_num                            |                                 10 | bool   | Max number of task retries                                                                                       | no       |
| rke2_retry_delay                          |                                 30 | bool   | Task delay on retries                                                                                            | no       |
| rke2_logging_format                       |                               json | string | Log format of the Kubernetes components and metrics-server; "" for their default                                 | no       |
| rke2_logging_volume_size                  |                                    | string | Log format of the Kubernetes components and metrics-server; "" for their default                                 | no       |
| rke2_logging_endpoint                     |                                    | string | Optional remote log destination (host:port); logs always go to the local store too                               | no       |
| rke2_logging_buffer_size                  |                         1073741824 | int    | Per-node disk buffer (bytes) for unsent remote logs; survives agent restarts                                     | no       |
| rke2_logging_retention_days               |                                  3 | int    | Days the local log store (VictoriaLogs) keeps logs; the oldest go first past 85% disk use                        | no       |
| rke2_logging_volume_size                  |                                5Gi | string | Local log store volume size                                                                                      | no       |
| rke2_logging_storage_class                |                                    | string | Local log store storage class; empty uses the cluster default                                                    | no       |
| rke2_kubevip_address                      |                                 "" | string | Control plane floating IP held by kube-vip (L2/ARP); "" disables kube-vip                                        | no       |
| rke2_evict_timeout                        |                                300 | bool   | Node drain eviction timeout in seconds                                                                           | no       |
| rke2_ippool_private                       |                                n/a | string | Private IP pool CIDR                                                                                             | yes      |
| rke2_ippool_public                        |                                n/a | string | Public IP pool CIDR                                                                                              | no       |
| rke2_certmanager_issuer_name              |                     cluster-issuer | string | Name of the cert-manager cluster issuer                                                                          | no       |
| rke2_certmanager_acme_secret              |                                n/a | string | Secret name for ACME challenge                                                                                   | no       |
| rke2_certmanager_acme_email               |                                n/a | string | Email for ACME challenge                                                                                         | no [1]   |
| rke2_argocd_hostname                      |   "argocd.{{ rke2_cluster_name }}" | string | ArgoCD hostname                                                                                                  | no       |
| rke2_argocd_values                        |                         object [2] | dict   | Helm chart values for ArgoCD chart                                                                               | no       |
| rke2_argocd_apps_deploy                   |                               true | dict   | Toggle flag for ArgoCD Applications chart deployment                                                             | no       |
| rke2_argocd_apps_values                   |                                n/a | dict   | Helm chart values for ArgoCD Applications chart                                                                  | no       |
| rke2_argocd_values_configs                |                                 {} | dict   | ArgoCD configs, override for default ArgoCD chart values                                                         | no       |
| rke2_argocd_values_notifications          |                                 {} | dict   | ArgoCD notifications, override for default ArgoCD chart values                                                   | no       |
| rke2_argocd_exec_timeout                  |                                 3m | string | ArgoCD exec timeout, override for default ArgoCD chart values                                                    | no       |
| rke2_argocd_redis_ha_enabled              |                               true | bool   | ArgoCD Redis HA toggle, override for default ArgoCD chart values                                                 | no       |
| rke2_argocd_controller_replicas           |                                  2 | int    | ArgoCD controller replicas, override for default ArgoCD chart values                                             | no       |
| rke2_argocd_server_replicas               |                                  2 | int    | ArgoCD server replicas, override for default ArgoCD chart values                                                 | no       |
| rke2_argocd_reposerver_replicas           |                                  2 | int    | ArgoCD repo server replicas, override for default ArgoCD chart values                                            | no       |
| rke2_argocd_applicationset_replicas       |                                  2 | int    | ArgoCD applicationset replicas, override for default ArgoCD chart values                                         | no       |
| rke2_argocd_apps_pokerops_revision        |                               HEAD | string | PokerOps ArgoCD revision, used to deploy base cluster assets                                                     | no       |
| rke2_longhorn_hostname                    | "longhorn.{{ rke2_cluster_name }}" | string | Longhorn UI hostname                                                                                             | no       |
| rke2_monitoring_endpoint                  |                                    | string | Remote ingestor URL; setting it enables monitoring                                                               | no       |
| rke2_monitoring_cluster_id                |            {{ rke2_cluster_name }} | string | Cluster label stamped on every metric and log record                                                             | no       |
| rke2_monitoring_tls_enabled               |                              false | bool   | Use mTLS to reach the remote ingestor                                                                            | no       |
| rke2_monitoring_vector_memory             |                                1Gi | string | Memory limit for Vector.dev                                                                                      |
| rke2_monitoring_vector_image              |      timberio/vector:0.48.0-debian | string | Vector agent image; the debian variant carries journalctl for node journal logs. Pinned, bumped by `rke2 update` | no       |
| rke2_coredns_cpu_limit                    |                               500m | string | CoreDNS per-pod CPU limit, override for default rke2-coredns chart values                                        | no       |
| rke2_coredns_memory_limit                 |                              512Mi | string | CoreDNS per-pod memory limit, override for default rke2-coredns chart values                                     | no       |
| rke2_coredns_autoscaler_cores_per_replica |                                128 | int    | Cluster cores per CoreDNS replica, override for default rke2-coredns autoscaler                                  | no       |
| rke2_coredns_autoscaler_nodes_per_replica |                                  8 | int    | Cluster nodes per CoreDNS replica, override for default rke2-coredns autoscaler                                  | no       |
| rke2_coredns_autoscaler_min_replicas      |                                  2 | int    | Minimum CoreDNS replicas, override for default rke2-coredns autoscaler                                           | no       |
| rke2_nolog                                |                               true | bool   | Toggle flag for logging sensitive statements                                                                     | no       |

[1] rke2_certmanager_acme_email is required whenever rke2_certmanager_acme_secret is set
[2] rke2_argocd_values default is as follows:

Velero S3 backup parameters

| Parameter         | Default | Type   | Description                            | Required |
| :---------------- | ------: | :----- | :------------------------------------- | :------- |
| rke2_cluster_name |     n/a | string | Cluster name, immutable after creation | yes      |

```yaml
redis-ha:
  enabled: true
controller:
  replicas: 2
server:
  replicas: 2
  ingress:
    enabled: true
    https: true
    ingressClassName: traefik-private
    hostname: "argocd.{{ rke2_cluster_name }}"
    annotations:
      nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
repoServer:
  replicas: 2
applicationSet:
  replicas: 2
configs:
  params:
    application.namespaces: "*"
    applicationsetcontroller.namespaces: "*"
global:
  env:
    - name: ARGOCD_EXEC_TIMEOUT
      value: 3m
```

## Collection roles

- pokerops.rke2.components
- [pokerops.rke2.rke2](https://github.com/lablabs/ansible-role-rke2)

## Collection playbooks

- pokerops.rke2.install: Install and (re)configure cluster
- pokerops.rke2.deploy: Deploy individual cluster components
- pokerops.rke2.secrets: Deploy cluster secrets
- pokerops.rke2.init: Deploy base cluster components
- pokerops.rke2.update: Update OS for rke2 cluster members
- pokerops.rke2.frr: Run an FRR BGP router for MetalLB peers on a test host (see below)

## Local logs

Every node's pod and node logs (kubelet, containerd, rke2) also go to a
cluster-local VictoriaLogs store in the `monitoring` namespace, kept for
`rke2_logging_retention_days`, for troubleshooting when the remote endpoint is
unreachable or not set. It has no Ingress, and its NetworkPolicy admits only the
log agents and Alloy; reach it through a port-forward:

```sh
kubectl -n monitoring port-forward svc/victoria-logs 9428:9428
```

Then open <http://localhost:9428/select/vmui/> for the web UI (from this
repository, `just logs` does both: it forwards and opens the browser), or query
[LogsQL](https://docs.victoriametrics.com/victorialogs/logsql/) directly:

```sh
# Errors from every pod in the last hour, by namespace
curl -s localhost:9428/select/logsql/query \
  --data-urlencode 'query=_time:1h level:error | stats by (kubernetes.pod_namespace) count()'
# One node's kubelet log, newest last
curl -s localhost:9428/select/logsql/query \
  --data-urlencode 'query=_time:30m node:="my-node" unit:="kubelet" | sort by (_time)'
# Follow a namespace live
curl -sN localhost:9428/select/logsql/tail \
  --data-urlencode 'query=kubernetes.pod_namespace:="argocd"'
```

Fields are the pipeline's normalized ones (`node`, `unit`, `level`, `msg`,
`log.*`, `kubernetes.*`). Anyone with cluster-admin can alter this store; it is
for speed, not a record of evidence.

## FRR test router

`pokerops.rke2.frr` runs [FRR](https://frrouting.org/) in a Docker container on the host
running your test environment (`localhost` unless `rke2_frr_host` is set). It accepts BGP
sessions from every address on the test network, so MetalLB speakers on the cluster members
peer with it and LoadBalancer addresses become routes on that host. It is the router this
collection's own `converged` and `full` scenarios test against. It does nothing unless
`rke2_metallb_mode` is `bgp`.

Import it before `pokerops.rke2.install`, and again with `rke2_frr_state: absent` on teardown:

```yaml
- name: Configure FRR router
  import_playbook: pokerops.rke2.frr
```

```yaml
- name: Destroy FRR router
  import_playbook: pokerops.rke2.frr
  vars:
    rke2_frr_state: absent
```

| Parameter               |                      Default | Type   | Description                                                    | Required |
| :---------------------- | ---------------------------: | :----- | :------------------------------------------------------------- | :------- |
| rke2_frr_address        |              libvirt_address | string | Host address CIDR on the network cluster members peer over     | yes [3]  |
| rke2_frr_asn            |         rke2_metallb_bgp_asn | int    | ASN shared with MetalLB peers (iBGP)                           | yes [3]  |
| rke2_frr_state          |                      present | string | `present` to deploy, `absent` to remove container and config   | no       |
| rke2_frr_host           |                    localhost | string | Inventory host that runs the router                            | no       |
| rke2_frr_group          | rke2_agent, else rke2_server | string | Group whose hosts the router balances routes over (ECMP paths) | no       |
| rke2_frr_version        |                       10.5.3 | string | FRR image tag                                                  | no       |
| rke2_frr_image          |        quay.io/frrouting/frr | string | FRR image repository                                           | no       |
| rke2_frr_container      |                          frr | string | Container name                                                 | no       |
| rke2_frr_config_dir     |            /var/lib/rke2-frr | string | Host directory mounted as the container's `/etc/frr`           | no       |
| rke2_frr_install_docker |                         true | bool   | Install and start `docker.io` first (apt based hosts)          | no       |

[3] Not required when the default is defined

Cluster members must be able to reach `rke2_frr_address`, and the collection
`community.docker` must be installed on the controller.

## Testing

You can test the collection directly from sources using command `just test`

Role releases are ci/cd tested against the following distributions:

- Ubuntu Noble
- Ubuntu Jammy

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit)
