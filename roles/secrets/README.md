# pokerops.rke2.secrets

Cluster secrets for RKE2 clusters.

Deployed as a deliberate pre-step, ahead of `pokerops.rke2.components`, so
credentials exist before the components that consume them. Kept out of the
components role for that reason: a normal component deploy does not create
secrets.

## Role Variables

| Parameter    | Default | Type | Description                              | Required |
| :----------- | ------: | :--- | :--------------------------------------- | :------- |
| rke2_secrets |      [] | list | List of secrets to create in the cluster | no       |

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit)
