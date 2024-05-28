from django.urls import include, path
from ._datasets import endpoints as dataset_endpoints
from ._evaluations import endpoints as evaluation_endpoints
from ._organizers import endpoints as organizer_endpoints
from ._runs import endpoints as run_endpoints
from ._tasks import endpoints as task_endpoints

endpoints = [
    path("datasets/", include(dataset_endpoints)),
    path("evaluations/", include(evaluation_endpoints)),
    path("organizers/", include(organizer_endpoints)),
    path("runs/", include(run_endpoints)),
    path("tasks/", include(task_endpoints)),
]