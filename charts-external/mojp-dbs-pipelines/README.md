# mojp-dbs-pipelines


## Deployment

```
./helm_upgrade_chart.sh mojp-dbs-pipelines
```


## Secrets

The chart requires a Clearmash API token.

Replace `<CLEARMASH_TOKEN>` in the following command with a valid token

```
! kubectl describe secret clearmash &&\
  kubectl create secret generic clearmash --from-literal=CLEARMASH_CLIENT_TOKEN=<CLEARMASH_TOKEN>
```
