from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from ... import model as modeldb


@api_view(['GET'])
def user_endpoint(request: Request) -> Response:
    return Response({"username": request.user.username, "groups": request.user.groups})


endpoints = [
    path("", user_endpoint),
]