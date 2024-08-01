.. _deployment:

Deployment
==========

.. hint:: You just want to try TIRA within your organization without setting up the production deployment? We have created a slimmed down :bdg-ref-secondary:`demo deployment <demo_deployment>` just for this!

.. rubric:: Modules of a complete TIRA deployment

.. grid:: 1 1 1 1
   :margin: 4 4 0 0
   :gutter: 1

   .. grid-item-card:: :octicon:`cpu` Backend
      :link: application
      :link-type: doc

      TIRA's brains.

   .. grid-item-card:: :octicon:`devices` Frontend
      :link: frontend
      :link-type: doc

      The web frontend presented to TIRA's users.

   .. grid-item-card:: :octicon:`id-badge` Authentication Provider

      TIRA does not do any user management. Instead, we leave this to third party authentication providers.
      +++
      For the official `tira.io <https://www.tira.io/>`_ deployment, we use Discourse but any authentication provider that supports trusted header authentication should work.

   .. grid-item-card:: :octicon:`lock` Reverse Proxy

      For security reasons, you **MUST** use a reverse proxy to delegate authentication to the Auth Provider and set the HTTP header fields accordingly. Trusted header authentication works by adding a user identifier as a simple HTTP header field to any request that needs authentication. If any user could just set this field as they whish, they could easily impersonate any user they like.
      +++
      For the official `tira.io <https://www.tira.io/>`_ deployment, we use Disraptor.

   .. grid-item-card:: :octicon:`package` Runner
      :link: runner
      :link-type: doc
      
      Runners are responsible for executing and evaluating the submissions.

.. umlet-image:: ../../development/images/architecturestack.uxf
    :align: center

.. toctree::
    :maxdepth: 2
    :hidden:

    application
    frontend
    demo
    frontend_legacy
