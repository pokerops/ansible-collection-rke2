# pokerops.rke2.components

Standard cluster components for RKE2 clusters.

## Role Variables

| Parameter                                  |                        Default | Type   | Description                                                                                                                                                                                                                    | Required |
| :----------------------------------------- | -----------------------------: | :----- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------- |
| rke2_argocd_hostname                       | argocd.{{ rke2_cluster_name }} | string | Argocd URL                                                                                                                                                                                                                     | no       |
| rke2_certmanager_issuer_name               |                 cluster-issuer | string | Name of the cert-manager cluster issuer                                                                                                                                                                                        | no       |
| rke2_monitoring_endpoint                   |                                | string | Remote ingestor URL; setting it enables monitoring                                                                                                                                                                             | no       |
| rke2_logging_endpoint                      |                                | string | Remote ingestor host:port; setting it enables logging                                                                                                                                                                          | no       |
| rke2_logging_buffer_size                   |                     1073741824 | int    | Per-node disk buffer (bytes) for unsent remote logs; survives agent restarts                                                                                                                                                   | no       |
| rke2_monitoring_cluster_id                 |        {{ rke2_cluster_name }} | string | Cluster label stamped on every metric and log record                                                                                                                                                                           | no       |
| rke2_monitoring_tls_enabled                |                          false | bool   | Use mTLS to reach the remote ingestor                                                                                                                                                                                          | no       |
| rke2_vector_agent_image                    |  timberio/vector:0.48.0-debian | string | Vector agent image; the debian variant carries journalctl for node journal logs. Pinned, bumped by `rke2 update`                                                                                                               | no       |

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit)
