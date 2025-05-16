# Ansible Collection - pokerops.rke2

[![Build Status](https://github.com/pokerops/ansible-collection-rke2/actions/workflows/molecule.yml/badge.svg)](https://github.com/pokerops/ansible-collection-rke2/actions/wofklows/molecule.yml)
[![Ansible Galaxy](http://img.shields.io/badge/ansible--galaxy-pokerops.rke2-blue.svg)](https://galaxy.ansible.com/ui/repo/published/pokerops/rke2/)

An [ansible collection](https://galaxy.ansible.com/ui/repo/published/pokerops/rke2/) to install and manage rke2 clusters

## Collection Variables

The following is the list of parameters intended for end-user manipulation:

Cluster wide parameters

| Parameter             |               Default | Type   | Description                            | Required |
| :-------------------- | --------------------: | :----- | :------------------------------------- | :------- |
| rke2_cluster_name     |                   n/a | string | Cluster name, immutable after creation | yes      |
| rke2_release_rke      |                v1.5.6 | string | RKE2 release to deploy                 | no       |
| rke2_release_k8s      |   v1.27.11-rancher1-1 | string | K8s release to deploy                  | no       |
| rke2_retry_num        |                    10 | bool   | Max number of task retries             | no       |
| rke2_retry_delay      |                    30 | bool   | Task delay on retries                  | no       |
| rke2_backup_interval  |                     1 | bool   | Backup interval in hours               | no       |
| rke2_backup_retention |                    24 | bool   | Backup retention in hours              | no       |
| rke2_evict_timeout    |                   300 | bool   | Node drain eviction timeout in seconds | no       |
| rke2_install_user     | {{ ansible_user_id }} | string | RKE2 install user                      | no       |

## Collection roles

- pokerops.rke2.k8s

## Collection playbooks

- pokerops.rke2.install: Install and (re)configure cluster
- pokerops.rke2.k8s: Deploy base K8s services
- pokerops.rke2.restart: Stop rke2 cluster services
- pokerops.rke2.update: Start rke2 cluster services

## Testing

You can test the collection directly from sources using command `make test`

Role releases are ci/cd tested against the following distributions:

- Ubuntu Noble
- Ubuntu Jammy

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit)
