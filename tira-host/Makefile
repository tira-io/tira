#		-v /home/tira:/home/tira \
# -v $PWD/src:/usr/lib/tira \

VENV_NAME?=venv
VENV_ACTIVATE=. $(VENV_NAME)/bin/activate
PYTHON=${VENV_NAME}/bin/python3
PROTO_INPUT_PATH=../tira-protocol/src
PROTO_OUT_PATH=src/tira_host/proto
VERSION=0.0.1
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

compile-protobuf: venv
	${PYTHON} -m grpc_tools.protoc -I=$(PROTO_INPUT_PATH) --python_out=$(PROTO_OUT_PATH) --grpc_python_out=$(PROTO_OUT_PATH) tira_host.proto
	sed -i 's/import tira_host_pb2 as tira__host__pb2/from proto import tira_host_pb2 as tira__host__pb2/g' $(PROTO_OUT_PATH)/tira_host_pb2_grpc.py
	touch $(PROTO_OUT_PATH)/__init__.py

clean:
	rm -r $(VENV_NAME)
	rm -r $(PROTO_OUT_PATH)