## Setup

### Local Dev Setup

For local dev setup:
  - have python3 and virtualenv installed
  - have `/mnt/ceph/tira` mounted
  - have a tira account that can read `/mnt/ceph/tira`
 
0. (optional) `tira-protocol~$ make build`
1. `~$ make setup`
2. `~$ make run-dev`

### Docker

0. (optional) `tira-protocol~$ make build`
1. `make build-tira-application-docker`
2. `make run-tira-application-docker`
3. (optional) Publish a new version to docker hub: `make publish-tira-application-docker`
