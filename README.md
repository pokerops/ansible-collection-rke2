# Ansible Collection - pokerops.rke2

[![Build Status](https://github.com/pokerops/ansible-collection-rke2/actions/workflows/molecule.yml/badge.svg)](https://github.com/pokerops/ansible-collection-rke2/actions/wofklows/molecule.yml)
[![Ansible Galaxy](http://img.shields.io/badge/ansible--galaxy-pokerops.rke2-blue.svg)](https://galaxy.ansible.com/ui/repo/published/pokerops/rke2/)

An opinionated [ansible collection](https://galaxy.ansible.com/ui/repo/published/pokerops/rke2/) to install and manage rke2 clusters matching standard components:

- [MetalLB](https://metallb.universe.tf/)
- [Longhorn](https://longhorn.io/)
- [CertManager](https://cert-manager.io/docs/)
- [Ingress Nginx](https://kubernetes.github.io/ingress-nginx/)
- [ArgoCD](https://argo-cd.readthedocs.io/en/stable/)

Default installation uses [ArgoCD Applications](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/) to deploy and manage the following components:

- [Keel](https://keel.sh/)
- [KServe](https://kserve.github.io/website/)
- [Kubernetes Reflector](https://github.com/emberstack/kubernetes-reflector)
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
- [Strimzi Operator](https://strimzi.io/)
- [Velero](https://velero.io/)
- [Zalando Operator](https://github.com/zalando/postgres-operator)

## To Do

- Add Molecule test scenario for Kafka backup and restore
- Add Molecule test scenario for Sealed Secrets backup and restore
- Add Grafana operator to base cluster deployment
- Add Grafana deployment to base cluster components
- Add Molecule test scenario for Grafana backup and restore

## Collection Variables

The following is the list of parameters intended for end-user manipulation:

Cluster wide parameters

| Parameter                              |                            Default | Type   | Description                                                              | Required |
| :------------------------------------- | ---------------------------------: | :----- | :----------------------------------------------------------------------- | :------- |
| rke2_cluster_name                      |                                n/a | string | Cluster name, immutable after creation                                   | yes      |
| rke2_version                           |                     v1.33.0+rke2r1 | string | RKE2 version to deploy                                                   | no       |
| rke2_nolog                             |                               true | bool   | Toggle flag for logging sensitive statements                             | no       |
| rke2_config_hostnames                  |                               true | bool   | Toggle flag for cluster hostfile entry configuration                     | no       |
| rke2_retry_num                         |                                 10 | bool   | Max number of task retries                                               | no       |
| rke2_retry_delay                       |                                 30 | bool   | Task delay on retries                                                    | no       |
| rke2_evict_timeout                     |                                300 | bool   | Node drain eviction timeout in seconds                                   | no       |
| rke2_ippool_private                    |                                n/a | string | Private IP pool CIDR                                                     | yes      |
| rke2_ippool_public                     |                                n/a | string | Public IP pool CIDR                                                      | no       |
| rke2_certmanager_acme_secret           |                                n/a | string | Secret name for ACME challenge                                           | no       |
| rke2_certmanager_acme_email            |                                n/a | string | Email for ACME challenge                                                 | no [1]   |
| rke2_argocd_hostname                   |   "argocd.{{ rke2_cluster_name }}" | string | ArgoCD hostname                                                          | no       |
| rke2_argocd_values                     |                         object [2] | dict   | Helm chart values for ArgoCD chart                                       | no       |
| rke2_argocd_apps_deploy                |                               true | dict   | Toggle flag for ArgoCD Applications chart deployment                     | no       |
| rke2_argocd_apps_values                |                                n/a | dict   | Helm chart values for ArgoCD Applications chart                          | no       |
| rke2_argocd_values_configs             |                                 {} | dict   | ArgoCD configs, override for default ArgoCD chart values                 | no       |
| rke2_argocd_values_notifications       |                                 {} | dict   | ArgoCD notifications, override for default ArgoCD chart values           | no       |
| rke2_argocd_values_cluster_credentials |                                 {} | dict   | ArgoCD Cluster Credentials, override for default ArgoCD chart values     | no       |
| rke2_argocd_exec_timeout               |                                 3m | string | ArgoCD exec timeout, override for default ArgoCD chart values            | no       |
| rke2_argocd_redis_ha_enabled           |                               true | bool   | ArgoCD Redis HA toggle, override for default ArgoCD chart values         | no       |
| rke2_argocd_controller_replicas        |                                  2 | int    | ArgoCD controller replicas, override for default ArgoCD chart values     | no       |
| rke2_argocd_server_replicas            |                                  2 | int    | ArgoCD server replicas, override for default ArgoCD chart values         | no       |
| rke2_argocd_reposerver_replicas        |                                  2 | int    | ArgoCD repo server replicas, override for default ArgoCD chart values    | no       |
| rke2_argocd_applicationset_replicas    |                                  2 | int    | ArgoCD applicationset replicas, override for default ArgoCD chart values | no       |
| rke2_argocd_apps_pokerops_revision     |                               HEAD | string | PokerOps ArgoCD revision, used to deploy base cluster assets             | no       |
| rke2_longhorn_hostname                 | "longhorn.{{ rke2_cluster_name }}" | string | Longhorn UI hostname                                                     | no       |
| rke2_nolog                             |                               true | bool   | Toggle flag for logging sensitive statements                             | no       |

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
    applicationsetcontroller.namespaces: "*"
global:
  env:
    - name: ARGOCD_EXEC_TIMEOUT
      value: 3m
```

## Collection roles

- pokerops.rke2.components
- pokerops.rke2.rke2

## Collection playbooks

- pokerops.rke2.install: Install and (re)configure cluster
- pokerops.rke2.deploy: Deploy individual cluster components
- pokerops.rke2.secrets: Deploy cluster secrets
- pokerops.rke2.init: Deploy base cluster components
- pokerops.rke2.update: Start rke2 cluster services
- pokerops.rke2.velero.s3: Start rke2 cluster services

## Testing

You can test the collection directly from sources using command `make test`

Role releases are ci/cd tested against the following distributions:

- Ubuntu Noble
- Ubuntu Jammy

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit)
