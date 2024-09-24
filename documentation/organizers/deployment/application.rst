Deploying the Backend
=====================

.. important:: TIRA makes greate use of the internet forum tool `Discourse <https://www.discourse.org/>`_. Before you
               continue, please set up a Discourse instance and install the reverse proxy plugin
               `Disraptor <https://www.disraptor.org>`_.

The TIRA backend is entirely contained within the official docker image,
`ghcr.io/tira-io/tira-backend:latest <https://github.com/tira-io/tira/pkgs/container/tira-backend>`_. To see, what a
deployment using this container can look like, please have a look at our
:bdg-ref-secondary:`demo deployment <demo_deployment>`.

Configuring TIRA
----------------
TIRA can be configured using two ways (non-exclusive):

(1) Environment variables
(2) A configuration file

To kill two birds with one stone (only figuratively speaking), we refer you to the fully documented default
configuration file (below). Any value of the form ``!ENV ${<name>:<value>}`` indicates that the value is read from the
environment variable ``<name>`` and, if that environment variable does not exist, the default value, ``<value>`` is
assigned. This means, that, to set TIRA into debug mode, for example, you have two options:

(1) The line ``debug: !ENV ${TIRA_DEBUG:false}`` tells us that, per default, the debug mode is disabled but we can
    enable it by setting the environment variable ``TIRA_DEBUG`` to ``true``.
(2) Copy the default configuration, replace ``debug: !ENV ${TIRA_DEBUG:false}`` with ``debug: true`` and map the new   
    configuration file into your container to ``/tira/config/tira-application-config.yml`` (this location can be
    changed using the ``TIRA_CONFIG`` environment variable).

.. literalinclude:: ../../../application/config/tira-application-config.yml
    :language: yaml
    :caption: TIRA's default configuration

.. attention:: Some of these configuration parameters are **secrets** and should stay *secret*. Do not use their
               default values for production and use `Docker secrets <https://docs.docker.com/engine/swarm/secrets/>`_
               to set them.


Endpoints
---------
Lastly, of course, Disraptor has to be supplied with the routes for TIRA at :code:`Settings > Plugins > Disraptor`.
Since routes may change in the future and depending on what you want to test you maybe do no need the full set of
routes arranged it is recommended to take a look at :code:`application/src/tira/urls.py`. Here is an example of
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
`/health`                  `http://127.0.0.1:8080/health`                  GET    
`/info`                    `http://127.0.0.1:8080/info`                    GET
`/v1/*wildcard`            `http://127.0.0.1:8080/v1/*wildcard`            GET
`/v1/*wildcard`            `http://127.0.0.1:8080/v1/*wildcard`            POST
`/v1/*wildcard`            `http://127.0.0.1:8080/v1/*wildcard`            DELETE
`/v1/*wildcard`            `http://127.0.0.1:8080/v1/*wildcard`            UPDATE
========================== =============================================== ========

.. important:: Routes that were added later take precedence over those added before when multiple rules match.
.. hint:: You may need to restart the Rails server to apply your changes.
