.PHONY: help setup setup-webpack webpack run-develop build-docker clean

VENV_NAME?=venv
PYTHON=${VENV_NAME}/bin/python3
VERSION_APPLICATION=0.0.26
VERSION_GRPC=0.0.26


.DEFAULT: help
help:
	@echo "make setup"
	@echo "       setup venv, compile protobuf, give permissions to tira, and make migrations"
	@echo "make run-develop"
	@echo "       run server as tira user"
	@echo "make run-git-develop"
	@echo "       run git-runner-script in development mode"
	@echo "make build-docker"
	@echo "       build the docker containers "
	@echo "make clean"
	@echo "       remove setup files"

setup:
	chmod +x setup.sh
	bash setup.sh
	chmod o+x src
	test -d $(VENV_NAME) || mkdir -p src/config/
	cp config/tira-application-config.dev.yml src/config/settings.yml
	make venv
	make webpack
	sh -c ". $(VENV_NAME)/bin/activate && \
	python3 src/manage.py index_model && \
	python3 src/manage.py createcachetable"

#setup-webpack:
#    npm add vue@next webpack-bundle-tracker@0.4.3 uikit; \
#    npm add --dev vue-loader@v16.8.2 webpack-cli webpack webpack-dev-server typescript ts-loader @vue/compiler-sfc style-loader css-loader

webpack:
	cd ./src/tira/frontend/; \
	npm install; \
	npm run build

webpack-watch:
	cd ./src/tira/frontend/;\
	npm install; \
	npm run plain


# Requirements are in setup.py, so whenever setup.py is changed, re-run installation of dependencies.
venv:
	test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	sh -c ". $(VENV_NAME)/bin/activate && \
		python3 -m pip install wheel && \
		python3 -m pip install -r requirements.txt"

run-develop: venv
	$(VENV_NAME)/bin/python3 src/manage.py run_develop

run-git-develop: venv
	cat config/tira-application-config.dev.yml |grep -v '^GIT_' > src/config/settings.yml
	kubectl -n services-tira get configmap tira-application-test-config -o json| jq --raw-output '.data."settings-test.yml"'|grep '^GIT_' >> src/config/settings.yml
	sh -c ". $(VENV_NAME)/bin/activate && cd src &&\
		python3 manage.py git_runner_cli"
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

docker-publish:
	docker push webis/tira-application:basis-${VERSION_APPLICATION}
	docker push webis/tira-application:${VERSION_APPLICATION}
	docker push webis/tira-application-grpc:${VERSION_GRPC}

build-docker-basis:
	docker build --tag webis/tira-application:basis-${VERSION_APPLICATION} -f Dockerfile.basis ..

clean:
	rm -r $(VENV_NAME)

forward-mysql:
	kubectl -n services-tira port-forward $$(kubectl -n services-tira get pods| grep tira-mariadb | awk '{print $$1 }') 3306
