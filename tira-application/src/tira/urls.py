from django.urls import path

from . import views
from . import actions

urlpatterns = [
    path('', views.index, name='index'),
    path('task', views.index, name='tasks'),
    path('tasks', views.index, name='tasks'),
    path('task/<str:task_id>', views.task_detail, name='task-detail'),
    path('task/<str:task_id>/dataset/<str:dataset_id>', views.dataset_detail, name='dataset-detail'),
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
    path('user/<str:user_id>/vm/<str:vm_id>/run_execute/<str:software_id>', actions.run_execute, name="run_execute"),
    path('user/<str:user_id>/vm/<str:vm_id>/run_eval/<str:software_id>', actions.run_eval, name="run_eval"),
    path('command_status/<str:command_id>', actions.command_status, name="command_status"),
    path('bulk_command_status/<str:bulk_id>', actions.get_bulk_command_status, name="get_bulk_command_status"),

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
