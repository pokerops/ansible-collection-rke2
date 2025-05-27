# pokerops.rke2.components

Standard cluster components for RKE2 clusters.

## Role Variables

| Parameter                    |                        Default | Type   | Description                              | Required |
| :--------------------------- | -----------------------------: | :----- | :--------------------------------------- | :------- |
| rke2_argocd_hostname         | argocd.{{ rke2_cluster_name }} | string | Argocd URL                               | no       |
| rke2_secrets                 |                             [] | list   | List of secrets to create in the cluster | no       |
| rke2_certmanager_issuer_name |                 cluster-issuer | string | Name of the cert-manager cluster issuer  | no       |

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit)
