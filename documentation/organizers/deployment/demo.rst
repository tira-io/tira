Demo Deployment
===============

.. todo:: This documentation is still a stub and represents a target state; that is, it does not work yet.

.. code:: yaml

    version: "3.8"
    services:
        tira-backend:
            image: ghcr.io/tira-io/tira-backend
            restart: unless-stopped
        tira-frontend:
            image: ghcr.io/tira-io/tira-frontend
            restart: unless-stopped
            environment:
                TIRA_REST_BASE_URL: https://api.tira.local
                TIRA_GRPC_BASE_URL: https://api.tira.local
        auth:
            image: ghcr.io/authelia/authelia
            restart: unless-stopped
            volumes:
                - ./authelia/configuration.dev.yml:/config/configuration.yml
                - ./authelia/users-database.yml:/config/users_database.yml
        nginx:
            image: ghcr
            ports:
                - "8080:80"
            volumes:
                - ./nginx/tira.conf:/config/nginx/site-confs/tira.conf
                - ./nginx/tira-backend.conf:/config/nginx/site-confs/tira-backend.conf
                - ./nginx/auth.conf:/config/nginx/site-confs/auth.conf
                - ./nginx/snippets/:/config/nginx/snippets/
                - ./nginx/certs/:/etc/nginx/certs/


And add the following entries to your hosts file:

.. code::

    127.0.0.1   www.tira.local
    127.0.0.1   api.tira.local
    127.0.0.1   auth.tira.local

.. hint:: On Linux and MacOS you can find the hosts file under ``/etc/hosts``.


.. umlet-figure:: ../../development/images/architecturestack.uxf

    The architecture of TIRA's deployment. For the demo deployment we use nginx and Authelia, which are replaced with
    Discourse and Disraptor for production. The reverse proxy delegates authentication to the authentication provider
    and adds trusted header fields to the requests to TIRA's backend and frontend.