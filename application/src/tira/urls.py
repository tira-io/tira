from django.urls import path

from django.views.generic import TemplateView

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
    path('task/<str:task_id>/user/<str:vm_id>', views.user, name='user'),
    path('task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/run/<str:run_id>', views.review, name='review'),
    # path('software/<str:task_id>', views.software, name='software'),

    path('request_vm', views.request_vm, name='request_vm'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),

    # grpc client endpoints
    path('task/<str:task_id>/vm/<str:vm_id>/edit_registration', vm_api.edit_registration, name='edit_registration'),
    path('task/<str:task_id>/vm/<str:vm_id>/add_software/vm', vm_api.software_add, name='software_add'),
    path('task/<str:task_id>/vm/<str:vm_id>/add_software/docker', vm_api.docker_software_add, name='docker_software_add'),
    path('task/<str:task_id>/vm/<str:vm_id>/save_software/docker/<str:docker_software_id>', vm_api.docker_software_save, name='docker_software_save'),
    path('task/<str:task_id>/vm/<str:vm_id>/save_software/vm/<str:software_id>', vm_api.software_save, name='software_save'),
    path('task/<str:task_id>/vm/<str:vm_id>/delete_software/vm/<str:software_id>', vm_api.software_delete, name='software_delete'),
    path('task/<str:task_id>/vm/<str:vm_id>/delete_software/docker/<str:docker_software_id>', vm_api.docker_software_delete, name='docker_delete'),
    path('task/<str:task_id>/vm/<str:vm_id>/upload/<str:dataset_id>', vm_api.upload, name='upload'),

    path('grpc/<str:vm_id>/vm_info', vm_api.vm_info, name='vm_info'),
    path('grpc/<str:vm_id>/vm_state', vm_api.vm_state, name='vm_state'),
    path('grpc/<str:vm_id>/vm_start', vm_api.vm_start, name='vm_start'),
    path('grpc/<str:vm_id>/vm_shutdown', vm_api.vm_shutdown, name="vm_shutdown"),
    path('grpc/<str:vm_id>/vm_stop', vm_api.vm_stop, name="vm_stop"),
    path('grpc/<str:vm_id>/vm_shutdown', vm_api.vm_shutdown, name="vm_shutdown"),
    path('grpc/<str:vm_id>/run_abort', vm_api.run_abort, name="run_abort"),
    path('grpc/<str:vm_id>/vm_running_evaluations', vm_api.vm_running_evaluations, name="vm_running_evaluations"),
    path('grpc/<str:vm_id>/get_running_evaluations', vm_api.get_running_evaluations, name="get_running_evaluations"),
    path('grpc/<str:task_id>/<str:vm_id>/run_execute/vm/<str:software_id>', vm_api.run_execute, name="run_execute"),
    path('grpc/<str:task_id>/<str:vm_id>/run_execute/docker/<str:dataset_id>/<str:docker_software_id>/<str:docker_resources>', vm_api.run_execute_docker_software, name='run_execute_docker_software'),

    path('grpc/<str:vm_id>/run_eval/<str:dataset_id>/<str:run_id>', vm_api.run_eval, name="run_eval"),
    path('grpc/<str:vm_id>/run_delete/<str:dataset_id>/<str:run_id>', vm_api.run_delete, name="run_delete"),
    path('grpc/<str:task_id>/<str:user_id>/stop_docker_software/<str:run_id>', vm_api.stop_docker_software, name="stop_docker_software"),

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
    path('tira-admin/edit-task/<str:task_id>', admin_api.admin_edit_task, name='tira-admin-edit-task'),
    path('tira-admin/delete-task/<str:task_id>', admin_api.admin_delete_task, name='tira-admin-delete-task'),
    path('tira-admin/add-dataset', admin_api.admin_add_dataset, name='tira-admin-add-dataset'),
    path('tira-admin/import-irds-dataset', admin_api.admin_import_ir_dataset, name='tira-admin-import-irds-dataset'),
    path('tira-admin/edit-dataset/<str:dataset_id>', admin_api.admin_edit_dataset, name='tira-admin-edit-dataset'),
    path('tira-admin/delete-dataset/<str:dataset_id>', admin_api.admin_delete_dataset, name='tira-admin-delete-dataset'),
    path('tira-admin/add-organizer/<str:organizer_id>', admin_api.admin_add_organizer, name='tira-admin-add-organizer'),
    path('tira-admin/edit-organizer/<str:organizer_id>', admin_api.admin_edit_organizer, name='tira-admin-edit-organizer'),
    path('tira-admin/edit-review/<str:dataset_id>/<str:vm_id>/<str:run_id>', admin_api.admin_edit_review, name='tira-admin-edit-review'),
    path('tira-admin/create-group/<str:vm_id>', admin_api.admin_create_group, name='tira-admin-create-group'),

    path('publish/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>', organizer_api.publish, name='publish'),
    path('blind/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>', organizer_api.blind, name='blind'),

    path('api/evaluations/<str:task_id>/<str:dataset_id>', data_api.get_evaluations_by_dataset, name='get_evaluations_by_dataset'),
    path('api/evaluation/<str:vm_id>/<str:run_id>', data_api.get_evaluation, name='get_evaluation'),
    path('api/submissions/<str:task_id>/<str:dataset_id>', data_api.get_submissions_by_dataset, name='get_submissions_by_dataset'),
    path('api/ova-list', data_api.get_ova_list, name='get_ova_list'),
    path('api/host-list', data_api.get_host_list, name='get_host_list'),
    path('api/organizer-list', data_api.get_organizer_list, name='get_organizer_list'),
    path('api/task-list', data_api.get_task_list, name='get_task_list'),
    path('api/task/<str:task_id>', data_api.get_task, name='get_task'),
    path('api/dataset/<str:dataset_id>', data_api.get_dataset, name='get_dataset'),
    path('api/datasets_by_task/<str:task_id>', data_api.get_dataset_for_task, name='get_dataset_for_task'),
    path('api/organizer/<str:organizer_id>', data_api.get_organizer, name='get_organizer'),
    path('api/role', data_api.get_role, name='get_role'),
    path('api/task/<str:task_id>/user/<str:user_id>', data_api.get_user, name='get_user'),
    path('api/task/<str:task_id>/user/<str:user_id>/refresh-docker-images', data_api.update_docker_images, name="get_updated_docker_images"),
    path('api/task/<str:task_id>/user/<str:user_id>/software/running/<str:force_cache_refresh>', data_api.get_running_software, name='get_running_software'),
    path('api/review/<str:dataset_id>/<str:vm_id>/<str:run_id>', data_api.get_review, name='get_review'),
    path('api/registration/add_registration/<str:vm_id>/<str:task_id>', data_api.add_registration, name='add_registration'),
]

app_name = 'tira'
