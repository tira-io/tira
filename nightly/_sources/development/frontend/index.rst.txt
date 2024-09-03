Frontend Development
====================

.. hint:: This page generally describes **two ways** of achieving the same thing: Using VSCode and using the shell. For
    general development, we **highly recommend** using the VSCode integration unless it does not work for you or a
    shell is required. Simply set the tab to the version you will work with, they a synchronized through the magic of
    technology.



.. rubric:: Getting Started

To get started, please read and follow the instructions of the :ref:`DevEnvPage` section.


.. tab-set::

    .. tab-item:: VSCode
        
        .. _launchfrontend:

        .. dropdown:: :octicon:`rocket` Launching the Frontend
            
            .. todo:: TODO

        .. dropdown:: :octicon:`beaker` Code Testing
            
            .. todo:: TODO

        .. dropdown:: :fab:`hammer` Building the Static Frontend

            .. attention:: This step can only be performed via shell and is only really useful for deployment. If
                you simply want to launch the frontend for debugging, have a look at
                :ref:`Launching the Frontend <launchfrontend>`.
    
    .. tab-item:: Shell
        
        .. dropdown:: :octicon:`rocket` Launching the Frontend
            
            Open a shell within the ``frontend`` directory and run

            .. code:: bash
                
                yarn dev

        .. dropdown:: :octicon:`beaker` Code Testing
            
            Open a shell within the ``frontend`` directory and run

            .. code:: bash
                
                yarn test

        .. dropdown:: :fab:`hammer` Building the Static Frontend

            Open a shell within the ``frontend`` directory and either run

            .. code:: bash
                
                yarn build-light



.. rubric:: Linting

.. note:: We don't currently have any linters



.. rubric:: Frequently Asked Questions

No questions yet :material-regular:`mood;1.5em;sd-text-success`.
