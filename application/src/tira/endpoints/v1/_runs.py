from django.urls import path
from rest_framework import pagination
from rest_framework.generics import RetrieveAPIView
from rest_framework.serializers import CharField, ModelSerializer, Serializer
from rest_framework_json_api.views import ModelViewSet

from ... import model as modeldb


class _RunSerializer(Serializer):
    id = CharField(source="run_id")

    class Meta:
        model = modeldb.Run
        fields = ["id", "downloadable", "deleted"]


class _ReviewSerializer(ModelSerializer):
    run_id = CharField(source="run")

    class Meta:
        model = modeldb.Review
        fields = [
            "run_id",
            "reviewer_id",
            "review_date",
            "no_errors",
            "missing_output",
            "extraneous_output",
            "invalid_output",
            "has_error_output",
            "other_errors",
            "comment",
            "has_errors",
            "has_warnings",
            "has_no_errors",
            "published",
            "blinded",
        ]


class _RunView(ModelViewSet):
    queryset = modeldb.Run.objects.all()
    serializer_class = _RunSerializer
    pagination_class = pagination.CursorPagination
    lookup_field = "run_id"


class _ReviewDetailView(RetrieveAPIView):
    queryset = modeldb.Review
    serializer_class = _ReviewSerializer
    lookup_field = "run"


endpoints = [
    path("", _RunView.as_view({"get": "list"})),
    path("<str:run_id>/", _RunView.as_view({"get": "retrieve", "delete": "destroy"})),
    path("<str:run>/review", _ReviewDetailView.as_view()),
]
