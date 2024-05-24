.. _TIRACLIPage:

TIRA CLI
========

You don't always need to write code to interact with TIRA. For your convenience, we offer a handy command line interface (CLI) for quick and efficient interactions with the TIRA platform.

.. note:: This documentation is particularly discussing ``tira-cli`` and not the ``tira-run`` command. ``tira-run``
    should be viewed as legacy and we are committed to move the functionality over to ``tira-cli``.


Introduction
~~~~~~~~~~~~
The TIRA CLI is part of the TIRA client for Python. To install it, install the TIRA client using

.. code:: bash

    $ pip install tira

If everything worked, the CLI's help page should display the following:

.. code-block:: bash

    $ tira-cli --help
    usage: tira-cli [-h] {download,upload,login} ...

    positional arguments:
      {download,upload,login}
        download            Download runs or datasets from TIRA.io
        upload              Upload runs or datasets to TIRA.io
        login               Login your TIRA client to the tira server.

    options:
      -h, --help            show this help message and exit


.. tip:: To quickly find out more about ``tira-cli`` or a specific subcommand, use ``tira-cli --help`` or
    ``tira-cli <subcommand> --help``.

.. important:: If you encounter any problems, check with ``tira-cli --version`` if you are up to date. Please include
    this information as well whenever you file a bug ticket for the CLI.


tira-cli login
~~~~~~~~~~~~~~

.. todo:: TODO


tira-cli upload
~~~~~~~~~~~~~~~

.. todo:: TODO


tira-cli download
~~~~~~~~~~~~~~~~~

.. todo:: TODO
