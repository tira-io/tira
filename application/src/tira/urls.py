from django.urls import path

from . import views
from .endpoints import admin_api, data_api, diffir_api, organizer_api, serp_api, vm_api

urlpatterns = [
    path("background_jobs/<str:task_id>/<str:job_id>", views.background_jobs, name="background_jobs"),
    path(
        "task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip",
        views.download_rundir,
        name="download_rundir",
    ),
    path(
        "data-download/git-repo-template/<str:vm_id>/<str:task_id>.zip",
        views.download_repo_template,
        name="download_repo_template",
    ),
    path(
        "data-download/<str:dataset_type>/<str:input_type>/<str:dataset_id>.zip",
        views.download_datadir,
        name="download_datadir",
    ),
    # grpc client endpoints
    path(
        "task/<str:task_id>/vm/<str:vm_id>/add_software/docker", vm_api.docker_software_add, name="docker_software_add"
    ),
    path("task/<str:task_id>/vm/<str:vm_id>/add_software/upload", vm_api.add_upload, name="add_upload"),
    path(
        "task/<str:task_id>/vm/<str:vm_id>/save_software/docker/<str:docker_software_id>",
        vm_api.docker_software_save,
        name="docker_software_save",
    ),
    path(
        "task/<str:task_id>/vm/<str:vm_id>/save_software/upload/<str:upload_id>",
        vm_api.upload_save,
        name="docker_software_save",
    ),
    path(
        "task/<str:task_id>/vm/<str:vm_id>/delete_software/vm/<str:software_id>",
        vm_api.software_delete,
        name="software_delete",
    ),
    path(
        "task/<str:task_id>/vm/<str:vm_id>/delete_software/docker/<str:docker_software_id>",
        vm_api.docker_software_delete,
        name="docker_delete",
    ),
    path("task/<str:task_id>/vm/<str:vm_id>/run_details/<str:run_id>", vm_api.run_details, name="run_details"),
    path(
        "task/<str:task_id>/vm/<str:vm_id>/software_details/<str:software_name>",
        vm_api.software_details,
        name="software_details",
    ),
    path("task/<str:task_id>/vm/<str:vm_id>/upload/<str:dataset_id>/<str:upload_id>", vm_api.upload, name="upload"),
    path("task/<str:task_id>/vm/<str:vm_id>/upload-delete/<str:upload_id>", vm_api.delete_upload, name="deleteupload"),
    path("grpc/<str:vm_id>/vm_info", vm_api.vm_info, name="vm_info"),
    path("grpc/<str:vm_id>/vm_state", vm_api.vm_state, name="vm_state"),
    path("grpc/<str:vm_id>/vm_start", vm_api.vm_start, name="vm_start"),
    path("grpc/<str:vm_id>/vm_shutdown", vm_api.vm_shutdown, name="vm_shutdown"),
    path("grpc/<str:vm_id>/vm_stop", vm_api.vm_stop, name="vm_stop"),
    path("grpc/<str:vm_id>/vm_shutdown", vm_api.vm_shutdown, name="vm_shutdown"),
    path("grpc/<str:vm_id>/run_abort", vm_api.run_abort, name="run_abort"),
    path("grpc/<str:vm_id>/vm_running_evaluations", vm_api.vm_running_evaluations, name="vm_running_evaluations"),
    path("grpc/<str:vm_id>/get_running_evaluations", vm_api.get_running_evaluations, name="get_running_evaluations"),
    path("grpc/<str:task_id>/<str:vm_id>/run_execute/vm/<str:software_id>", vm_api.run_execute, name="run_execute"),
    path(
        (
            "grpc/<str:task_id>/<str:vm_id>/run_execute/docker/<str:dataset_id>/<str:docker_software_id>/"
            "<str:docker_resources>/<str:rerank_dataset>"
        ),
        vm_api.run_execute_docker_software,
        name="run_execute_docker_software",
    ),
    path("grpc/<str:vm_id>/run_eval/<str:dataset_id>/<str:run_id>", vm_api.run_eval, name="run_eval"),
    path("grpc/<str:vm_id>/run_delete/<str:dataset_id>/<str:run_id>", vm_api.run_delete, name="run_delete"),
    path(
        "grpc/<str:task_id>/<str:user_id>/stop_docker_software/<str:run_id>",
        vm_api.stop_docker_software,
        name="stop_docker_software",
    ),
    path("tira-admin/reload/vms", admin_api.admin_reload_vms, name="tira-admin-reload-vms"),
    path("tira-admin/reload/datasets", admin_api.admin_reload_datasets, name="tira-admin-reload-datasets"),
    path("tira-admin/reload/tasks", admin_api.admin_reload_tasks, name="tira-admin-reload-tasks"),
    path("tira-admin/reload-data", admin_api.admin_reload_data, name="tira-admin-reload-data"),
    path("tira-admin/reload-runs/<str:vm_id>", admin_api.admin_reload_runs, name="tira-admin-reload-runs"),
    path("tira-admin/create-vm", admin_api.admin_create_vm, name="tira-admin-create-vm"),
    path("tira-admin/archive-vm", admin_api.admin_archive_vm, name="tira-admin-archive-vm"),
    path("tira-admin/modify-vm", admin_api.admin_modify_vm, name="tira-admin-modify-vm"),
    path(
        "tira-admin/export-participants/<str:task_id>.csv", data_api.export_registrations, name="export_registrations"
    ),
    path("tira-admin/<str:organizer_id>/create-task", admin_api.admin_create_task, name="tira-admin-create-task"),
    path("tira-admin/edit-task/<str:task_id>", admin_api.admin_edit_task, name="tira-admin-edit-task"),
    path("tira-admin/delete-task/<str:task_id>", admin_api.admin_delete_task, name="tira-admin-delete-task"),
    path("tira-admin/add-dataset/<str:task_id>", admin_api.admin_add_dataset, name="tira-admin-add-dataset"),
    path(
        "tira-admin/upload-dataset/<str:task_id>/<str:dataset_id>/<str:dataset_type>",
        admin_api.admin_upload_dataset,
        name="tira-admin-upload-dataset",
    ),
    path(
        "tira-admin/import-irds-dataset/<str:task_id>",
        admin_api.admin_import_ir_dataset,
        name="tira-admin-import-irds-dataset",
    ),
    path("tira-admin/edit-dataset/<str:dataset_id>", admin_api.admin_edit_dataset, name="tira-admin-edit-dataset"),
    path(
        "tira-admin/delete-dataset/<str:dataset_id>", admin_api.admin_delete_dataset, name="tira-admin-delete-dataset"
    ),
    path("tira-admin/add-organizer/<str:organizer_id>", admin_api.admin_add_organizer, name="tira-admin-add-organizer"),
    path(
        "tira-admin/edit-organizer/<str:organizer_id>", admin_api.admin_edit_organizer, name="tira-admin-edit-organizer"
    ),
    path(
        "tira-admin/edit-review/<str:dataset_id>/<str:vm_id>/<str:run_id>",
        admin_api.admin_edit_review,
        name="tira-admin-edit-review",
    ),
    path("tira-admin/create-group/<str:vm_id>", admin_api.admin_create_group, name="tira-admin-create-group"),
    path("publish/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>", organizer_api.publish, name="publish"),
    path("blind/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>", organizer_api.blind, name="blind"),
    path(
        "api/evaluations/<str:task_id>/<str:dataset_id>",
        data_api.get_evaluations_by_dataset,
        name="get_evaluations_by_dataset",
    ),
    path(
        "api/evaluations-of-vm/<str:task_id>/<str:vm_id>", data_api.get_evaluations_by_vm, name="get_evaluations_by_vm"
    ),
    path("api/evaluation/<str:vm_id>/<str:run_id>", data_api.get_evaluation, name="get_evaluation"),
    path(
        "api/submissions/<str:task_id>/<str:dataset_id>",
        data_api.get_submissions_by_dataset,
        name="get_submissions_by_dataset",
    ),
    path(
        "api/docker-softwares-details/<str:vm_id>/<str:docker_software_id>",
        vm_api.docker_software_details,
        name="software_details",
    ),
    path(
        "api/huggingface_model_mounts/vm/<str:vm_id>/<str:hf_model>",
        vm_api.huggingface_model_mounts,
        name="huggingface_model_mounts",
    ),
    path(
        "api/upload-group-details/<str:task_id>/<str:vm_id>/<str:upload_id>",
        vm_api.upload_group_details,
        name="upload_id",
    ),
    path("api/evaluations_of_run/<str:vm_id>/<str:run_id>", data_api.get_evaluations_of_run, name="evaluations_of_run"),
    path(
        "api/configuration-of-evaluation/<str:task_id>/<str:dataset_id>",
        data_api.get_configuration_of_evaluation,
        name="get_configuration_of_evaluation",
    ),
    path("api/list-runs/<str:task_id>/<str:dataset_id>/<str:vm_id>/<str:software_id>", data_api.runs, name="runs"),
    path("api/host-list", data_api.get_host_list, name="get_host_list"),
    path("api/organizer-list", data_api.get_organizer_list, name="get_organizer_list"),
    path("api/task-list", data_api.get_task_list, name="get_task_list"),
    path("api/task/<str:task_id>", data_api.get_task, name="get_task"),
    path(
        "api/registration_formular/<str:task_id>", data_api.get_registration_formular, name="get_registration_formular"
    ),
    path("api/dataset/<str:dataset_id>", data_api.get_dataset, name="get_dataset"),
    path("api/datasets_by_task/<str:task_id>", data_api.get_dataset_for_task, name="get_dataset_for_task"),
    path("api/organizer/<str:organizer_id>", data_api.get_organizer, name="get_organizer"),
    path("api/role", data_api.get_role, name="get_role"),
    path("api/task/<str:task_id>/user/<str:user_id>", data_api.get_user, name="get_user"),
    path(
        "api/task/<str:task_id>/user/<str:user_id>/refresh-docker-images",
        data_api.update_docker_images,
        name="get_updated_docker_images",
    ),
    path(
        "api/count-of-team-submissions/<str:task_id>",
        organizer_api.get_count_of_team_submissions,
        name="get_count_of_team_submissions",
    ),
    path(
        "api/count-of-missing-reviews/<str:task_id>",
        organizer_api.get_count_of_missing_reviews,
        name="get_count_of_missing_reviews",
    ),
    path(
        "api/task/<str:task_id>/user/<str:user_id>/software/running/<str:force_cache_refresh>",
        data_api.get_running_software,
        name="get_running_software",
    ),
    path("api/task/<str:task_id>/public-submissions", data_api.public_submissions, name="public_submissions"),
    path(
        "api/task/<str:task_id>/submission-details/<str:user_id>/<str:display_name>",
        data_api.public_submission,
        name="public_submission",
    ),
    path("api/review/<str:dataset_id>/<str:vm_id>/<str:run_id>", data_api.get_review, name="get_review"),
    path(
        "api/registration/add_registration/<str:vm_id>/<str:task_id>",
        data_api.add_registration,
        name="add_registration",
    ),
    path(
        "api/submissions-for-task/<str:task_id>/<str:user_id>/<str:submission_type>",
        data_api.submissions_for_task,
        name="submissions_for_task",
    ),
    path("api/tirex-components", data_api.tirex_components, name="tirex_components"),
    path("api/tirex-snippet", data_api.get_snippet_to_run_components, name="get_snippet_to_run_components"),
    path(
        "api/snippets-for-tirex-components",
        data_api.get_snippet_to_run_components,
        name="get_snippet_to_run_components",
    ),
    path("api/re-ranking-datasets/<str:task_id>", data_api.reranking_datasets, name="reranking_datasets"),
    path("api/submissions-of-user/<str:vm_id>", data_api.submissions_of_user, name="submissions_of_user"),
    path(
        "api/add_software_submission_git_repository/<str:task_id>/<str:vm_id>",
        vm_api.add_software_submission_git_repository,
        name="add_software_submission_git_repository",
    ),
    path(
        "api/get_software_submission_git_repository/<str:task_id>/<str:vm_id>",
        vm_api.get_software_submission_git_repository,
        name="get_software_submission_git_repository",
    ),
    path("api/token/<str:vm_id>", vm_api.get_token, name="get_token"),
    path(
        "api/import-submission/<str:task_id>/<str:vm_id>/<str:submission_type>/<str:s_id>",
        data_api.import_submission,
        name="import_submission",
    ),
    path("diffir/<str:task_id>/<int:topk>/<str:run_id_1>/<str:run_id_2>", diffir_api.diffir, name="diffir"),
    path(
        "serp/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/<int:topk>/<str:run_id>",
        serp_api.serp,
        name="serp",
    ),
]

app_name = "tira"
