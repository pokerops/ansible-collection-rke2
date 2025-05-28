# Ansible Collection - pokerops.rke2

[![Build Status](https://github.com/pokerops/ansible-collection-rke2/actions/workflows/molecule.yml/badge.svg)](https://github.com/pokerops/ansible-collection-rke2/actions/wofklows/molecule.yml)
[![Ansible Galaxy](http://img.shields.io/badge/ansible--galaxy-pokerops.rke2-blue.svg)](https://galaxy.ansible.com/ui/repo/published/pokerops/rke2/)

An [ansible collection](https://galaxy.ansible.com/ui/repo/published/pokerops/rke2/) to install and manage rke2 clusters

## Collection Variables

The following is the list of parameters intended for end-user manipulation:

Cluster wide parameters

| Parameter                           |                          Default | Type   | Description                                                              | Required |
| :---------------------------------- | -------------------------------: | :----- | :----------------------------------------------------------------------- | :------- |
| rke2_cluster_name                   |                              n/a | string | Cluster name, immutable after creation                                   | yes      |
| rke2_version                        |                   v1.33.0+rke2r1 | string | RKE2 version to deploy                                                   | no       |
| rke2_retry_num                      |                               10 | bool   | Max number of task retries                                               | no       |
| rke2_retry_delay                    |                               30 | bool   | Task delay on retries                                                    | no       |
| rke2_evict_timeout                  |                              300 | bool   | Node drain eviction timeout in seconds                                   | no       |
| rke2_ippool_private                 |                              n/a | string | Private IP pool CIDR                                                     | yes      |
| rke2_ippool_public                  |                              n/a | string | Public IP pool CIDR                                                      | no       |
| rke2_certmanager_acme_secret        |                              n/a | string | Secret name for ACME challenge                                           | no       |
| rke2_certmanager_acme_email         |                              n/a | string | Email for ACME challenge                                                 | no [1]   |
| rke2_argocd_hostname                | "argocd.{{ rke2_cluster_name }}" | string | ArgoCD hostname, used for ingress                                        | no       |
| rke2_argocd_values                  |                       object [2] | dict   | Helm chart values for ArgoCD Applications chart                          | no       |
| rke2_argocd_apps_values             |                              n/a | dict   | Helm chart varlues for ArgoCD Applications chart                         | no       |
| rke2_argocd_values_configs          |                       object [3] | dict   | ArgoCD configs, override for default ArgoCD chart values                 | no       |
| rke2_argocd_exec_timeout            |                               3m | string | ArgoCD exec timeout, override for default ArgoCD chart values            | no       |
| rke2_argocd_redis_ha_enabled        |                             true | bool   | ArgoCD Redis HA toggle, override for default ArgoCD chart values         | no       |
| rke2_argocd_controller_replicas     |                                2 | int    | ArgoCD controller replicas, override for default ArgoCD chart values     | no       |
| rke2_argocd_server_replicas         |                                2 | int    | ArgoCD server replicas, override for default ArgoCD chart values         | no       |
| rke2_argocd_reposerver_replicas     |                                2 | int    | ArgoCD repo server replicas, override for default ArgoCD chart values    | no       |
| rke2_argocd_applicationset_replicas |                                2 | int    | ArgoCD applicationset replicas, override for default ArgoCD chart values | no       |

[1] rke2_certmanager_acme_email is required whenever rke2_certmanager_acme_secret is set
[2] rke2_argocd_values default is as follows:

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
    ingressClassName: nginx-private
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
  cm:
    application.resourceTrackingMethod: label
global:
  env:
    - name: ARGOCD_EXEC_TIMEOUT
      value: 3m
```

[3] rke2_argocd_values_configs default is as follows:

```yaml
params:
  application.namespaces: "*"
cm:
  application.resourceTrackingMethod: label
```

## Collection roles

- pokerops.rke2.components
- pokerops.rke2.rke2

## Collection playbooks

- pokerops.rke2.install: Install and (re)configure cluster
- pokerops.rke2.init: Deploy base K8s services
- pokerops.rke2.update: Start rke2 cluster services

## Testing

You can test the collection directly from sources using command `make test`

Role releases are ci/cd tested against the following distributions:

- Ubuntu Noble
- Ubuntu Jammy

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit)

```

```
