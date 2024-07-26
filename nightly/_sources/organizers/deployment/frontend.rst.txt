.. _frontend:

Deploying the Frontend
======================

The recommended way to deploy TIRA's frontend is Docker (or Docker Compose) using the official image, `ghcr.io/tira-io/tira-frontend:latest <https://github.com/tira-io/tira/pkgs/container/tira-frontend>`_.

The frontend is configured using the following environment variables:

+----------------------+----------------------------------------------------------------------------------------------+
| Environment Variable | Description                                                                                  |
+======================+==============================================================================================+
| TIRA_REST_BASE_URL   | The URL at which the backend's REST-API can be reached.                                      |
+----------------------+----------------------------------------------------------------------------------------------+
| TIRA_GRPC_BASE_URL   | The URL at which the backend's GRPC-API can be reached. `The GRPC URL only exists for legacy |
|                      | reasons and will be removed in the future. In the meantime, set TIRA_GRPC_BASE_URL to the    |
|                      | same value as TIRA_REST_BASE_URL.`                                                           |
+----------------------+----------------------------------------------------------------------------------------------+

The frontend configured in the official container is fixed to use **port 80**. Using Docker, you can, of course, remap it to any other port you prefer.

.. attention:: The frontend SHOULD be deployed behind a reverse proxy which delegates authentication using trusted headers. See :bdg-ref-secondary:`deployment` for more information on the deployment as a whole or :bdg-ref-secondary:`demo_deployment` for a stripped down example of a basic deployment for demo purposes.