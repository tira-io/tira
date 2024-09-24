"""
This file contains miscellaneous and **unversioned** endpoints (e.g., the /health or /info).
"""

from django.urls import path
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from tira import __version__ as tira_version

rest_api_version = "v1.0.0-draft"


@api_view(["GET"])
def health_endpoint(request: Request) -> Response:
    """
    The /health endpoint returns 2xx on success (currently 204 because we don't respond with any content). It can be
    used to check if the REST-API is served.
    """
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def info_endpoint(request: Request) -> Response:
    """
    The /info endpoint contains general information about the running server (e.g., the version of TIRA that is
    running). Do not add any sensitive information to this endpoint as it is **public**!
    """
    return Response(
        {
            "version": tira_version,
            "restApiVersion": rest_api_version,
        }
    )


endpoints = [
    path("health", health_endpoint),
    path("info", info_endpoint),
]
