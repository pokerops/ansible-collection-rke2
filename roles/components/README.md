# pokerops.rke2.components

Standard cluster components for RKE2 clusters.

## Role Variables

| Parameter                    |                        Default | Type   | Description                                        | Required |
| :--------------------------- | -----------------------------: | :----- | :------------------------------------------------- | :------- |
| rke2_argocd_hostname         | argocd.{{ rke2_cluster_name }} | string | Argocd URL                                         | no       |
| rke2_certmanager_issuer_name |                 cluster-issuer | string | Name of the cert-manager cluster issuer            | no       |
| rke2_monitoring_endpoint     |                                | string | Remote ingestor URL; setting it enables monitoring | no       |
| rke2_monitoring_cluster_id   |        {{ rke2_cluster_name }} | string | Cluster label stamped on every metric              | no       |
| rke2_monitoring_tls_enabled  |                          false | bool   | Use mTLS to reach the remote ingestor              | no       |

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit)
