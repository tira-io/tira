from django.urls import path

from . import views

app_name = 'tira'
urlpatterns = [
    path('', views.index, name='index'),
    path('task', views.task_list, name='task'),
    path('tasks', views.task_list, name='task'),
    path('task/<str:task_id>', views.task_detail, name='task-detail'),
    path('task/<str:task_id>/user/<str:user_id>', views.software_detail, name='software-detail'),
    path('task/<str:task_id>/user/<str:user_id>/<str:action>', views.software_detail, name='software-detail'),
    path('dataset', views.dataset_list, name='dataset'),
    path('dataset/<str:dataset_id>', views.dataset_detail, name='dataset-detail'),
    path('software/<str:user_id>', views.software_user, name='software-user'),
    path('authentication', views.authentication, name='authentication'),

    # grpc client endpoints
    path('user/<str:user_id>/vm/<str:vm_name>/vm_start', views.vm_start, name='vm_start'),
    path('user/<str:user_id>/vm/<str:vm_name>/vm_stop', views.vm_stop, name="vm_stop"),
    path('user/<str:user_id>/vm/<str:vm_name>/run_execute/<str:software_id>', views.run_execute, name="run_execute"),
    path('user/<str:user_id>/vm/<str:vm_name>/run_eval/<str:software_id>', views.run_eval, name="run_eval"),
    path('user/<str:user_id>/command_status/<str:command_id>', views.command_status, name="command_status"),
]