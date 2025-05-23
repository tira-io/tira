"""
This file contains miscellaneous and **unversioned** endpoints (e.g., the /health or /info).
"""

import json

from django.conf import settings
from django.urls import path
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from tira import __version__ as tira_version
from tira.check_format import SUPPORTED_FORMATS
from tira.evaluators import MEASURE_TO_EVALUATORS

from .. import model as modeldb
from .v1._systems import public_submissions

rest_api_version = "v1.0.0-draft"


EVALUATOR_TO_TYPE = {
    "TrecTools": "Retrieval",
    "RunFileEvaluator": "Retrieval",
    "HuggingFaceEvaluator": "Classification",
    "WowsEvalEvaluator": "Retrieval",
    "TextGenerationEvaluator": "TextGeneration",
}

TRUSTED_EVALUATORS: dict[str, list[str]] = {"Retrieval": [], "Classification": [], "TextGeneration": []}

for measure, evaluator in MEASURE_TO_EVALUATORS.items():
    if evaluator not in EVALUATOR_TO_TYPE:
        continue
    TRUSTED_EVALUATORS[EVALUATOR_TO_TYPE[evaluator]].append(measure)


try:
    SOFTWARE_COUNT = len(json.loads(public_submissions(None).content.decode("UTF-8")))
    DATASET_COUNT = modeldb.Dataset.objects.count()
    TASK_COUNT = modeldb.Task.objects.count()
except Exception:
    SOFTWARE_COUNT = 0
    DATASET_COUNT = 0
    TASK_COUNT = 0


@api_view(["GET"])
@permission_classes([])
@authentication_classes([])
def health_endpoint(request: Request) -> Response:
    """
    The /health endpoint returns 2xx on success (currently 204 because we don't respond with any content). It can be
    used to check if the REST-API is served.
    """
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([])
@authentication_classes([])
def info_endpoint(request: Request) -> Response:
    """
    The /info endpoint contains general information about the running server (e.g., the version of TIRA that is
    running). Do not add any sensitive information to this endpoint as it is **public**!
    """
    return Response(
        {
            "version": tira_version,
            "restApiVersion": rest_api_version,
            "publicSystemCount": SOFTWARE_COUNT,
            "datasetCount": DATASET_COUNT,
            "taskCount": TASK_COUNT,
            "supportedFormats": SUPPORTED_FORMATS,
            "trustedEvaluators": TRUSTED_EVALUATORS,
        }
    )


@api_view(["GET"])
@permission_classes([])
@authentication_classes([])
def well_known_endpoint(request: Request) -> Response:
    return Response(settings.WELL_KNOWN)


endpoints = [
    path("health", health_endpoint),
    path("info", info_endpoint),
    path(".well-known/tira/client", well_known_endpoint),
]
