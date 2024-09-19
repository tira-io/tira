import os

import django

from tira_app.grpc import grpc_server

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_admin.settings")

django.setup()

grpc_server.serve()
