Backend Development
====================

Getting Started
---------------
To get started, please read and follow the instructions of the :ref:`DevEnvPage` section.

Code Testing
------------
Open a shell within the ``application`` directory and run

.. code:: bash
    
    make tests

Linting
-------

.. todo:: We don't currently have any linters

FAQ
---

Yay, no questions yet.




.. This was copied over from the deployment documentation and should be worked into the development documentation instead
    Development
    ~~~~~~~~~~~
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
