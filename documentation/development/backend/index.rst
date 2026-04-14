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

    - Start the application
    
    .. code:: bash
        
        application/src~$ python3 manage.py runserver 8080

    - Start the application. This is used in make run-develop and the container (by now, this is redundant with runserver right?) TODO
    
    .. code:: bash

        application/src~$ python3 manage.py run_develop

