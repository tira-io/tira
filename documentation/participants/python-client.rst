Python Client
=============
For programatic access to TIRA, we provide a python API, the "Python Client", which serves two use-cases:

(1) Interfacing with the TIRA platform
(2) Integrating with third party APIs (e.g., ir-datasets) that would not work otherwise due to TIRA's sandbox.

.. important:: TIRA sandboxes all the evaluation runs to avoid publicizing evaluation data and maintain comparability
   beyond the initial shared task. For you, this means that you can't access arbitrary external resources. Since you
   should not, of course, have to abstain from using `hugging-face`, `ìr_datasets` or other crucial dependencies, we
   integrated some of these into the sandbox.

.. toctree::

   python-client/tiraclient
   python-client/pyterrier
   python-client/ir-datasets


..
   * :ref:`modindex`


   tira.io\_utils module
   ---------------------

   .. automodule:: tira.io_utils
      :members:
      :undoc-members:
      :show-inheritance:

   tira.ir\_datasets\_util module
   ------------------------------

   .. automodule:: tira.ir_datasets_util
      :members:
      :undoc-members:
      :show-inheritance:

   tira.pyterrier\_integration module
   ----------------------------------

   .. automodule:: tira.pyterrier_integration
      :members:
      :undoc-members:
      :show-inheritance:

   tira.pyterrier\_util module
   ---------------------------

   .. automodule:: tira.pyterrier_util
      :members:
      :undoc-members:
      :show-inheritance:

   tira.third\_party\_integrations module
   --------------------------------------

   .. automodule:: tira.third_party_integrations
      :members:
      :undoc-members:
      :show-inheritance:

   Module contents
   ---------------

   .. automodule:: tira
      :members:
      :undoc-members:
      :show-inheritance:
