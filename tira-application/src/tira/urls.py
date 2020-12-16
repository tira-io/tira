from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('task', views.index, name='task'),
    path('tasks', views.index, name='task'),
    path('task/<str:task_id>', views.task_detail, name='task-detail'),
    path('task/<str:task_id>/user/<str:vm_id>', views.software_detail, name='software-detail'),
    path('task/<str:task_id>/dataset/<str:dataset_id>', views.dataset_detail, name='dataset-detail'),
    path('dataset', views.dataset_list, name='dataset'),
    # path('software/<str:user_id>', views.software_detail, name='software-detail'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),

    # grpc client endpoints
    path('user/<str:user_id>/vm/<str:vm_name>/vm_start', views.vm_start, name='vm_start'),
    path('user/<str:user_id>/vm/<str:vm_name>/vm_stop', views.vm_stop, name="vm_stop"),
    path('user/<str:user_id>/vm/<str:vm_name>/run_execute/<str:software_id>', views.run_execute, name="run_execute"),
    path('user/<str:user_id>/vm/<str:vm_name>/run_eval/<str:software_id>', views.run_eval, name="run_eval"),
    path('user/<str:user_id>/command_status/<str:command_id>', views.command_status, name="command_status"),
]
app_name = 'tira'
