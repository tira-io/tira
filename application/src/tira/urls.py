from django.urls import path

from . import views
from .endpoints import organizer_api, admin_api, vm_api, data_api

urlpatterns = [
    path('', views.index, name='index'),
    path('task', views.index, name='index'),
    path('tasks', views.index, name='index'),
    path('task/<str:task_id>', views.task, name='task'),
    path('task/<str:task_id>/dataset/<str:dataset_id>', views.dataset, name='dataset'),
    path('task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip', views.download_rundir, name='download_rundir'),
    path('task/<str:task_id>/user/<str:vm_id>', views.software_detail, name='software-detail'),
    path('task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/run/<str:run_id>', views.review, name='review'),
    path('request_vm', views.request_vm, name='request_vm'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),

    # grpc client endpoints
    path('task/<str:task_id>/vm/<str:vm_id>/software_add', vm_api.software_add, name='software_add'),
    path('task/<str:task_id>/vm/<str:vm_id>/software_save/<str:software_id>', vm_api.software_save, name='software_save'),
    path('task/<str:task_id>/vm/<str:vm_id>/software_delete/<str:software_id>', vm_api.software_delete, name='software_delete'),

    path('grpc/<str:vm_id>/vm_info', vm_api.vm_info, name='vm_info'),
    path('grpc/<str:vm_id>/vm_state', vm_api.vm_state, name='vm_state'),
    path('grpc/<str:vm_id>/vm_start', vm_api.vm_start, name='vm_start'),
    path('grpc/<str:vm_id>/vm_shutdown', vm_api.vm_shutdown, name="vm_shutdown"),
    path('grpc/<str:vm_id>/vm_stop', vm_api.vm_stop, name="vm_stop"),
    path('grpc/<str:vm_id>/vm_shutdown', vm_api.vm_shutdown, name="vm_shutdown"),
    path('grpc/<str:vm_id>/run_abort', vm_api.run_abort, name="run_abort"),
    path('grpc/<str:vm_id>/vm_running_evaluations', vm_api.vm_running_evaluations, name="vm_running_evaluations"),
    path('grpc/<str:task_id>/<str:vm_id>/run_execute/<str:software_id>', vm_api.run_execute, name="run_execute"),
    path('grpc/<str:vm_id>/run_eval/<str:dataset_id>/<str:run_id>', vm_api.run_eval, name="run_eval"),
    path('grpc/<str:vm_id>/run_delete/<str:dataset_id>/<str:run_id>', vm_api.run_delete, name="run_delete"),

    path('tira-admin', views.admin, name='tira-admin'),

    path('tira-admin/reload/vms', admin_api.admin_reload_vms, name='tira-admin-reload-vms'),
    path('tira-admin/reload/datasets', admin_api.admin_reload_datasets, name='tira-admin-reload-datasets'),
    path('tira-admin/reload/tasks', admin_api.admin_reload_tasks, name='tira-admin-reload-tasks'),
    path('tira-admin/reload-data', admin_api.admin_reload_data, name='tira-admin-reload-data'),
    path('tira-admin/reload-runs/<str:vm_id>', admin_api.admin_reload_runs, name='tira-admin-reload-runs'),

    path('tira-admin/create-vm', admin_api.admin_create_vm, name='tira-admin-create-vm'),
    path('tira-admin/archive-vm', admin_api.admin_archive_vm, name='tira-admin-archive-vm'),
    path('tira-admin/modify-vm', admin_api.admin_modify_vm, name='tira-admin-modify-vm'),
    path('tira-admin/create-task', admin_api.admin_create_task, name='tira-admin-create-task'),
    path('tira-admin/add-dataset', admin_api.admin_add_dataset, name='tira-admin-add-dataset'),
    path('tira-admin/create-group/<str:vm_id>', admin_api.admin_create_group, name='tira-admin-create-group'),

    path('publish/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>', organizer_api.publish, name='publish'),
    path('blind/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>', organizer_api.blind, name='blind'),

    path('api/evaluations/<str:task_id>/<str:dataset_id>', data_api.get_evaluations_by_dataset, name='get_evaluations_by_dataset'),
    path('api/submissions/<str:task_id>/<str:dataset_id>', data_api.get_submissions_by_dataset, name='get_submissions_by_dataset'),
    path('api/ova-list', data_api.get_ova_list, name='get_ova_list'),
    path('api/host-list', data_api.get_host_list, name='get_host_list'),
    path('api/organizer-list', data_api.get_organizer_list, name='get_organizer_list'),
    path('api/task-list', data_api.get_task_list, name='get_task_list'),

]
app_name = 'tira'
