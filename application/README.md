# The TIRA Application

The backend server and frontend of the TIRA application.

## Development Setup

We use devcontainers for development. To start your environment, either use Github Codespaces (click on "Code" -> "Codespaces" in Github to open one) as easiest way to get started, or [devpod](https://github.com/loft-sh/devpod) as open source alternative (directly pointing to our Kubernetes or your local docker installation).

Run `make` to get an overview of all commands that will setup a self-contained tira application in your dev environment.

1. Setup the database and compile the vuetify frontend
   ```bash
   ~$ make setup
   ```

2. Start the local environment, point your browser to the specified URL
   ```bash
   ~$ make run-develop
   ```

3. Optionally: To work on real data, initialize your development database from a database dump
   ```bash
   ~$ make import-data-from-dump
   ```

4. Optionally: Change the configuration (the settings used for the development setup are: `tira/application/config/settings-dev.yml`)


## Docker

You can run tira in a docker container for a simple deployment. 

You need to run two docker containers for a tira-application: `registry.webis.de/code-lib/public-images/tira-application` and `registry.webis.de/code-lib/public-images/tira-application-grpc`. 

   ```bash
   ~$ docker run -d --rm --name=tira-application \
		 -p 8080:80 \
		 -v=/path/to/model:/mnt/ceph/tira \
		 registry.webis.de/code-lib/public-images/tira-application:latest

   ~$ docker run -d --rm --name=tira-application-grpc \
		-p 50052:50052 \
		 -v=/path/to/model:/mnt/ceph/tira \
		 registry.webis.de/code-lib/public-images/tira-application-grpc:latest
   ```

## Build and Deploy

### Step 1: Run the tests

   ```bash
   make tests # run all tests (automatically done in Github Actions on each commit)
   ```

### Step 2: Re-build the docker images: 

   ```bash
   ~$ make build-docker
   ~$ make build-docker-all
   ```

These make targets from the deployment configuration: `tira/application/config/settings-deploy.yml`

### Step 3: Deploy on Kubernetes

- `code-admin-knowledge-base/services/tira/` contains all the deployment yamls.
- Add the discourse secret in the namespace via: `tira-host/src/tira_scripts/k8s-deploy-discourse-api-key.sh`
   (this part is entirely deprecated and should be updated)


## Create New Zip of the Database Dump

Go the the password database `webis.uni-weimar.de:code-admin/passwords` -> Generic -> tira-development-database-dump

```
cd /mnt/ceph/storage/data-in-production/tira/development-database-dumps/
zip --encrypt django-db-dump-<DATE>.zip /mnt/ceph/tira/state/db-backup/django-db-dump-<DATE>.json
ln -s django-db-dump-<DATE>.zip django-db-dump.zip
```

## Troubleshooting

If there are problems with the precompiled protobuf parser, you can recompile them from the `tira/protocol` repository and copy them to `tira/application/src/tira/proto`. 

If you run into `django.db.utils.OperationalError: (1050, "Table <xy> already exists")`, skip migrations using `./venv/bin/python3 src/manage.py migrate --fake` .
