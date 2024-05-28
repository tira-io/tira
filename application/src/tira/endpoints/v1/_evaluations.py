from django.urls import path
from rest_framework_json_api.views import ModelViewSet
from rest_framework.serializers import CharField, ModelSerializer
from rest_framework import pagination

from ... import model as modeldb


class EvaluationSerializer(ModelSerializer):
    class Meta:
        model = modeldb.Evaluation
        fields = ['measure_key', 'measure_value', "evaluator", "run"]


class _EvaluationView(ModelViewSet):
    queryset = modeldb.Evaluation.objects.all()
    serializer_class = EvaluationSerializer
    pagination_class = pagination.CursorPagination


endpoints = [
    path("", _EvaluationView.as_view({'get': 'list'})),
]