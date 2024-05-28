Pyterrier Integration
=====================

.. code-block:: diff

    - import pyterrier as pt
    - if not pt.started():
    -     pt.init()
    + from tira.third_party_integrations import ensure_pyterrier_is_loaded
    + ensure_pyterrier_is_loaded()
    + import pyterrier as pt
