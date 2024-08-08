from django.urls import path
from rest_framework import pagination
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import CharField, ModelSerializer
from rest_framework_json_api.views import ModelViewSet

from ... import model as modeldb
from ._evaluations import EvaluationSerializer
from ._organizers import OrganizerSerializer


class DatasetNameOnlySerializer(ModelSerializer):
    id = CharField(source="dataset_id")

    class Meta:
        model = modeldb.Dataset
        fields = ["id", "display_name"]


class TaskSerializer(ModelSerializer):
    id = CharField(source="task_id")
    name = CharField(source="task_name")
    description = CharField(source="task_description")
    organizer = OrganizerSerializer()
    website = CharField(source="web")
    datasets = DatasetNameOnlySerializer(source="dataset_set", many=True, required=False, read_only=True)

    class Meta:
        model = modeldb.Task
        fields = "__all__"


class RegistrationSerializer(ModelSerializer):

    class Meta:
        model = modeldb.Registration
        fields = "__all__"


class _TaskView(ModelViewSet):
    queryset = modeldb.Task.objects.all()
    serializer_class = TaskSerializer
    pagination_class = pagination.CursorPagination
    permission_classes = [IsAdminUser]  # TODO: set to something sensible
    lookup_field = "task_id"


class _EvaluationView(ModelViewSet):
    serializer_class = EvaluationSerializer
    pagination_class = pagination.CursorPagination
    permission_classes = [IsAdminUser]  # TODO: set to something sensible
    lookup_field = "task_id"

    def get_queryset(self):
        return modeldb.Evaluation.objects.filter(run__task=self.kwargs[self.lookup_field])


class _RegistrationView(ModelViewSet):
    serializer_class = RegistrationSerializer
    pagination_class = pagination.CursorPagination
    permission_classes = [IsAdminUser]  # TODO: set to something sensible
    lookup_field = "task_id"

    def get_queryset(self):
        return modeldb.Registration.objects.filter(registered_on_task=self.kwargs[self.lookup_field])


endpoints = [
    path("", _TaskView.as_view({"get": "list", "post": "create"})),
    path("<str:task_id>/", _TaskView.as_view({"get": "retrieve", "delete": "destroy"})),
    path("<str:task_id>/evaluations", _EvaluationView.as_view({"get": "list"})),
    path("<str:task_id>/registrations", _RegistrationView.as_view({"get": "list", "post": "create"})),
    # path("<str:task_id>/submissions", _SubmissionView.as_view({'get': 'list', 'post': 'create'})),
]
