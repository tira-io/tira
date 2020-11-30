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
1. `~$ docker build --tag tira-web-2:latest -f Dockerfile-application .`
2. `~$ docker run -ti --rm -p 8080:8080 -v=/mnt/ceph/storage/data-in-progress/_TO_BE_MOVED/tira10-dev:/mnt/ceph/tira tira-web-2:latest`