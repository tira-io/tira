from django.urls import path

from . import views
from . import actions

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
    # path('software/<str:user_id>', views.software_detail, name='software-detail'),  # show all vms on tasks of a user
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),

    # grpc client endpoints
    # path('user/<str:user_id>/vm/<str:vm_id>/vm_info', endpoints.vm_info, name='vm_info'),
    path('user/<str:user_id>/vm/<str:vm_id>/vm_start', actions.vm_start, name='vm_start'),
    path('user/<str:user_id>/vm/<str:vm_id>/vm_stop', actions.vm_stop, name="vm_stop"),
    path('task/<str:task_id>/vm/<str:vm_id>/software_add', actions.software_add, name='software_add'),
    path('task/<str:task_id>/vm/<str:vm_id>/software_save/<str:software_id>', actions.software_save, name='software_save'),
    path('task/<str:task_id>/vm/<str:vm_id>/software_delete/<str:software_id>', actions.software_delete, name='software_delete'),
    path('user/<str:user_id>/vm/<str:vm_id>/run_execute/<str:software_id>', actions.run_execute, name="run_execute"),
    path('user/<str:user_id>/vm/<str:vm_id>/run_eval/<str:software_id>', actions.run_eval, name="run_eval"),
    path('command_status/<str:command_id>', actions.command_status, name="command_status"),
    path('bulk_command_status/<str:bulk_id>', actions.get_bulk_command_status, name="get_bulk_command_status"),

    path('grpc/<str:vm_id>/vm_info', actions.vm_info, name='vm_info'),
    path('grpc/<str:vm_id>/vm_state', actions.vm_state, name='vm_state'),
    path('grpc/<str:vm_id>/vm_start', actions.vm_start, name='vm_start'),
    path('grpc/<str:vm_id>/vm_shutdown', actions.vm_shutdown, name="vm_shutdown"),
    path('grpc/<str:vm_id>/vm_stop', actions.vm_stop, name="vm_stop"),
    path('grpc/<str:vm_id>/vm_shutdown', actions.vm_shutdown, name="vm_shutdown"),
    path('grpc/<str:vm_id>/vm_abort_run', actions.vm_abort_run, name="vm_abort_run"),
    path('grpc/<str:task_id>/<str:vm_id>/run_execute/<str:software_id>', actions.run_execute, name="run_execute"),
    path('grpc/<str:vm_id>/run_eval/<str:software_id>', actions.run_eval, name="run_eval"),
    path('grpc/<str:vm_id>/run_delete/<str:dataset_id>/<str:run_id>', actions.run_delete, name="run_delete"),

    path('tira-admin', views.admin, name='tira-admin'),
    path('tira-admin/reload-data', actions.admin_reload_data, name='tira-admin-reload-data'),
    path('tira-admin/create-vm', actions.admin_create_vm, name='tira-admin-create-vm'),
    path('tira-admin/archive-vm', actions.admin_archive_vm, name='tira-admin-archive-vm'),
    path('tira-admin/modify-vm', actions.admin_modify_vm, name='tira-admin-modify-vm'),
    path('tira-admin/create-task', actions.admin_create_task, name='tira-admin-create-task'),
    path('tira-admin/add-dataset', actions.admin_add_dataset, name='tira-admin-add-dataset'),

    # path('task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/run/<str:run_id>/review', views.add_review, name='add-review'),
    path('publish/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>', actions.publish, name='publish'),
    path('blind/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>', actions.blind, name='blind'),
]
app_name = 'tira'
