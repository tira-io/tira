from django.urls import path
from rest_framework import pagination
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import CharField, ModelSerializer
from rest_framework_json_api.views import ModelViewSet

from ... import model as modeldb


class OrganizerSerializer(ModelSerializer):
    id = CharField(source="organizer_id")
    website = CharField(source="web")

    class Meta:
        model = modeldb.Organizer
        fields = ["id", "name", "years", "website"]


# TODO: creating an organizer should behave like: admin_add_organizer
# TODO: editing an organizer should behave like: admin_edit_organizer


class _OrganizerView(ModelViewSet):
    queryset = modeldb.Organizer.objects.all()
    serializer_class = OrganizerSerializer
    pagination_class = pagination.CursorPagination
    permission_classes = [IsAdminUser]  # TODO: set to something sensible
    lookup_field = "organizer_id"

    filterset_fields = {
        "name": (
            "exact",
            "contains",
        ),
        "web": (
            "exact",
            "contains",
        ),
        "years": (
            "exact",
            "contains",
        ),
    }


endpoints = [
    path("", _OrganizerView.as_view({"get": "list", "post": "create"})),
    path("<str:organizer_id>/", _OrganizerView.as_view({"get": "retrieve", "delete": "destroy"})),
]
