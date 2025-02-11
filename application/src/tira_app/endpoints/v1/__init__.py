from django.urls import include, path

from ._anonymous import endpoints as anonymous_endpoints
from ._datasets import endpoints as dataset_endpoints
from ._evaluations import endpoints as evaluation_endpoints
from ._organizers import endpoints as organizer_endpoints
from ._runs import endpoints as run_endpoints
from ._systems import endpoints as system_endpoints
from ._tasks import endpoints as task_endpoints
from ._tirex import endpoints as tirex_endpoints
from ._user import endpoints as user_endpoints

endpoints = [
    path("anonymous/", include(anonymous_endpoints)),
    path("datasets/", include(dataset_endpoints)),
    path("evaluations/", include(evaluation_endpoints)),
    path("organizers/", include(organizer_endpoints)),
    path("runs/", include(run_endpoints)),
    path("systems/", include(system_endpoints)),
    path("tirex/", include(tirex_endpoints)),
    path("tasks/", include(task_endpoints)),
    path("user/", include(user_endpoints)),
]
