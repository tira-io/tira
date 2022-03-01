VENV_NAME?=venv
VENV_ACTIVATE=. $(VENV_NAME)/bin/activate
PYTHON=${VENV_NAME}/bin/python3
VERSION=0.0.8-dev
VBOXVERSION=6.1.16
TIRA_PASSWORD=tira
TIRA_MODEL_PATH=/mnt/nfs/tira
#TIRA_MODEL_PATH=/home/nikolay/workspace/github/tira/model/src
DEV_MODE=false # if ture grpc service inside the container won't start
CONTAINER_NAME=tira-host-dev

venv:
	test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	${PYTHON} -m pip install grpcio grpcio-tools

run-tira-docker-dev: build-tira-docker
	docker container rm -f $(CONTAINER_NAME)
	docker run \
		-d \
		-v /dev/vboxdrv:/dev/vboxdrv \
		-v /dev/vboxnetflt:/dev/vboxnetflt \
		-v /dev/vboxnetadp:/dev/vboxnetadp \
		-v /dev/vboxpci:/dev/vboxpci \
		-v /dev/vboxnetctl:/dev/vboxnetctl \
		-v $(TIRA_MODEL_PATH):/mnt/nfs/tira \
		-v ${PWD}/src:/tira \
		-v ${PWD}/src/tira_scripts:/usr/lib/tira \
		--name="$(CONTAINER_NAME)" \
		--privileged \
		--cap-add=NET_ADMIN \
		--network host \
		--hostname=$(hostname) \
		--env DEV=$(DEV_MODE) \
		tira-io/tira-host:$(VERSION) -f /dev/null

build-tira-docker:
	cp ../protocol/build/python/* src/tira_host/proto/
	docker build -t tira-io/tira-host:$(VERSION) --build-arg TIRA_PASSWORD=$(TIRA_PASSWORD) --build-arg VBOXVERSION=$(VBOXVERSION) -f build/Dockerfile .

export-tira-image: build-tira-docker
	sudo docker save tira-io/tira-host:$(VERSION) -o /mnt/ceph/tira/data/tira-host-images/tira-io-tira-host-$(VERSION).tar

clean:
	rm -r $(VENV_NAME)
