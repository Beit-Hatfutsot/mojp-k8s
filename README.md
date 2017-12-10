# The Museum Of The Jewish People Kubernetes Environment

## Why can't it just work all the time?

[![it can - with Kubernetes!](it-can-with-kubernetes.png)](https://cloud.google.com/kubernetes-engine/kubernetes-comic/)

## Interacting with the environment

You can interact with the Kubernetes environment in the following ways - 

* [Google Cloud Shell](https://cloud.google.com/shell/docs/quickstart) - The recommended and easiest way for running management commands. Just setup a Google Cloud account and enable billing (you get 300$ free, you can setup billing alerts to avoid paying by mistake).
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

These files shouldn't contain any secrets and can be committed to a public repo.

## Connecting to an environment

```
source switch_environment.sh production
```

On cloud shell, if you are mostly using this environment / project, add this to your .bashrc:

```
cd mojp-k8s; source switch_environment.sh production
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

Each environment can override the default values using `values.production.yaml` which is merged with the `values.yaml` file

## Secrets

Secrets are stored and managed directly in kubernetes.

To update an existing secret, delete it first `kubectl delete secret SECRET_NAME`

After updating a secret you should update the affected deployments, you can use `./force_update.sh` to do that

#### env-vars

You can make up these values if you are creating a new environment, just keep them secure

```
kubectl create secret generic env-vars \
                      --from-literal=MINIO_ACCESS_KEY=admin \
                      --from-literal=MINIO_SECRET_KEY=**********
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
export SERVICE_ACCOUNT_ID="${SERVICE_ACCOUNT_NAME}@${CLOUDSDK_CORE_PROJECT}.iam.gserviceaccount.com"
gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}"
gcloud iam service-accounts keys create "--iam-account=${SERVICE_ACCOUNT_ID}" ./secret-mojp-k8s-ops.json
```

Add admin roles for common services:

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

Build and run the ops docker container

```
docker build -t mojp-k8s-ops . &&\
docker run -it -v "`pwd`/secret-mojp-k8s-ops.json:/k8s-ops/secret.json" \
               -v "`pwd`:/ops" \
               mojp-k8s-ops
```

You should be able to run `source switch_environment.sh production` and continue working with the environment from there.

## Continuos Deployment

Each app / module is self-deploying using the ops docker and manages it's own deployment script.

The continuous deployment flow is based on:

* Travis - runs the deployment script on each app's repo on commit to master branch (AKA merge of PR).
* Ops Docker (see above) - provides a consistent deployment environment and to securely authenticate with the service account secret.
* GitHub - for persistency of deployment environment values - GitHub maintains the state of the environment. Each app commits deployment updates to the k8s repo.

We use [Travis CLI](https://github.com/travis-ci/travis.rb#installation) below but you can also do the setup from the UI.

#### Setting up a repo for continuous deployment

Enable Travis for the repo (run `travis enable` from the repo directory)

Copy `.travis.yml` and `continuous_deployment.sh` from this repo to the app repo

Modify the deployment code in continuous_deployment.sh according to your app requirements

Set the k8s ops service account secret on travis:

```
travis encrypt-file ../mojp-k8s/secret-mojp-k8s-ops.json secret-mojp-k8s-ops.json.enc
```

Copy the `openssl` command output by the above command and modify in your continuous_deployment.sh

Modify the -out param of the openssl command to `-out k8s-ops-secret.json`

Create a GitHub machine user according to [these instructions](https://developer.github.com/v3/guides/managing-deploy-keys/#machine-users).

Give this user write permissions to the k8s repo.

Add the GitHub machine user secret key to travis on the app's repo:

```
travis env set --private K8S_OPS_GITHUB_REPO_TOKEN "*****"
```

Commit the .travis.yml changes and the encrypted file.

## App Docker Images

For the above continuous deployment procedure you will also need to build each app docker image automatically.

The easiest way is to add an automated build for the app repo in Google Container Registry, you can do that in the UI

The above example continuous deployment script uses an image which is tagged with the git commit sha

In this case the resulting image tag should look like:

`gcr.io/bh-org-01/mojp-dbs-front:5b1030d34e77e60db1b8384a3b68f690de5a4a9c`

Where the tag is the git commit sha

This allows the continuous deployment to update the image tag ASAP without waiting for it to be built.

Kubernetes will make sure the deployment occurs only when the image is ready.

## Load Balancer - static IP

Traefik uses a load balancer service which by default has a temporary IP which changes on updates.

Reserve a static IP:

```
gcloud compute addresses create mojp-production-traefik --region=europe-west1
```

Get the IP address and update the traefik values:

```
IP=`gcloud compute addresses describe mojp-production-traefik --region=europe-west1 | grep ^address: | cut -d" " -f2 -`
./update_yaml.py '{"traefik":{"loadBalancerIP":"'$IP'"}}' "values.${K8S_ENVIRONMENT_NAME}.yaml"
```
