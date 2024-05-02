Workflow
========
.. todo:: add nice introductory text

Getting Started
---------------
Initial Setup
~~~~~~~~~~~~~
.. todo:: how do I start working on TIRA?

Running TIRA locally
~~~~~~~~~~~~~~~~~~~~
.. todo:: How to run TIRA locally


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

Code Coverage
~~~~~~~~~~~~~
.. code-block:: bash

    coverage run -m pytest tests
    coverage xml --omit=tests/**

Generating documentation
~~~~~~~~~~~~~~~~~~~~~~~~
From within the `python-client/sphynx` directory run

.. code-block:: bash

    sphinx-apidoc -o . ../tira && make html

Releasing a new version
~~~~~~~~~~~~~~~~~~~~~~~
.. todo:: How to release a new version