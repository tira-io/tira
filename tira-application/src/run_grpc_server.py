import django
import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "django_admin.settings"
)
from django_admin.settings import DATABASES, TIME_ZONE, INSTALLED_APPS
django.setup()

from tira import grpc_server
grpc_server.serve()
