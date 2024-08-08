from django.http import HttpRequest
from rest_framework.permissions import SAFE_METHODS, BasePermission


class ReadOnly(BasePermission):
    def has_permission(self, request: HttpRequest, view):
        return request.method in SAFE_METHODS


class IsOrganizer(BasePermission):

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request: HttpRequest, view, obj) -> bool:
        print(request)
        print(view)
        print(obj)
        # TODO: implement
        return False
