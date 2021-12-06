from django.urls import path

from . import views
from .actions import actions, admin_actions, software_actions

urlpatterns = [
    path('', views.index, name='index'),
    path('task', views.index, name='tasks'),
    path('tasks', views.index, name='tasks'),
    path('task/<str:task_id>', views.task_detail, name='task-detail'),
    path('task/<str:task_id>/dataset/<str:dataset_id>', views.dataset_detail, name='dataset-detail'),
    path('task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip', views.download_rundir, name='download_rundir'),
    path('task/<str:task_id>/user/<str:vm_id>', views.software_detail, name='software-detail'),
    path('task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/run/<str:run_id>', views.review, name='review'),
    path('dataset', views.dataset_list, name='dataset'),
    path('users', views.users, name='users'),
    path('user/<str:user_id>', views.user_detail, name='user-detail'),
    path('request_vm', views.request_vm, name='request_vm'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),

    # grpc client endpoints
    path('task/<str:task_id>/vm/<str:vm_id>/software_add', software_actions.software_add, name='software_add'),
    path('task/<str:task_id>/vm/<str:vm_id>/software_save/<str:software_id>', software_actions.software_save, name='software_save'),
    path('task/<str:task_id>/vm/<str:vm_id>/software_delete/<str:software_id>', software_actions.software_delete, name='software_delete'),

    path('grpc/<str:vm_id>/vm_info', software_actions.vm_info, name='vm_info'),
    path('grpc/<str:vm_id>/vm_state', software_actions.vm_state, name='vm_state'),
    path('grpc/<str:vm_id>/vm_start', software_actions.vm_start, name='vm_start'),
    path('grpc/<str:vm_id>/vm_shutdown', software_actions.vm_shutdown, name="vm_shutdown"),
    path('grpc/<str:vm_id>/vm_stop', software_actions.vm_stop, name="vm_stop"),
    path('grpc/<str:vm_id>/vm_shutdown', software_actions.vm_shutdown, name="vm_shutdown"),
    path('grpc/<str:vm_id>/run_abort', software_actions.run_abort, name="run_abort"),
    path('grpc/<str:vm_id>/vm_running_evaluations', software_actions.vm_running_evaluations, name="vm_running_evaluations"),
    path('grpc/<str:task_id>/<str:vm_id>/run_execute/<str:software_id>', software_actions.run_execute, name="run_execute"),
    path('grpc/<str:vm_id>/run_eval/<str:dataset_id>/<str:run_id>', software_actions.run_eval, name="run_eval"),
    path('grpc/<str:vm_id>/run_delete/<str:dataset_id>/<str:run_id>', software_actions.run_delete, name="run_delete"),

    path('tira-admin', views.admin, name='tira-admin'),
    path('tira-admin/reload-data', admin_actions.admin_reload_data, name='tira-admin-reload-data'),
    path('tira-admin/create-vm', admin_actions.admin_create_vm, name='tira-admin-create-vm'),
    path('tira-admin/archive-vm', admin_actions.admin_archive_vm, name='tira-admin-archive-vm'),
    path('tira-admin/modify-vm', admin_actions.admin_modify_vm, name='tira-admin-modify-vm'),
    path('tira-admin/create-task', admin_actions.admin_create_task, name='tira-admin-create-task'),
    path('tira-admin/add-dataset', admin_actions.admin_add_dataset, name='tira-admin-add-dataset'),

    path('publish/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>', actions.publish, name='publish'),
    path('blind/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>', actions.blind, name='blind'),
]
app_name = 'tira'
