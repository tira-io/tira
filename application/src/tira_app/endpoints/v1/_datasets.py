from django.urls import path
from rest_framework import pagination
from rest_framework.permissions import AllowAny
from rest_framework.serializers import CharField, ModelSerializer
from rest_framework_json_api.views import ModelViewSet

from ... import model as modeldb


class DatasetSerializer(ModelSerializer):
    id = CharField(source="dataset_id")

    class Meta:
        model = modeldb.Dataset
        fields = [
            "id",
            "dataset_id",
            "default_task",
            "display_name",
            "is_confidential",
            "is_deprecated",
            "ir_datasets_id",
            "chatnoir_id",
        ]


class _DatasetView(ModelViewSet):
    queryset = modeldb.Dataset.objects.all()
    serializer_class = DatasetSerializer
    pagination_class = pagination.CursorPagination
    lookup_field = "dataset_id"
    permission_classes = [AllowAny]


endpoints = [
    path("", _DatasetView.as_view({"get": "list"})),
    path("all", _DatasetView.as_view({"get": "list"})),
]
