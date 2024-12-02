from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from ... import model as modeldb


@api_view(["GET"])
def read_anonymous_submission(request: Request, submission_uuid: str) -> Response:
    """Read information about an anonymous submission identified by the ownership uuid.

    Args:
        request (Request): The request that triggered the REST API call.
        submission_uuid (str): The ownership uuid of the anonymous submission

    Returns:
        Response: The information about the anonymous submission
    """
    ret = modeldb.AnonymousUploads.objects.get(uuid=submission_uuid)

    return Response({"uuid": ret.uuid, "dataset_id": ret.dataset.dataset_id, "created": ret.created})


endpoints = [
    path("<str:submission_uuid>", read_anonymous_submission),
]
