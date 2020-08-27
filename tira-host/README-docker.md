# TIRA 9 Application

## Non-betaweb deployment

In order to successfully run dockerized TIRA Host following requirements should be met by the host machine:

- VirtualBox 5.2.34 and extension pack (see https://github.com/tira-io/tira9-application2/tree/master#installing-a-tira-host or Dockerfile)
- Docker
- Permissions of TIRA model folder contents should be set to ```tira``` user/group: ```sudo chown -R 1010:1010 initial-docker-tira-model```
  - Folder ```initial-docker-tira-model``` in the current project is a sample TIRA data model including test Alpine Linux VM image.

### Build the image

```bash
# cd .../tira9-application2
docker build -t webis/tira9-application2:v1 --build-arg tira_password=tira -f build/Dockerfile .
```

### Run the container

```bash
# cd .../tira9-application2
docker run \
    -d \
    -v /dev/vboxdrv:/dev/vboxdrv \
    -v /dev/vboxnetflt:/dev/vboxnetflt \
    -v /dev/vboxnetadp:/dev/vboxnetadp \
    -v /dev/vboxpci:/dev/vboxpci \
    -v /dev/vboxnetctl:/dev/vboxnetctl \
    -v /mnt/nfs/tira:/mnt/nfs/tira \   # if necessary to use pre-mounted cehp/nfs storage
    -v $PWD/build/initial-docker-tira-model:/mnt/nfs/tira \   # or in case of local dev deployment
    --env TIRA_FQDN=$(hostname) \   # change to the host FQDN if necessary
    --name="tira" \
    --privileged \
    --cap-add=NET_ADMIN \
    --network host \
    --hostname=$(hostname) \
    webis/tira9-application2:v1 tail -f /dev/null
```

## Deployment on a betaweb machine

Certain simplifications were made regarding deployment of dockerized  TIRA host on a betaweb, as currently it is only used for development and testing: e.g. SSH server inside container is not exposed, instead all TIRA command calls executed on the host are passed into the container with "alias" in /usr/bin/tira script (see below).

The following steps should be done on the host machine:

- apply tira salt state:
  - iptables
  - virtualbox, extpack
  - mount /mnt/ceph/tira
  - tira user, ssh key
  - dnsmasq
  - ...
- install docker
- modify /usr/bin/tira to execute tira commands inside the container:

  ```bash
    #!/bin/bash
    docker exec -it tira tira "$@"
  ```

- add tira user to docker group: ```sudo usermod -aG docker tira```
- /home/tira/.ssh/* should be copied to the container /home/tira/.ssh/ (This is done in docker run command)
- change ```tira_password``` in ```docker build``` command

### Build the image

```bash
# cd .../tira9-application2
docker build -t webis/tira9-application2:v1 --build-arg tira_password=tira -f build/Dockerfile .
```

### Run the container

```bash
# cd .../tira9-application2
docker run \
    -d \
    -v /dev/vboxdrv:/dev/vboxdrv \
    -v /dev/vboxnetflt:/dev/vboxnetflt \
    -v /dev/vboxnetadp:/dev/vboxnetadp \
    -v /dev/vboxpci:/dev/vboxpci \
    -v /dev/vboxnetctl:/dev/vboxnetctl \
    -v /mnt/nfs/tira:/mnt/nfs/tira \   # if necessary to use pre-mounted cehp/nfs storage
    -v /home/tira/.ssh:/home/tira/.ssh \
    --name="tira" \
    --privileged \
    --cap-add=NET_ADMIN \
    --network host \
    --hostname=$(hostname) \
    webis/tira9-application2:v1 tail -f /dev/null
```
