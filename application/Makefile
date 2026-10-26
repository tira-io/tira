.PHONY: help setup run-develop tests build-docker clean

VERSION_APPLICATION=0.0.105

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
	s3cmd mb s3://tira-mirrored-resources || echo "already exists"
	python3 src/manage.py makemigrations
	python3 src/manage.py migrate
	python3 src/manage.py createcachetable
	python3 src/manage.py makemigrations tira
	python3 src/manage.py migrate tira 
	python3 src/manage.py index_model

# Runs the backend test suite (application/test) in a throwaway container based on the devcontainer
# base image (webis/tira:dev-container-0.0.2, see ../.devcontainer/Dockerfile-base.dev), which already
# bakes in the Python [test,dev] extras and TIRA_ROOT/TIRA_CONFIG env vars, so we only need to
# re-link the package in editable mode (--no-deps, no network access needed), prepare the database
# (make setup), and run pytest -- mirroring .github/workflows/tests.yml.
#
# The repository is streamed into the container via a tar pipe (instead of a bind mount) and
# extracted into the container's own writable layer: stray root-owned build artifacts (egg-info,
# __pycache__, node_modules, ...) that may exist on the host would otherwise make `pip install -e .`
# fail with "Cannot update time stamp of directory ..." since the container user cannot touch them
# through a bind mount; these are also excluded from the tar stream so reading them never requires
# elevated host permissions in the first place. `make clean` removes the sqlite3/admin.prototext
# fixtures carried over in the tar stream, so `index_model` starts from a fresh database instead of
# colliding with an already-indexed admin VM.
tests:
	tar -C .. --exclude=.git --exclude=__pycache__ --exclude='*.egg-info' --exclude=node_modules -cf - . | \
		docker run --rm -i --user root -w /workspaces/tira/application \
		webis/tira:dev-container-0.0.2 \
		bash -lc "mkdir -p /workspaces/tira && tar -xf - -C /workspaces/tira && cd /workspaces/tira/application \
			&& echo -e '\ntira_s3_config:\n  s3_bucket: none' >> ./config/tira-application-config.yml \
			&& touch ~/.s3cfg && pip install --no-deps -e . && make clean && make setup && cd test && pytest"

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

build-docker:
	docker build --tag webis/tira-application:${VERSION_APPLICATION} -f Dockerfile.application ..

build-docker-all: build-docker
	docker build --tag webis/tira-application:${VERSION_APPLICATION}-diffir-base -f Dockerfile.application-diffir-base ..
	docker build --tag webis/tira-application:${VERSION_APPLICATION}-diffir -f Dockerfile.application-diffir ..
	docker build --tag webis/tira-ir-datasets-starter:${VERSION_APPLICATION}-jupyter -f Dockerfile.application_ir_datasets_jupyter ..

docker-publish:
	docker push webis/tira-application:basis-${VERSION_APPLICATION}
	docker push webis/tira-application:${VERSION_APPLICATION}
	docker push webis/tira-application:${VERSION_APPLICATION}-diffir-base
	docker push webis/tira-application:${VERSION_APPLICATION}-diffir
	docker tag webis/tira-application:${VERSION_APPLICATION}-diffir webis/tira-ir-datasets-starter:${VERSION_APPLICATION}
	docker push webis/tira-ir-datasets-starter:${VERSION_APPLICATION}

build-docker-basis:
	docker build --tag webis/tira-application:basis-${VERSION_APPLICATION} -f Dockerfile.basis ..

