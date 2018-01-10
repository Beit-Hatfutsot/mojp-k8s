# The Museum Of The Jewish People Kubernetes Environment

See the [sk8s documentation](https://github.com/OriHoch/sk8s/blob/master/README.md)


## Secrets

#### env-vars

You can make up these values if you are creating a new environment, just keep them secure

```
kubectl create secret generic env-vars \
                      --from-literal=MINIO_ACCESS_KEY=admin \
                      --from-literal=MINIO_SECRET_KEY=**********
```

#### etc-bhs secret

You should get the files from a team member

```
kubectl create secret generic etc-bhs --from-file app_server.yaml --from-file front-nginx-prerender.conf
```


## Minio management

```
kubectl exec -it minio-954ddffbc-j9ddc sh
apk --update add bash openssl curl && bash
curl https://dl.minio.io/client/mc/release/linux-amd64/mc > /bin/mc && chmod +x /bin/mc
mc config host add minio http://localhost:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
mc --help
```
