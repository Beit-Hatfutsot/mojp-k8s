# gentrees chart

## Manual sending of gentrees to email

```
kubectl exec gentrees-export-pod-name -- /export/entrypoint.sh send-trees -s 0 -e target@email.com
```

## Deployment

```
./helm_upgrade_external_chart.sh gentrees --install
```

## Secrets

Create htpasswd file for authentication to nginx

```
 htpasswd -bc ./secret-htpasswd username password
```

Get a service account key for storing the backups

```
cat ./secret_service_key
{
  "type": "service_account",
  "project_id": "bh-org-01",
  ...
}
```

Set [nexmo](https://www.nexmo.com/) sms secrets

```
 SMS_API_KEY=
 SMS_API_SECRET=
```

Create the secret

```
kubectl create secret generic gentrees --from-file=htpasswd=./secret-htpasswd \
                                       --from-file=secret_service_key=./secret_service_key \
                                       --from-literal=SMS_API_KEY=$SMS_API_KEY \
                                       --from-literal=SMS_API_SECRET=$SMS_API_SECRET
```
