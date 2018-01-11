# mojp-dbs-searchapp


## Deployment

```
./helm_upgrade_chart.sh mojp-dbs-searchapp
```


## Entrypoint

```
kubectl port-forward mojp-dbs-searchapp-<TAB><TAB> 8000
```

http://localhost:8000/searchapp/
