from django.urls import path
from rest_framework_json_api.views import ModelViewSet
from rest_framework.serializers import Serializer, CharField, ModelSerializer
from rest_framework import pagination

from ._organizers import OrganizerSerializer
from ._evaluations import EvaluationSerializer
from ...authentication import IsOrganizerOrReadOnly
from ... import model as modeldb


class TaskSerializer(Serializer):
    id = CharField(source="task_id")
    name = CharField(source="task_name")
    description = CharField(source="task_description")
    organizer = OrganizerSerializer()
    website = CharField(source="web")


class RegistrationSerializer(ModelSerializer):
    
    class Meta:
        model = modeldb.Registration
        fields = "__all__"


class _TaskView(ModelViewSet):
    queryset = modeldb.Task.objects.all()
    serializer_class = TaskSerializer
    pagination_class = pagination.CursorPagination
    # permission_classes = [IsOrganizerOrReadOnly]
    lookup_field="task_id"


class _EvaluationView(ModelViewSet):
    serializer_class = EvaluationSerializer
    pagination_class = pagination.CursorPagination
    # permission_classes = [IsOrganizerOrReadOnly]
    lookup_field="task_id"

    def get_queryset(self):
        return modeldb.Evaluation.objects.filter(run__task=self.kwargs[self.lookup_field])


class _RegistrationView(ModelViewSet):
    serializer_class = RegistrationSerializer
    pagination_class = pagination.CursorPagination
    # permission_classes = [IsOrganizerOrReadOnly]
    lookup_field="task_id"

    def get_queryset(self):
        return modeldb.Registration.objects.filter(registered_on_task=self.kwargs[self.lookup_field])


endpoints = [
    path("", _TaskView.as_view({'get': 'list', 'post': 'create'})),
    path("<str:task_id>/", _TaskView.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    path("<str:task_id>/evaluations", _EvaluationView.as_view({'get': 'list'})),
    path("<str:task_id>/registrations", _RegistrationView.as_view({'get': 'list', 'post': 'create'})),
    # path("<str:task_id>/submissions", _SubmissionView.as_view({'get': 'list', 'post': 'create'})),
]