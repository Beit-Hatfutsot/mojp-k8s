# Kubernetes Environment

## Interacting with the environment

You can interact with the Kubernetes environment in the following ways - 

* [Google Cloud Shell](https://cloud.google.com/shell/docs/quickstart) - The recommended and easiest way. Just setup a Google Cloud account and enable billing (you get 300$ free, you can setup billing alerts to avoid paying by mistake).
* Any modern PC / OS should also work, you will just need to install some basic dependencies like Docker and Google Cloud SDK (possibly more TBD). The main problem with working from local PC is the network connection, if you have a stable, fast connection and know how to install the dependencies, you might be better of running from your own PC.
* Docker - This repo contains a Dockerfile which can be used to interact with the environment from CI / CD / automation tools. See the Docker Ops section below for more details.

This guide will assume you are using Google Cloud Shell because it makes the process easier and faster, but you can follow along from a local PC as well, you might have to install some dependencies manually though.

You can use the cloud shell file editor to edit files, just be sure to configure it to indentation of 2 spaces (not tabs - because they interfere with the yaml files)

## Authorize with GitHub and clone

Having infrastructure as code means you should be able to push any changes to infrastructure configuration back to GitHub.

You can use the following procudure on both Google Cloud Shell and from local PC

Create an SSH key -

```
[ ! -f .ssh/id_rsa.pub ] && ssh-keygen -t rsa -b 4096 -C "${USER}@cloudshell"
cat ~/.ssh/id_rsa.pub
```

Add the key in github - https://github.com/settings/keys

Clone the mojp-k8s repo

```
git clone git@github.com:Beit-Hatfutsot/mojp-k8s.git
```

Change to the mojp-k8s directory, all following commands should run from that directory

```
cd mojp-k8s
```

## Create a new cluster

Creating a new cluster is easiest using the Google Kubernetes Engine UI. It's recommended to start with a minimum of 1 n1-standard-1 node. Need to bear in mind that kubernetes consumes some resources as well.

## Create a new environment

Each environment should have the following files in the root of the project:

- `.env.ENVIRONMENT_NAME` *(required)*: the basic environment connection details
- `values.ENVIRONMENT_NAME.yaml` *(optional)*: override default helm chart values for this namespace

These files shouldn't contain any secrets and can be committeed to a public repo.

## Connecting to an environment

```
source switch_environment.sh ENVIRONMENT_NAME
```

On cloud shell, if you are mostly using this environment / project, add this to your .bashrc:

```
cd mojp-k8s; source switch_environment.sh ENVIRONMENT_NAME
```

## Initialize / Upgrade Helm

Installs / upgrades the Helm server-side component on the cluster

```
helm init --upgrade
```

## Deployment

```
./helm_upgrade.sh [optional helm upgrade arguments]..
```

Helm will detect changes in any subcharts and deploy appropriately.

For initial installation you should add `--install`

On updates, depending on the changes you might need to add `--recreate-pods` or `--force`

For debugging you can also use `--debug` and `--dry-run`

You can use the `force_update.sh` script after your deployed to force update on a specific deployment and wait for rollout to complete

## Configuring values / subcharts

The default values are at `values.yaml` - these are used in the chart template files

Each environment can override the default values using `values.ENVIRONMENT_NAME.yaml` which is merged with the `values.yaml` file

## Secrets

Secrets are stored and managed directly in kubernetes.

To update an existing secret, delete it first `kubectl delete secret SECRET_NAME`

After updating a secret you should update the affected deployments, you can use `./force_update.sh` to do that

#### env-vars

You can make up these values if you are creating a new environment, just keep them secure

```
kubectl create secret generic env-vars \\
                      --from-literal=MINIO_ACCESS_KEY=*** \
                      --from-literal=MINIO_SECRET_KEY=***
```

#### etc-bhs

You should get the files from a team member

```
kubectl create secret generic etc-bhs --from-file app_server.yaml --from-file front-nginx-prerender.conf
```

## Docker OPS

To faciliate CI/CD and other automated flows you can use the provided ops Dockerfile.

The ops container requires a Google Cloud service key:

```
export SERVICE_ACCOUNT_NAME="mojp-k8s-ops"
export SERVICE_ACCOUNT_SECRET_FILE="./secret-${SERVICE_ACCOUNT_NAME}.json"
export SERVICE_ACCOUNT_ID="${SERVICE_ACCOUNT_NAME}@${CLOUDSDK_CORE_PROJECT}.iam.gserviceaccount.com"
gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}"
gcloud iam service-accounts keys create "--iam-account=${SERVICE_ACCOUNT_ID}" "${SERVICE_ACCOUNT_SECRET_FILE}"
```

The following adds admin roles for common services:

```
gcloud projects add-iam-policy-binding --role "roles/storage.admin" "${CLOUDSDK_CORE_PROJECT}" \
                                       --member "serviceAccount:${SERVICE_ACCOUNT_ID}"
gcloud projects add-iam-policy-binding --role "roles/storage.admin" "${CLOUDSDK_CORE_PROJECT}" \
                                       --member "serviceAccount:${SERVICE_ACCOUNT_ID}"
gcloud projects add-iam-policy-binding --role "roles/cloudbuild.builds.editor" "${CLOUDSDK_CORE_PROJECT}" \
                                       --member "serviceAccount:${SERVICE_ACCOUNT_ID}"
gcloud projects add-iam-policy-binding --role "roles/container.admin" "${CLOUDSDK_CORE_PROJECT}" \
                                       --member "serviceAccount:${SERVICE_ACCOUNT_ID}"
```

Build and run the docker container

```
docker build -t mojp-k8s-ops . &&\
docker run -it -v "`pwd`/${SERVICE_ACCOUNT_SECRET_FILE}:/k8s-ops/secret.json" mojp-k8s-ops
```

You should be able to run `source switch_environment.sh production` and continue working with the environment from there.

## Continuos Deployment

We use a basic CD flow based on Travis and GitHub:

* PR is merged to master branch on an app repo
* Travis build on master branch of each app repo starts the continuous deployment process for that repo
* This process involves the following steps
  * git pull from the k8s repo / master
  * update values.yaml file with the app docker image
  * push to github
  * perform a rolling update on the relevant apps deployment / perform additional deployment steps

You should enable Travis for each app repo:

```

```

























