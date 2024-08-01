from django.urls import path
from rest_framework import pagination
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework_json_api.views import ModelViewSet

from ... import model as modeldb


class EvaluationSerializer(ModelSerializer):
    class Meta:
        model = modeldb.Evaluation
        fields = ["measure_key", "measure_value", "evaluator", "run"]


class _EvaluationView(ModelViewSet):
    queryset = modeldb.Evaluation.objects.all()
    serializer_class = EvaluationSerializer
    pagination_class = pagination.CursorPagination
    permission_classes = [IsAdminUser]  # TODO: set to something sensible


endpoints = [
    path("", _EvaluationView.as_view({"get": "list"})),
]
