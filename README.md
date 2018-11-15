# The Museum Of The Jewish People Kubernetes Environment

See the [sk8s documentation](https://github.com/OriHoch/sk8s/blob/master/README.md)

Install Helm in the compatible version

```
HELM_VERSION=v2.8.2

curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get > get_helm.sh &&\
     chmod 700 get_helm.sh &&\
     ./get_helm.sh --version "${HELM_VERSION}" &&\
     helm version --client && rm ./get_helm.sh
```

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

## Deploy Mongo

Connect to the cluster

```
source connect.sh
```

Deploy

```
helm upgrade mongo charts-external/mongo/ --install
```

Port forward to mongo-express

```
kubectl port-forward deployment/mongoexpress 8081
```

Access mongo-express at http://localhost:8081

## Deploy Heptio ARK Backups


Create a GCS bucket to hold backups: `mojp-k8s-ark-backups`

Create a service account for Ark server

```
gcloud --project=bh-org-01 iam service-accounts create mojp-k8s-heptio-ark \
    --display-name "mojp-k8s Heptio Ark service account"
```

Give permissions to the service account

```
ROLE_PERMISSIONS=(
     compute.disks.get
     compute.disks.create
     compute.disks.createSnapshot
     compute.snapshots.get
     compute.snapshots.create
     compute.snapshots.useReadOnly
     compute.snapshots.delete
     compute.projects.get
     storage.objects.create
)
gcloud iam roles create heptio_ark.server \
     --project bh-org-01 \
     --title "Heptio Ark Server" \
     --permissions "$(IFS=","; echo "${ROLE_PERMISSIONS[*]}")" &&\
 gcloud projects add-iam-policy-binding bh-org-01 \
     --member serviceAccount:mojp-k8s-heptio-ark@bh-org-01.iam.gserviceaccount.com \
     --role projects/bh-org-01/roles/heptio_ark.server &&\
gsutil iam ch serviceAccount:mojp-k8s-heptio-ark@bh-org-01.iam.gserviceaccount.com:objectAdmin gs://mojp-k8s-backups
```

Make sure you are connected to the relevant environment

```
source connect.sh
```

Create service account and secret

```
TEMPFILE=`mktemp` &&\
kubectl create ns heptio-ark &&\
gcloud iam service-accounts keys create $TEMPFILE \
     --iam-account mojp-k8s-heptio-ark@bh-org-01.iam.gserviceaccount.com &&\
kubectl create secret generic cloud-credentials --namespace heptio-ark --from-file cloud=$TEMPFILE &&\
rm $TEMPFILE
```

Install Heptio Ark prerequisites

```
kubectl apply -f manifests/ark/00-prereqs.yaml
```

Deploy Heptio Ark server to the cluster

```
kubectl apply -f manifests/ark/00-ark-config.yaml
kubectl apply -f manifests/ark/10-deployment.yaml
```

Install Ark client

```
wget https://github.com/heptio/ark/releases/download/v0.9.4/ark-v0.9.4-linux-amd64.tar.gz
tar -xvzf ark-v0.9.4-linux-amd64.tar.gz
sudo mv ark /usr/local/bin/
sudo mv ark-restic-restore-helper /usr/local/bin
rm ark-v0.9.4-linux-amd64.tar.gz
```

Schedule daily cluster-wide backup with retention of 30 days

```
ark schedule create cluster-daily --schedule '0 13 * * *' --ttl 720h0m0s
```

See latest backups

```
ark get backups && ark get schedules
```


## Deploy Elasticsearch for dbs

Connect to the cluster

```
source connect.sh
```

Deploy

```
helm upgrade elasticsearch charts-external/elasticsearch/ --install
```

Port forward to elasticsearch

```
kubectl port-forward deployment/mongoexpress 9200
```

