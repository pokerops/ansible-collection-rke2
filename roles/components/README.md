# pokerops.rke2.components

Standard cluster components for RKE2 clusters.

## Role Variables

| Parameter                    |                        Default | Type   | Description                                        | Required |
| :--------------------------- | -----------------------------: | :----- | :------------------------------------------------- | :------- |
| rke2_argocd_hostname         | argocd.{{ rke2_cluster_name }} | string | Argocd URL                                         | no       |
| rke2_certmanager_issuer_name |                 cluster-issuer | string | Name of the cert-manager cluster issuer            | no       |
| rke2_monitoring_endpoint     |                                | string | Remote ingestor URL; setting it enables monitoring | no       |
| rke2_logging_endpoint        |                                | string | Remote ingestor host:port; setting it enables logging | no    |
| rke2_monitoring_cluster_id   |        {{ rke2_cluster_name }} | string | Cluster label stamped on every metric and log record | no     |
| rke2_monitoring_tls_enabled  |                          false | bool   | Use mTLS to reach the remote ingestor              | no       |
| rke2_logging_local_retention_deploy | false                   | bool   | Deploy a local SeaweedFS log store + POSIX mount; setting it enables logging even with no remote endpoint | no |
| rke2_seaweedfs_logs_namespace |                 seaweedfs-logs | string | Namespace for the local log retention SeaweedFS cluster | no   |
| rke2_seaweedfs_logs_version  |                            4.48 | string | SeaweedFS version for both the cluster image and the host `weed` binary | no |
| rke2_seaweedfs_logs_bucket   |                            logs | string | Bucket name backing the local log retention mount  | no       |
| rke2_seaweedfs_logs_storage_class |               seaweedfs-logs | string | Storage class for the local log retention volume   | no       |
| rke2_seaweedfs_logs_volume_size |                          4Gi | string | Volume size for the local log retention cluster    | no       |
| rke2_seaweedfs_logs_max_volume_count |                       7 | int    | Volume headroom for the bucket's collection; too low silently exhausts itself on other collections | no |
| rke2_seaweedfs_logs_retention_days |                         3 | int    | Days before a log file ages out (whole days only)  | no       |
| rke2_seaweedfs_logs_mount_path |              /var/log/cluster | string | Host path every node mounts the logs bucket at - agents write, server nodes read | no |

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit)
