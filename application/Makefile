.PHONY: help setup run-develop build-docker clean

VERSION_APPLICATION=0.0.105
VERSION_GRPC=0.0.105

PYTHON=python3

.DEFAULT: help
help:
	@echo "make setup"
	@echo "       setup your environment"
	@echo "make run-develop"
	@echo "       run the tira server"
	@echo "make tests"
	@echo "       run all tests (automatically done in Github Actions on each commit)"
	@echo "make build-docker"
	@echo "       build the docker containers for deployment"
	@echo "make clean"
	@echo "       clean the environment"

clean: 
	rm -f ../model/src/state/tira.sqlite3
	rm -f ../model/src/model/virtual-machines/admin.prototext

setup:
	s3cmd mb s3://tira-mirrored-resources
	python3 src/manage.py makemigrations
	python3 src/manage.py migrate
	python3 src/manage.py createcachetable
	python3 src/manage.py makemigrations tira
	python3 src/manage.py migrate tira 
	python3 src/manage.py index_model

run-develop:
	python3 src/manage.py makemigrations \
	&& python3 src/manage.py migrate --fake \
	&& python3 src/manage.py run_develop

.data-dumps/django-db-dump.zip:
	@mkdir -p .data-dumps && \
	echo "Please run scp <YOUR-USR-NAME>@ssh.webis.de:/mnt/ceph/storage/data-in-production/tira/development-database-dumps/django-db-dump.zip .data-dumps/" && \
	exit 1

import-data-from-dump: .data-dumps/django-db-dump.zip
	@rm -f ../model/src/state/tira.sqlite3 && \
	rm -f ../model/src/model/virtual-machines/admin.prototext && \
	cd .data-dumps/ && \
	rm -f *.json && \
	echo "Please use the generic > tira-db-dump password from git@webis.uni-weimar.de:code-admin/passwords.git" && \
	unzip -j django-db-dump.zip && \
	mv *.json django-db-dump-tmp.json && \
	head -n -1 django-db-dump-tmp.json > django-db-dump.json && \
	echo ', {"model": "tira.dataset", "pk": "none", "fields": {"default_task": null, "display_name": "", "evaluator": null, "is_confidential": true, "is_deprecated": false, "data_server": null, "released": "", "default_upload_name": "predictions", "created": "2022-08-11", "last_modified": "2022-08-11", "irds_docker_image": null, "irds_import_command": null, "irds_import_truth_command": null}}]' >> django-db-dump.json && \
	rm django-db-dump-tmp.json && \
	cd .. && \
	${PYTHON} src/manage.py migrate && \
	${PYTHON} src/manage.py createcachetable && \
	${PYTHON} src/manage.py makemigrations tira && \
	${PYTHON} src/manage.py migrate tira && \
	${PYTHON} src/manage.py loaddata .data-dumps/django-db-dump.json

import-mock-data:
	${PYTHON} src/manage.py loaddata mock-data/mock-data.json

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

build-docker-all: build-docker
	docker build --tag webis/tira-application:${VERSION_APPLICATION}-diffir-base -f Dockerfile.application-diffir-base ..
	docker build --tag webis/tira-application:${VERSION_APPLICATION}-diffir -f Dockerfile.application-diffir ..
	docker build --tag webis/tira-application-grpc:${VERSION_GRPC} -f Dockerfile.application-grpc ..
	docker build --tag webis/tira-ir-datasets-starter:${VERSION_APPLICATION}-jupyter -f Dockerfile.application_ir_datasets_jupyter ..

docker-publish:
	docker push webis/tira-application:basis-${VERSION_APPLICATION}
	docker push webis/tira-application:${VERSION_APPLICATION}
	docker push webis/tira-application:${VERSION_APPLICATION}-diffir-base
	docker push webis/tira-application:${VERSION_APPLICATION}-diffir
	docker tag webis/tira-application:${VERSION_APPLICATION}-diffir webis/tira-ir-datasets-starter:${VERSION_APPLICATION}
	docker push webis/tira-ir-datasets-starter:${VERSION_APPLICATION}
	docker push webis/tira-application-grpc:${VERSION_GRPC}

build-docker-basis:
	docker build --tag webis/tira-application:basis-${VERSION_APPLICATION} -f Dockerfile.basis ..

