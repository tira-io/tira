run-tira-docker: build-tira-docker
docker run \
    -d \
    -v /dev/vboxdrv:/dev/vboxdrv \
    -v /dev/vboxnetflt:/dev/vboxnetflt \
    -v /dev/vboxnetadp:/dev/vboxnetadp \
    -v /dev/vboxpci:/dev/vboxpci \
    -v /dev/vboxnetctl:/dev/vboxnetctl \
    -v /mnt/nfs/tira:/mnt/nfs/tira \
    -v $PWD/build/initial-docker-tira-model:/mnt/nfs/tira \
    --name="tira" \
    --privileged \
    --cap-add=NET_ADMIN \
    --network host \
    --hostname=$(hostname) \
    webis/tira9-application2:v1 tail -f /dev/null

build-tira-docker:
	docker build -t webis/tira9-application2:v1 --build-arg tira_password=tira -f build/Dockerfile .

