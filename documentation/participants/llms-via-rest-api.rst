Usage of LLMs via REST API
==========================

Is it possible to use LLMs via a REST API in TIRA. Organizers of a shared task must allow this (please reach out to the organizers of your task so that they can enable this).

Attention, this is only a place holder, we are currently in progress of properly documenting this.

High Level Points

You need to forward environment variables to your software, specifically OPENAI_API_KEY, OPENAI_BASE_URL, and OPENAI_MODEL.

Example from trec auto judge:

TBD.

TIRA does not store the forwarded environment variables in a persistent storage, still, the forwarding process causes that the variables are in the celery queue so that the worker that runs the software gets them.

Do not forward access to production REST APIs. Best practice: Have an litellm OpenAI compatible Proxy running on your machine, only forward the credentials of that proxy, delete the proxy and credentials after your participation. If you can not host an own litellm proxy, please reach out to us, we host one, we can add your credentials there, this gives the oportunity that you still not need to forward real environment variables to tira and that we can check after the shared task that the actual production api key is deleted.

