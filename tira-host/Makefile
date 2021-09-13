VENV_NAME?=venv
VENV_ACTIVATE=. $(VENV_NAME)/bin/activate
PYTHON=${VENV_NAME}/bin/python3
VERSION=0.0.2
VBOXVERSION=6.1.16
TIRA_PASSWORD=tira

venv:
	test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	${PYTHON} -m pip install grpcio grpcio-tools

run-tira-docker-prod: build-tira-docker
	docker run \
		-d \
		-v /dev/vboxdrv:/dev/vboxdrv \
		-v /dev/vboxnetflt:/dev/vboxnetflt \
		-v /dev/vboxnetadp:/dev/vboxnetadp \
		-v /dev/vboxpci:/dev/vboxpci \
		-v /dev/vboxnetctl:/dev/vboxnetctl \
		-v /mnt/ceph/tira:/mnt/nfs/tira \
		-v /home/tira:/home/tira \
		--name="tira-host" \
		--privileged \
		--cap-add=NET_ADMIN \
		--network host \
		--hostname=$(hostname) \
		tira-io/tira-host -f /dev/null

run-tira-docker-dev: build-tira-docker
	docker container rm -f tira-host-dev
	docker run \
		-d \
		-v /dev/vboxdrv:/dev/vboxdrv \
		-v /dev/vboxnetflt:/dev/vboxnetflt \
		-v /dev/vboxnetadp:/dev/vboxnetadp \
		-v /dev/vboxpci:/dev/vboxpci \
		-v /dev/vboxnetctl:/dev/vboxnetctl \
		-v /mnt/nfs/tira:/mnt/nfs/tira \
		-v ${PWD}/src:/tira \
		-v ${PWD}/src/tira_scripts:/usr/lib/tira \
		--name="tira-host-dev" \
		--privileged \
		--cap-add=NET_ADMIN \
		--network host \
		--hostname=$(hostname) \
		--env DEV=true \
		tira-io/tira-host -f /dev/null


build-tira-docker:
	docker build -t tira-io/tira-host --build-arg TIRA_PASSWORD=$(TIRA_PASSWORD) --build-arg VBOXVERSION=$(VBOXVERSION) -f build/Dockerfile .

export-tira-image:
	docker build -t tira-io/tira-host:$(VERSION) --build-arg TIRA_PASSWORD=$(TIRA_PASSWORD) --build-arg VBOXVERSION=$(VBOXVERSION) -f build/Dockerfile .
	sudo docker save tira-io/tira-host:$(VERSION) -o /mnt/ceph/tira/data/tira-dockerized-host-images/tira-io-tira-host-$(VERSION).tar

clean:
	rm -r $(VENV_NAME)
	rm -r $(PROTO_OUT_PATH)