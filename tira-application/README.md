## Setup

### Local Dev Setup

For local dev setup:
  - have python3 and virtualenv installed
  - have `/mnt/ceph/tira` mounted
  - have a tira account that can read `/mnt/ceph/tira`
 
0. (optional) `tira-protocol~$ make build`
1. `~$ make setup`
2. `~$ make run-dev`

### Kubernetes

Use `make k8s-deploy-tira-application` and `make k8s-undeploy-tira-application`.

### Docker

0. (optional) `tira-protocol~$ make build`
1. `make docker-build-tira-application`
2. `make docker-run-tira-application`
3. (optional) Publish a new version to docker hub: `make docker-publish-tira-application`

## Settings 

The environment for the docker deployment can be configured via settings files, which can be found at `tira-application/config/`. 

## Database

The docker setup uses a pre-existing database located at `tira_root/state/`, where `tira_root` as given in the settings will be mounted. This database must be created once by running 

`make deployment-migrations`
