IR-Datasets Integration
=======================

The **only** thing you need to know about TIRA's ir_datasets integration as a user is to replace your import of
ir_datasets like so:

.. code-block:: diff
    
   - import ir_datasets
   + from tira.third_party_integrations import ir_datasets

Now you can work with ir_datasets **exactly** like you usually would. The entire rest of this page only contains
background information on what happens behind the scenes and you can safely skip it if you are not interested.


.. rubric:: Behind the Scenes

.. todo:: TODO