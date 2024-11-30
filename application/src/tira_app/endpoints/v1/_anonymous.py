from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["GET"])
def read_anonymous_submission(request: Request, submission_uuid: str) -> Response:
    """Read information about an anonymous submission identified by the ownership uuid.

    Args:
        request (Request): The request that triggered the REST API call.
        submission_uuid (str): The ownership uuid of the anonymous submission

    Returns:
        Response: The information about the anonymous submission
    """
    return Response(
        {"uuid": submission_uuid, "dataset_id": "clueweb09-en-trec-web-2009-20230107-training", "created": "fooo"}
    )


endpoints = [
    path("<str:submission_uuid>", read_anonymous_submission),
]
