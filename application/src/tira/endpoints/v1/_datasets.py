from django.urls import path
from rest_framework_json_api.views import ModelViewSet
from rest_framework.serializers import CharField, ModelSerializer
from rest_framework import pagination

from ... import model as modeldb
from ._tasks import TaskSerializer


class _DatasetSerializer(ModelSerializer):
    id = CharField(source="dataset_id")
    default_task = TaskSerializer()

    class Meta:
        model = modeldb.Dataset
        fields = ['id', 'default_task', 'display_name', 'evaluator', 'is_confidential', 'is_deprecated', 'data_server', 'released', 'default_upload_name', 'created', 'last_modified']


class _DatasetView(ModelViewSet):
    queryset = modeldb.Dataset.objects.all()
    serializer_class = _DatasetSerializer
    pagination_class = pagination.CursorPagination
    lookup_field="dataset_id"

endpoints = [
    path("", _DatasetView.as_view({'get': 'list'})),
    path("<str:dataset_id>/", _DatasetView.as_view({'get': 'retrieve', 'delete': 'destroy'}))
]