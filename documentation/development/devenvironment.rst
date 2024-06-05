.. _DevEnvPage:

Development Environment
=======================

.. epigraph::

    The right amount of complexity is what creates the optimal simplicity.

    -- David Allen


Requirements
------------
TIRA's development has at most two requirements: `VSCode <https://code.visualstudio.com/>`_ (with the
`Dev Containers <https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers>`_ extension)
and `Docker <https://www.docker.com/>`_. Please follow their respective installation guides before proceeding **OR**
you can use GitHub Codespaces by visiting the `TIRA repository <https://github.com/tira-io/tira/>`_ and clicking on
:menuselection:`Code --> Codespaces`.

.. todo:: GitHub Codespaces are not currently supported.

Getting Started
---------------
Open the repository in GitHub Codespaces or VSCode. If you are using VSCode, a dialog (depicted below) should pop up
asking if you want to open the repository in a development container -- click ``Reopen in Container``.

.. image:: images/open-in-container.png
    :align: center

Thats all for the environment! With the magic of Docker, all dependencies will now be installed and won't clutter your
main operating system.

The only thing remaining is to start the services and access TIRA. Open two shells, one in ``application`` and the other
in ``frontend``. To start the backend ("application"), run ``make run-develop`` and for the frontend: ``yarn dev``. Both
shells should tell you that their respective service is running. Now visit `<https://127.0.0.1:8082/>`_ in your browser
and you should see TIRA. To log in, perform an action that requires you to be logged in (e.g., submitting to one of the
tasks like `<https://127.0.0.1:8082/task-overview/task_1/>`_). You can find the credentials in :ref:`Tbl Credentials`
below. Note that the login and authentication is not actually performed by TIRA but by a separate "authentication
provider". In case of the development environment, this is done by `Authelia <https://www.authelia.com/>`_ and for the
production deployment by `Discourse <https://www.discourse.org/>`_. You are logged in now and should see a new menu when
trying to submit again.

.. attention:: You may have noticed that the ports described in this guide **do not** coincide with the ports listened
  to by the frontend and backend. For example, the frontend actually runs on the port 3000 but *must* be accessed via
  port 8082. To understand why, please read the section describing the `development infrastructure
  <#the-development-infrastructure>`_.


Debugging
---------
You don't actually need to launch TIRA's frontend and backend via the shell but can use our "Run and Debug"
configuration instead. To access it, press :kbd:`Ctrl+Shift+D` (:kbd:`Cmd+Shift+D` for MacOS). And select ``TIRA Stack``
from the debug side-bar that opened:

.. image:: images/debug-bar.png
    :align: center
    :width: 250pt

Now you can just press :kbd:`F5` every time to run and debug both, the frontend and backend. If an error occurs in any
of the two, VSCode will pause the execution, show you where the error happened and lets you step through the stackframes
and local variables.


The Development Infrastructure
------------------------------
The development environment is quite similar to the production environment and consists of 3 services:

- **The development environment**

  You are here when you open the repository in a development container.
- **The authentication provider** (Authelia)

  In production the authentication is performed with forward authentication using trusted headers by Disraptor as a
  reverse proxy and Discourse as the authentication provider. Authelia replaces Discourse for the development
  environment.
- **The reverse proxy** (nginx)

  This replaces Disraptor as the reverse proxy that redirects authentication to the auth provider (Discourse /
  Authelia). The reverse proxy also relays TIRA's frontend and backend to mimick the production environment.

  .. attention:: While TIRA's frontend and backend run on the same host (the development environment) within the
    development environment, this may **not** be the case in production. Instead, all communication should be routed
    through the reverse proxy. Otherwise, your code will not run in production and likely not in development since the
    reverse proxy handles login and authorization.

.. umlet-figure:: images/devenv.uxf

Lookup Tables for Useful Information
-----------------------------------
Root Password
~~~~~~~~~~~~~
You may occasionally need root privileges in the development container. The password for the root user is ``1234`` (if
it is such a popular choice, it must be because it is a secure password).

Demo Users
~~~~~~~~~~
By default the authentication provider in the development environment is set up with these user accounts (see also:
``.devfiles/authelia/users-database.yml``):

.. _Tbl Credentials:
.. table:: Demo Users

  +-----------+----------+-----------------------+
  |Username   | Password |        Roles          |
  +===========+==========+=======================+
  |admin      | password | admins, tira_reviewer |
  +-----------+----------+-----------------------+
  |organizer1 | password | --                    |
  +-----------+----------+-----------------------+
  |organizer2 | password | --                    |
  +-----------+----------+-----------------------+
  |user1      | password | --                    |
  +-----------+----------+-----------------------+
  |user2      | password | --                    |
  +-----------+----------+-----------------------+


Network Ports
~~~~~~~~~~~~~
The reverse proxy serves each service in the development environment on a different port. The mapping is as follows:

=======================  ======================
        Service                  Address       
=======================  ======================
Authentication Provider  https://127.0.0.1:8081
TIRA Frontend            https://127.0.0.1:8082
TIRA Backend             https://127.0.0.1:8080
=======================  ======================

.. attention:: The reverse proxy only serves ``https``. Your browser should tell you that it does not trust the
    certificate. This happens since we self-signed the certificate used by the development deployment. You can tell your
    browser to connect anyway.

.. note:: If you can not connect to a service or it tells you that there was a protocol error or similar, check the
    ports forwarded by VSCode. If you find that VSCode forwards any of the ports from the table above, **remove** them.
    The reverse proxy should do the forwarding.