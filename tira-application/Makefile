.PHONY: help setup run-develop k8s-deploy-tira-application docker-publish-tira-application clean

VENV_NAME?=venv
PYTHON=${VENV_NAME}/bin/python3
GRPC_SRC_DIR=../tira-protocol/src
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
	! test -d $(GRPC_SRC_DIR) || { echo "please compile the protocol files first. See the docs in tira/tira-protocol"; exit 1; }
	chmod o+x src
	mkdir -p $(BUILD_PATH)
	cp $(GRPC_SRC_DIR)/* $(BUILD_PATH)/
	mkdir -p src/config
	make venv

# Requirements are in setup.py, so whenever setup.py is changed, re-run installation of dependencies.
venv:
	test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	sh -c ". $(VENV_NAME)/bin/activate && \
		python3 -m pip install -r requirements.txt"

run-develop: venv
	cp config/settings-dev.yml src/config/settings.yml
	sh -c ". $(VENV_NAME)/bin/activate && \
	python3 src/manage.py run_develop"

docker-run-tira-application:
	docker run -td --rm \
        --name=tira-application \
		-p 8080:80 \
		-v=/mnt/ceph/tira:/mnt/ceph/tira \
		webis/tira-web-2:${VERSION}
	docker run -td --rm \
        --name=tira-application-grpc \
		-p 50052:50052 \
		-v=/mnt/ceph/tira:/mnt/ceph/tira \
		webis/tira-application-grpc:${VERSION}

docker-build-tira-application:
	docker build --tag webis/tira-web-2:${VERSION} -f Dockerfile.application ..
	docker build --tag webis/tira-application-grpc:${VERSION} -f Dockerfile.application-grpc ..

docker-publish-tira-application: docker-build-tira-application
	docker tag webis/tira-web-2:${VERSION} registry.webis.de/code-lib/public-images/tira-application:${VERSION}
	docker tag webis/tira-web-2:${VERSION} registry.webis.de/code-lib/public-images/tira-application:latest
	docker tag webis/tira-application-grpc:${VERSION} registry.webis.de/code-lib/public-images/tira-application-grpc:${VERSION}
	docker tag webis/tira-application-grpc:${VERSION} registry.webis.de/code-lib/public-images/tira-application-grpc:latest
	docker login registry.webis.de
	docker push registry.webis.de/code-lib/public-images/tira-application:latest
	docker push registry.webis.de/code-lib/public-images/tira-application:${VERSION}
	docker push registry.webis.de/code-lib/public-images/tira-application-grpc:${VERSION}

k8s-deploy-tira-application: k8s-undeploy-tira-application
	kubectl -n services-tira apply -f tira-application.yml

k8s-undeploy-tira-application:
	kubectl -n services-tira delete -f tira-application.yml || echo "already undeployed?"

clean:
	rm -r $(VENV_NAME)
	rm -r $(BUILD_PATH)
