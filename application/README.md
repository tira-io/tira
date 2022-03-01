## Local Development

The following steps will setup a local tira-application and tira-application-grpc. By default, it uses tira/model which comes with this repo. 

0. Install Protobuf and compile the tira protocol. Install Python3, pip, and virtualenv
   ```bash
   protocol~$ make build
                ~$ sudo apt-get update && sudo apt-get install python3 python3-pip python3-venv 
   ```

1. Setup the local environment
   ```bash
   ~$ make setup  # This creates the virtual environment and prepares Django's database
   ```

2. Setup the local environment
   ```bash
   ~$ make run-develop  # This updates the config and runs the server within the venv.
   ```

## Docker

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

These make targets the the deployment configuration: `tira/application/config/settings-deploy.yml`

### Development

The settings used for this local deployment are: `tira/application/config/settings-dev.yml` 

Frequently used development commands are:

   ```bash
   application/src~$ python3 manage.py runserver 8080  # Start the application without any grpc server
   application/src~$ python3 manage.py grpc_server  # Start only the application's grpc server
   application/src~$ python3 manage.py run_develop  # Start the application and  the application's grpc server. This is used in make run-develop and the container
   application/src~$ python3 manage.py run_mockup  # Start the application, the application's grpc server, and a mock host grpc server that will reply to the application with fake commands. This is the simplest way to develop the application.
   ```  
