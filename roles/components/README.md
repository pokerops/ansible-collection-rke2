# pokerops.rke2.components

Standard cluster components for RKE2 clusters.

## Role Variables

| Parameter                                  |                        Default | Type   | Description                                                                                                                                                                                                                    | Required |
| :----------------------------------------- | -----------------------------: | :----- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------- |
| rke2_argocd_hostname                       | argocd.{{ rke2_cluster_name }} | string | Argocd URL                                                                                                                                                                                                                     | no       |
| rke2_certmanager_issuer_name               |                 cluster-issuer | string | Name of the cert-manager cluster issuer                                                                                                                                                                                        | no       |
| rke2_monitoring_endpoint                   |                                | string | Remote ingestor URL; setting it enables monitoring                                                                                                                                                                             | no       |
| rke2_logging_endpoint                      |                                | string | Optional remote log destination (host:port); logs always go to the local store too                                                                                                                                             | no       |
| rke2_logging_buffer_size                   |                     1073741824 | int    | Per-node disk buffer (bytes) for unsent remote logs; survives agent restarts                                                                                                                                                   | no       |
| rke2_logging_retention_days                |                              3 | int    | Days the local log store (VictoriaLogs) keeps logs; the oldest go first past 85% disk use                                                                                                                                      | no       |
| rke2_logging_volume_size                   |                            5Gi | string | Local log store volume size                                                                                                                                                                                                    | no       |
| rke2_logging_storage_class                 |                                | string | Local log store storage class; empty uses the cluster default                                                                                                                                                                  | no       |
| rke2_monitoring_cluster_id                 |        {{ rke2_cluster_name }} | string | Cluster label stamped on every metric and log record                                                                                                                                                                           | no       |
| rke2_monitoring_tls_enabled                |                          false | bool   | Use mTLS to reach the remote ingestor                                                                                                                                                                                          | no       |
| rke2_vector_agent_image                    |  timberio/vector:0.48.0-debian | string | Vector agent image; the debian variant carries journalctl for node journal logs. Pinned, bumped by `rke2 update`                                                                                                               | no       |

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


## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit)
