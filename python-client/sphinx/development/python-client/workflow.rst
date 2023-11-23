Workflow
========
TODO: add nice introductory text

Getting Started
-------------
Initial Setup
~~~~~~~~~~~~~
TODO: how do I start working on TIRA?

Running TIRA locally
~~~~~~~~~~~~~~~~~~~~
TOOD


Commands
--------
Linting
~~~~~~~
.. code-block:: bash

    black --check tira/ tests/
    flake8 tira/ tests/
    mypy tira/ tests/

To let black reformat a file, run:

.. code-block:: bash

    black tira tests

Unit Tests
~~~~~~~~~~
.. code-block:: bash

    pytest

Generating documentation
~~~~~~~~~~~~~~~~~~~~~~~~
From within the `python-client/sphynx` directory run

.. code-block:: bash

    sphinx-apidoc -o . ../tira && make html

Releasing a new version
~~~~~~~~~~~~~~~~~~~~~~~
TODO