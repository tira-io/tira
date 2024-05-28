from django.urls import path
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.serializers import Serializer, CharField
from rest_framework import pagination

from ... import model as modeldb


class _DatasetSerializer(Serializer):
    id = CharField(source="dataset_id")


class _DatasetView(ListAPIView):
    queryset = modeldb.Dataset.objects.all()
    serializer_class = _DatasetSerializer
    pagination_class = pagination.CursorPagination


class _DatasetDetailView(RetrieveAPIView):
    queryset = modeldb.Dataset.objects.all()
    serializer_class = _DatasetSerializer
    lookup_field="dataset_id"


endpoints = [
    path("", _DatasetView.as_view()),
    path("<str:dataset_id>/", _DatasetDetailView.as_view())
]