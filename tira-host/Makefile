# -v $PWD/build/initial-docker-tira-model:/mnt/nfs/tira \
# -v $PWD/src:/usr/lib/tira \

run-tira-docker: build-tira-docker
docker run \
    -d \
    -v /dev/vboxdrv:/dev/vboxdrv \
    -v /dev/vboxnetflt:/dev/vboxnetflt \
    -v /dev/vboxnetadp:/dev/vboxnetadp \
    -v /dev/vboxpci:/dev/vboxpci \
    -v /dev/vboxnetctl:/dev/vboxnetctl \
    -v /mnt/nfs/tira:/mnt/nfs/tira \
    -v /home/tira:/home/tira \
    --name="tira-host" \
    --privileged \
    --cap-add=NET_ADMIN \
    --network host \
    --hostname=$(hostname) \
    tira-io/tira-host -f /dev/null

build-tira-docker:
	docker build -t tira-io/tira-host --build-arg TIRA_PASSWORD=tira --build-arg VBOXVERSION=6.1.16 -f build/Dockerfile .
