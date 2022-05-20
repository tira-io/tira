VENV_NAME?=venv
VENV_ACTIVATE=. $(VENV_NAME)/bin/activate
PYTHON=${VENV_NAME}/bin/python3
VERSION=0.0.11
VBOXVERSION=6.1.18
TIRA_PASSWORD=tira
TIRA_MODEL_PATH=/mnt/ceph/tira
DEV_MODE=true # if `true` grpc service will be executed via watchdog
PYCHARM_VERSION=213.6777.50
CONTAINER_NAME=tira-host-dev

venv:
	test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	#${PYTHON} -m pip install grpcio grpcio-tools
	${PYTHON} -m pip install -r build/requirements.txt

run-dev: build-image
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
		-v ${PWD}/src/tira_host/conf/grpc_service-dev.ini:/tira/tira_host/conf/grpc_service.ini \
		--name="$(CONTAINER_NAME)" \
		--privileged \
		--cap-add=NET_ADMIN \
		--network host \
		--hostname=$(hostname) \
		--env DEV=$(DEV_MODE) \
		--add-host=host.docker.internal:host-gateway \
		tira-io/tira-host:$(VERSION) -f /dev/null

build-image:
	cp ../protocol/build/python/* src/tira_host/proto/
	docker build -t tira-io/tira-host:$(VERSION) --build-arg TIRA_PASSWORD=$(TIRA_PASSWORD) --build-arg VBOXVERSION=$(VBOXVERSION) --build-arg PYCHARM_VERSION=$(PYCHARM_VERSION) -f build/Dockerfile .

export-image: build
	sudo docker save tira-io/tira-host:$(VERSION) -o /mnt/ceph/tira/data/tira-host-images/tira-io-tira-host-$(VERSION).tar
