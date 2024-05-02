Deploying the Application Module
================================

Development Setup
-----------------
The following steps will setup a self-contained, local tira application and a mockup tira host. See `Development`_ for
more detailed options. 

.. code:: bash

    # Install Python3, pip and virtualenv
    sudo apt-get update && \
        sudo apt-get install python3 python3-pip python3-venv libmysqlclient-dev
    # Setup the local environment
    make setup  # This creates the virtual environment and prepares Django's database
    # Setup the local environment
    make run-develop  # This updates the config and runs the server within the venv.

Docker
------
You can run tira in a docker container for a simple deployment. 

You need to run two docker containers for a tira-application:

- :code:`registry.webis.de/code-lib/public-images/tira-application` and
- :code:`registry.webis.de/code-lib/public-images/tira-application-grpc`.

.. code:: bash

   ~$ docker run -d --rm --name=tira-application \
		 -p 8080:80 \
		 -v="</path/to/model>":/mnt/ceph/tira \
		 registry.webis.de/code-lib/public-images/tira-application:latest

   ~$ docker run -d --rm --name=tira-application-grpc \
		-p 50052:50052 \
		 -v="</path/to/model>":/mnt/ceph/tira \
		 registry.webis.de/code-lib/public-images/tira-application-grpc:latest

Use TIRA with Discourse via Disraptor (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you set up Discourse with `Disraptor <https://www.disraptor.org>`_, this will be useful information on how to
make TIRA work with it.

(1) Since TIRA has a legacy and a Disraptor :code:`deployment` mode first change that to :code:`disraptor` in the
    development config file :code:`application/config/tira-application-config.dev.yml`.
(2) When you set up Disraptor you set a :code:`Disraptor App Secret Key` that allows Disraptor to communicate with your
    web application. Since TIRA has to evaluate that this secret is correct we have to supply it to it. TIRA expects
    that secret in an environment variable called :code:`DISRAPTOR_APP_SECRET_KEY`, so before starting your development
    TIRA environment with :code:`make run-develop` or :code:`make run-git-develop` always remember to
    :code:`export DISRAPTOR_APP_SECRET_KEY=<your-secret-key>`.
(3) Lastly, of course, Disraptor has to be supplied with the routes for TIRA at :code:`Settings > Plugins > Disraptor`.
    Since routes may change in the future and depending on what you want to test you maybe do no need the full set of
    routes arranged it is recommended to take a look at :code:`application/src/tira/urls.py`.  Here is an example of
    what can be used to have access to most of the **current** TIRA:

    ========================== =============================================== ========
    From                       To                                              Method 
    ========================== =============================================== ========
    `/public/tira/*wildcard`   `http://127.0.0.1:8080/public/tira/*wildcard`   GET    
    `/task/*wildcard`          `http://127.0.0.1:8080/task/*wildcard`          GET    
    `/task/*wildcard`          `http://127.0.0.1:8080/task/*wildcard`          POST   
    `/api/*wildcard`           `http://127.0.0.1:8080/api/*wildcard`           GET    
    `/tira-admin`              `http://127.0.0.1:8080/tira-admin`              GET    
    `/tira-admin/*wildcard`    `http://127.0.0.1:8080/tira-admin/*wildcard`    GET    
    `/tira-admin/*wildcard`    `http://127.0.0.1:8080/tira-admin/*wildcard`    POST   
    `/static/*wildcard`        `http://127.0.0.1:8080/static/*wildcard`        GET    
    `/grpc/*wildcard`          `http://127.0.0.1:8080/grpc/*wildcard`          GET    
    `/grpc/*wildcard`          `http://127.0.0.1:8080/grpc/*wildcard`          POST   
    `/tasks`                   `http://127.0.0.1:8080/`                        GET    
    `/tira/static/*wildcard`   `http://127.0.0.1:8080/tira/static/*wildcard`   GET    
    ========================== =============================================== ========

    .. note::
        Let's say route A gets added here first and then route B. Rails will evaluate them from latest to earliest. So
        when checking for a destination Rails will first look if route B matches before it checks route A and so on.
        This can lead to states where you might see unexpected behavior if your routes (namely these with wildcards)
        have interseting "To"-pools.
    .. note::
        Sometimes Rails does not instantly take in new routes so when adding new routes you might want to restart the
        Rails server.

Build and Deploy
----------------
Run the tests
~~~~~~~~~~~~~
.. code:: bash

    # run all tests in application/src/tira/tests
    application/src~$ python3 manage.py test test tira/tests/
    # run an individual test module
    application/src~$ python3 manage.py test test tira/tests/tests.py

Deploy on Kubernetes
~~~~~~~~~~~~~~~~~~~~
.. todo:: This step is deprecated and the documentation must be updated

Add the discourse secret in the namespace via:

.. code:: bash

    ??? TODO?

Re-build the docker images 
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    # Build the protobuf libraries from source.
    make build
    # This creates the virtual environment and prepares Django's database
    make setup
    # Build the docker image (deploy mode with nginx)
    make docker-build-tira-application
    # Run the docker container with the make command (deploy mode)
    make docker-run-tira-application
    # (optional) Publish a new version
    make docker-publish-tira-application

These make targets from the deployment configuration: :code:`tira/application/config/settings-deploy.yml`.

Development
~~~~~~~~~~~
The settings used for the development setup are: :code:`tira/application/config/settings-dev.yml`.

Frequently used development commands are:

- Start the application without any grpc server
  
  .. code:: bash
    
    application/src~$ python3 manage.py runserver 8080

- Start only the application's grpc server
  
  .. code:: bash

    application/src~$ python3 manage.py grpc_server

- Start the application and  the application's grpc server. This is used in make run-develop and the container
  
  .. code:: bash

    application/src~$ python3 manage.py run_develop

- Start the application, the application's grpc server, and a mock host grpc server that will reply to the application
  with fake commands. This is the simplest way to develop the application.
  
  .. code:: bash

    application/src~$ python3 manage.py run_mockup

Troubleshooting
---------------
If there are problems with the precompiled protobuf parser, you can recompile them from the :code:`tira/protocol`
repository and copy them to :code:`tira/application/src/tira/proto`. 

Setup on MacOS (Monterey/M1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. attention::
    This part of the documentation is experimental and may not work for everyone.
.. note::
    We will assume that `brew <https://brew.sh/>`_ is installed.

(1) Install required software

    .. code:: bash

        brew install python@3.10 pipenv pyvenv mariadb uwsgi
(2) Inside :code:`tira/application/config/tira-application-config.dev.yml` change :code:`tira_root` to the model you
    want to use.
(3) From within :code:`tira/application` execute the makefile at least once. This copies the config and runs
    :code:`manage.py index_model` once.

    .. code:: bash

        make setup
    .. note::
        If above command did not work, you may try to build the venv and install the requirements manually by executing
        the following commands within :code:`tira/application`

        .. code:: bash

            python3.10 -m venv venv
            source venv/bin/activat
            pip install -r requirements.txt
