## Development Setup

The following steps will setup a self-contained, local tira application and a mockup tira host. See [Development](#development) for more detailed options. 

1. Install Python3, pip, virtualenv, yarn and the mysql tools. For Ubuntu:
   ```bash
   ~$ sudo apt-get update && sudo apt-get install python3 python3-pip python3-venv libmysqlclient-dev yarn npm
   ```

2. Setup the local environment
   ```bash
   ~$ make setup  # This creates the virtual environment and prepares Django's database
   ```

3. Initialize your development database from a database dump
   ```bash
   ~$ make import-data-from-dump
   ```

4. Setup the local environment
   ```bash
   ~$ make run-develop  # This updates the config and runs the server within the venv.
   ```

5. Run all unit tests
   ```bash
   ~$ make tests
   ```

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

### Run the tests

   ```bash
   application/src~$ python3 manage.py test test tira/tests/  # run all tests in application/src/tira/tests
   application/src~$ python3 manage.py test test tira/tests/tests.py  # run an individual test module
   ```

### Deploy on Kubernetes

- Add the discourse secret in the namespace via: `tira-host/src/tira_scripts/k8s-deploy-discourse-api-key.sh`

### Re-build the docker images: 

   ```bash
   protocol~$ make build  # Build the protobuf libraries from source. 
   ~$ make setup  # This creates the virtual environment and prepares Django's database
   ~$ make docker-build-tira-application  # Build the docker image (deploy mode with nginx)
   ~$ make docker-run-tira-application  # Run the docker container with the make command (deploy mode)
   ~$ make docker-publish-tira-application  # (optional) Publish a new version
   ```

These make targets from the deployment configuration: `tira/application/config/settings-deploy.yml`

### Development

The settings used for the development setup are: `tira/application/config/settings-dev.yml` 

Frequently used development commands are:

   ```bash
   application/src~$ python3 manage.py runserver 8080  # Start the application without any grpc server
   application/src~$ python3 manage.py grpc_server  # Start only the application's grpc server
   application/src~$ python3 manage.py run_develop  # Start the application and  the application's grpc server. This is used in make run-develop and the container
   application/src~$ python3 manage.py run_mockup  # Start the application, the application's grpc server, and a mock host grpc server that will reply to the application with fake commands. This is the simplest way to develop the application.
   ```

### Frontend Development

Build the frontend code via `make vite`

## Troubleshooting

If there are problems with the precompiled protobuf parser, you can recompile them from the `tira/protocol` repository and copy them to `tira/application/src/tira/proto`. 

If you run into `django.db.utils.OperationalError: (1050, "Table <xy> already exists")`, skip migrations using `./venv/bin/python3 src/manage.py migrate --fake` .

Windows users using WSL: If you run into `setup.sh: line 3: $'\r'`: command not found' when executing make setup:
   1. run `sudo apt-get install dos2unix`
   2. run `dos2unix setup.sh`
   3. run `cd tests && dos2unix setup.sh`
   4. Now make setup should work

   Error running vite-dev: `00h00m00s 0/0: : ERROR: [Errno 2] No such file or directory: 'install'`:
    run `apt remove cmdtest
   sudo apt remove yarn
   curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
   echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
   sudo apt-get update
   sudo apt-get install yarn -y`
