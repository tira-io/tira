## Local Development

The following steps will setup a local tira-application and tira-application-grpc. By default, it uses tira/tira-model which comes with this repo. 

0. Install Protobuf and compile the tira protocol. Install Python3, pip, and virtualenv
   ```bash
   tira-protocol~$ make build
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
		 -v=/path/to/tira-model:/mnt/ceph/tira \
		 registry.webis.de/code-lib/public-images/tira-application:latest

   ~$ docker run -d --rm --name=tira-application-grpc \
		-p 50052:50052 \
		 -v=/path/to/tira-model:/mnt/ceph/tira \
		 registry.webis.de/code-lib/public-images/tira-application-grpc:latest
   ```  

## Build and Deploy

### Re-build the docker images: 

   ```bash
   tira-protocol~$ make build  # Build the protobuf libraries from source. 
   ~$ make setup  # This creates the virtual environment and prepares Django's database
   ~$ make docker-build-tira-application  # Build the docker image (deploy mode with nginx)
   ~$ make docker-run-tira-application  # Run the docker container with the make command (deploy mode)
   ~$ make docker-publish-tira-application  # (optional) Publish a new version
   ```  

These make targets the the deployment configuration: `tira/tira-application/config/settings-deploy.yml`

### Development

The settings used for this local deployment are: `tira/tira-application/config/settings-dev.yml` 

Frequently used development commands are:

   ```bash
   tira-application/src~$ python3 manage.py runserver 8080  # Start the application without any grpc server
   tira-application/src~$ python3 manage.py grpc_server  # Start only the application's grpc server
   tira-application/src~$ python3 manage.py run_develop  # Start the application and  the application's grpc server. This is used in make run-develop and the container
   tira-application/src~$ python3 manage.py run_mockup  # Start the application, the application's grpc server, and a mock host grpc server that will reply to the application with fake commands. This is the simplest way to develop the application.
   ```  
