.PHONY: help setup run-dev clean

VENV_NAME?=venv
PYTHON=${VENV_NAME}/bin/python3
SRC_DIR=../tira-protocol/src
#PYTHON_DEST=${VENV_NAME}/lib/python3.7/site-packages
BUILD_PATH=src/tira/proto
VERSION=0.0.7


.DEFAULT: help
help:
	@echo "make setup"
	@echo "       setup venv, compile protobuf, give permissions to tira, and make migrations"
	@echo "make run-dev"
	@echo "       run server as tira user"
	@echo "make clean"
	@echo "       remove setup files"

setup:
	chmod o+x src
	mkdir -p $(BUILD_PATH)
	mkdir -p src/config
	cp config/settings-dev.yml src/config/settings.yml
	make venv
	make local-migrations

# Requirements are in setup.py, so whenever setup.py is changed, re-run installation of dependencies.
venv:
	test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	sh -c ". $(VENV_NAME)/bin/activate && \
		python3 -m pip install -r requirements.txt"

# Better use the make in tira-protocol
protobuf: venv
	protoc -I=$(SRC_DIR) --python_out=$(BUILD_PATH) $(SRC_DIR)/tira_to_web.proto
	protoc -I=$(SRC_DIR) --python_out=$(BUILD_PATH) $(SRC_DIR)/tira_messages.proto
	protoc -I=$(SRC_DIR) --python_out=$(BUILD_PATH) $(SRC_DIR)/TiraClientWebMessages.proto
	${PYTHON} -m grpc_tools.protoc -I=$(SRC_DIR) --grpc_python_out=$(BUILD_PATH) tira_to_web.proto
	${PYTHON} -m grpc_tools.protoc -I=$(SRC_DIR) --python_out=$(BUILD_PATH) --grpc_python_out=$(BUILD_PATH) tira_host.proto
	sed -i 's/import tira_host_pb2 as tira__host__pb2/from . import tira_host_pb2 as tira__host__pb2/g' $(BUILD_PATH)/tira_host_pb2_grpc.py
	touch $(BUILD_PATH)/__init__.py

local-migrations:
	cp config/settings-dev.yml src/config/settings.yml
	sh -c ". $(VENV_NAME)/bin/activate && \
	python3 src/manage.py makemigrations && \
	python3 src/manage.py migrate"

deployment-migrations:
	cp config/settings-deploy.yml src/config/settings.yml
	sh -c ". $(VENV_NAME)/bin/activate && \
	python3 src/manage.py makemigrations && \
	python3 src/manage.py migrate"

run-dev:
	cp config/settings-dev.yml src/config/settings.yml
	sh -c ". $(VENV_NAME)/bin/activate && \
	python3 src/manage.py runserver 8080"

run-wsgi:
	su tira -c". $(VENV_NAME)/bin/activate && \
	uwsgi --ini src/uwsgi.ini"

clean:
	rm -r $(VENV_NAME)
	rm -r $(BUILD_PATH)

k8s-deploy-tira-application: k8s-undeploy-tira-application
	kubectl -n webisservices create configmap tira-web2-config --from-file=config/settings-deploy.yml
	kubectl -n webisservices apply -f tira-application.yml

k8s-undeploy-tira-application:
	kubectl -n webisservices delete -f tira-application.yml || echo "already undeployed?"
	kubectl -n webisservices delete configmap tira-web2-config || echo "no configmap?"

docker-publish-tira-application: docker-build-tira-application
	docker login &&\
	docker push webis/tira-web-2:${VERSION} &&\
	docker tag webis/tira-web-2:${VERSION} webis/tira-web-2:latest &&\
	docker push webis/tira-web-2:latest

docker-build-tira-application-grpc:
	docker build --tag webis/tira-application-grpc:${VERSION} -f tira-application-grpc.Dockerfile ..

docker-run-tira-application:
	docker run -ti --rm \
        --name=tira-application \
		-p 8080:80 \
		-v=/mnt/ceph/tira:/mnt/ceph/tira \
		webis/tira-web-2:${VERSION}

docker-run-tira-application-grpc:
	docker run -ti --rm \
        --name=tira-application-grpc \
		-p 50052:50052 \
		-v=/mnt/ceph/tira:/mnt/ceph/tira \
		webis/tira-application-grpc:${VERSION}

docker-build-tira-application:
	docker build --tag webis/tira-web-2:${VERSION} -f Dockerfile ..


docker-build-and-push-to-webis-registry: docker-build-tira-application
	docker tag webis/tira-web-2:${VERSION} registry.webis.de/code-lib/public-images/tira-application:${VERSION}
	docker login registry.webis.de
	docker push registry.webis.de/code-lib/public-images/tira-application:${VERSION}
	docker tag webis/tira-web-2:${VERSION} registry.webis.de/code-lib/public-images/tira-application:latest
	docker push registry.webis.de/code-lib/public-images/tira-application:latest

docker-build-and-push-to-webis-registry-grpc: docker-build-tira-application-grpc
	docker tag webis/tira-application-grpc:${VERSION} registry.webis.de/code-lib/public-images/tira-application-grpc:${VERSION}
	docker login registry.webis.de
	docker push registry.webis.de/code-lib/public-images/tira-application-grpc:${VERSION}
