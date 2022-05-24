.PHONY: help setup run-develop build-docker clean

VENV_NAME?=venv
PYTHON=${VENV_NAME}/bin/python3
VERSION_APPLICATION=0.0.12
VERSION_GRPC=0.0.12


.DEFAULT: help
help:
	@echo "make setup"
	@echo "       setup venv, compile protobuf, give permissions to tira, and make migrations"
	@echo "make run-develop"
	@echo "       run server as tira user"
	@echo "make build-docker"
	@echo "       build the docker containers "
	@echo "make clean"
	@echo "       remove setup files"

setup:
	chmod +x setup.sh
	bash setup.sh
	chmod o+x src
	mkdir -p src/config
	make venv

# Requirements are in setup.py, so whenever setup.py is changed, re-run installation of dependencies.
venv:
	test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	sh -c ". $(VENV_NAME)/bin/activate && \
		python3 -m pip install wheel && \
		python3 -m pip install -r requirements.txt"

run-develop: venv
	cp config/tira-application-config.dev.yml src/config/settings.yml
	sh -c ". $(VENV_NAME)/bin/activate && \
	python3 src/manage.py run_develop"

run-docker:
	docker run -td --rm \
        --name=tira-application \
		-p 8080:80 \
		-v=/mnt/ceph/tira:/mnt/ceph/tira \
		webis/tira-application:${VERSION_APPLICATION}
	docker run -td --rm \
        --name=tira-application-grpc \
		-p 50052:50052 \
		-v=/mnt/ceph/tira:/mnt/ceph/tira \
		webis/tira-application-grpc:${VERSION_GRPC}

build-docker:
	docker build --tag webis/tira-application:${VERSION_APPLICATION} -f Dockerfile.application ..
	docker build --tag webis/tira-application-grpc:${VERSION_GRPC} -f Dockerfile.application-grpc ..

clean:
	rm -r $(VENV_NAME)