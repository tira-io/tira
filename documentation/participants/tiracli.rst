.. _TIRACLIPage:

TIRA CLI
========

You don't always need to write code to interact with TIRA. For your convenience, we offer a handy command line interface (CLI) for quick and efficient interactions with the TIRA platform.

.. note:: ``tira-cli`` is the preferred command. The legacy ``tira-run`` command is still needed when directly
    executing a container image that is not registered as a TIRA approach.


Introduction
~~~~~~~~~~~~
The TIRA CLI is part of the TIRA client for Python. To install it, install the TIRA client using

.. code:: bash

    $ pip install tira

If everything worked, the CLI's help page should display the following:

.. code-block:: bash

    $ tira-cli --help
    usage: tira-cli [-h] [-v]
                    {download,upload,evaluate,login,verify-installation,code-submission,dataset-submission,admin,run} ...

    positional arguments:
      {download,upload,evaluate,login,verify-installation,code-submission,dataset-submission,admin,run}
        download            Download runs or datasets from TIRA.io
        upload              Upload runs or datasets to TIRA.io
        evaluate            Evaluate runs locally.
        login               Login your TIRA client to the TIRA server.
        verify-installation Verify that your local TIRA client is correctly installed.
        code-submission     Make a code submission from a git repository.
        dataset-submission  Submit a new task/dataset to TIRA.
        admin               Control TIRA admin endpoints.
        run                 Run approaches in TIRA or locally.

    options:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit


.. tip:: To quickly find out more about ``tira-cli`` or a specific subcommand, use ``tira-cli --help`` or
    ``tira-cli <subcommand> --help``.

.. important:: If you encounter any problems, check with ``tira-cli --version`` if you are up to date. Please include
    this information as well whenever you file a bug ticket for the CLI.


tira-cli login
~~~~~~~~~~~~~~

.. todo:: TODO


tira-cli verify-installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify that the local client and its dependencies are ready before building submissions or running approaches:

.. code-block:: bash

    tira-cli verify-installation


tira-cli run local
~~~~~~~~~~~~~~~~~~

Execute an approach registered in TIRA on a local or published dataset:

.. code-block:: bash

    tira-cli run local \
      --approach trec-auto-judge/webis/Naive-AutoJudge \
      --input kiddie-20260605-training \
      --out tira-output

Use ``tira-cli run local --help`` for resource limits, environment forwarding, and directory mounts. To execute an
unregistered image directly, continue to use ``tira-run --image ... --command ...``.


tira-cli upload
~~~~~~~~~~~~~~~

.. todo:: TODO


tira-cli download
~~~~~~~~~~~~~~~~~

To download every run of one approach on a dataset, use ``--all-runs``. Each run is stored in a separate
subdirectory named after its TIRA run ID:

.. code:: bash

    tira-cli download \
      --approach trec-auto-judge/webis/tinyjudge \
      --dataset rag25-gen-20260608-test \
      --all-runs \
      --output data/experiment-runs
