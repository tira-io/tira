from django.urls import path
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.serializers import Serializer, CharField
from rest_framework import pagination

from ._organizers import OrganizerSerializer
from ... import model as modeldb


class _TaskSerializer(Serializer):
    id = CharField(source="task_id")
    name = CharField(source="task_name")
    description = CharField(source="task_description")
    organizer = OrganizerSerializer()
    website = CharField(source="web")


class _TaskView(ListAPIView):
    queryset = modeldb.Task.objects.all()
    serializer_class = _TaskSerializer
    pagination_class = pagination.CursorPagination


class _TaskDetailView(RetrieveAPIView):
    queryset = modeldb.Task.objects.all()
    serializer_class = _TaskSerializer
    lookup_field="task_id"


endpoints = [
    path("", _TaskView.as_view()),
    path("<str:task_id>/", _TaskDetailView.as_view())
]