from utils_for_testing import route_to_test
from datetime import datetime

#Used for some tests
now = datetime.now().strftime("%Y%m%d")

ADMIN = 'tira_reviewer'

API_ACCESS_MATRIX = [
    route_to_test(
        url_pattern='',
        params=None,
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task',
        params=None,
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='tasks',
        params=None,
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>',
        params={'task_id': 'this-task-does-not-exist'},
        groups=ADMIN,
        expected_status_code=404
    ),
    route_to_test(
        url_pattern='task/<str:task_id>',
        params={'task_id': 'shared-task-1'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/dataset/<str:dataset_id>',
        params={'task_id': 'shared-task-1', 'dataset_id': 'this-dataset-does-not-exist'},
        groups=ADMIN,
        expected_status_code=404
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/dataset/<str:dataset_id>',
        params={'task_id': 'shared-task-1', 'dataset_id': f'dataset-1-{now}-training'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/dataset/<str:dataset_id>',
        params={'task_id': 'shared-task-1', 'dataset_id': f'dataset-2-{now}-test'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip',
        params={'task_id': 'shared-task-1', 'dataset_id': f'dataset-1-{now}-training', 'vm_id': 'example_participant', 'run_id': 'run-1'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip',
        params={'task_id': 'shared-task-1', 'dataset_id': f'dataset-2-{now}-test', 'vm_id': 'example_participant', 'run_id': 'run-1'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'participant-does-not-exist'},
        groups=ADMIN,
        expected_status_code=302
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/run/<str:run_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'dataset_id': f'dataset-1-{now}-training', 'run_id': 'run-1'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/run/<str:run_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'dataset_id': f'dataset-2-{now}-test', 'run_id': 'run-1'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='request_vm',
        params={},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='login',
        params={},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='logout',
        params={},
        groups=ADMIN,
        expected_status_code=302
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/add_software/vm',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/add_software/docker',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/save_software/docker/<str:docker_software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'docker_software_id': 0},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/save_software/vm/<str:software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'software_id': 0},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/delete_software/vm/<str:software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'software_id': 0},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/delete_software/docker/<str:docker_software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'software_id': 0},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/upload/<str:dataset_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'dataset_id': 0},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_info',
        params={'vm_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_state',
        params={'vm_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_start',
        params={'vm_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_shutdown',
        params={'vm_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_stop',
        params={'vm_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/run_abort',
        params={'vm_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_running_evaluations',
        params={'vm_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/get_running_evaluations',
        params={'vm_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='grpc/<str:task_id>/<str:vm_id>/run_execute/vm/<str:software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'does-not-exist', 'software_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='grpc/<str:task_id>/<str:vm_id>/run_execute/docker/<str:dataset_id>/<str:docker_software_id>/<str:docker_resources>',
        params={'task_id': 'shared-task-1', 'vm_id': 'does-not-exist', 'dataset_id': 'does-not-exist', 'docker_software_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/run_eval/<str:dataset_id>/<str:run_id>',
        params={'vm_id': 'does-not-exist', 'dataset_id': f'dataset-1-{now}-training', 'run_id': 'run-1'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='grpc/<str:task_id>/<str:user_id>/stop_docker_software/<str:run_id>',
        params={'user_id': 'example_participant', 'task_id': f'shared-task-1', 'run_id': 'run-1'},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='tira-admin',
        params={},
        groups=ADMIN,
        expected_status_code=200
    ),
    route_to_test(
        url_pattern='tira-admin/reload/vms',
        params={},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/reload/datasets',
        params={},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/reload/tasks',
        params={},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/create-vm',
        params={},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/modify-vm',
        params={},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/edit-task/<str:task_id>',
        params={'task_id': 'shared-task-1'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/delete-task/<str:task_id>',
        params={'task_id': 'task-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/add-dataset',
        params={},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/import-irds-dataset',
        params={},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/edit-dataset/<str:dataset_id>',
        params={'dataset_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/delete-dataset/<str:dataset_id>',
        params={'dataset_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/add-organizer/<str:organizer_id>',
        params={'organizer_id': 'organizer-id-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/edit-organizer/<str:organizer_id>',
        params={'organizer_id': 'organizer-id-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/edit-review/<str:dataset_id>/<str:vm_id>/<str:run_id>',
        params={'dataset_id': 'dataset-does-not-exist', 'vm_id': 'vm-id-does-not-exist', 'run_id': 'run-id-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='tira-admin/create-group/<str:vm_id>',
        params={'vm_id': 'vm-id-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='publish/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>',
        params={'dataset_id': 'dataset-does-not-exist', 'vm_id': 'vm-id-does-not-exist', 'run_id': 'run-id-does-not-exist', 'value': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='blind/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>',
        params={'dataset_id': 'dataset-does-not-exist', 'vm_id': 'vm-id-does-not-exist', 'run_id': 'run-id-does-not-exist', 'value': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/evaluations/<str:task_id>/<str:dataset_id>',
        params={'task_id': 'task-does-not-exist', 'dataset_id': 'dataset-id-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/evaluation/<str:vm_id>/<str:run_id>',
        params={'vm_id': 'example-participant', 'run_id': 'run-1'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/submissions/<str:task_id>/<str:dataset_id>',
        params={'task_id': 'task-id-does-not-exist', 'dataset_id': 'dataset-id-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/ova-list',
        params={},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/host-list',
        params={},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/organizer-list',
        params={},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/task-list',
        params={},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/task/<str:task_id>',
        params={'task_id': 'task-id-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/dataset/<str:dataset_id>',
        params={'dataset_id': 'dataset-id-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/datasets_by_task/<str:task_id>',
        params={'task_id': 'task-id-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/organizer/<str:organizer_id>',
        params={'organizer_id': 'organizer-id-id-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/role',
        params={},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/task/<str:task_id>/user/<str:user_id>',
        params={'task_id': 'task-id-does-not-exist', 'user_id': 'user-id-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/task/<str:task_id>/user/<str:user_id>/refresh-docker-images',
        params={'task_id': 'task-id-does-not-exist', 'user_id': 'user-id-does-not-exist'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/task/<str:task_id>/user/<str:user_id>/software/running/<str:force_cache_refresh>',
        params={'task_id': 'task-id-does-not-exist', 'user_id': 'user-id-does-not-exist', 'force_cache_refresh': 'ignore'},
        groups=ADMIN,
        expected_status_code=200,
    ),
    route_to_test(
        url_pattern='api/review/<str:dataset_id>/<str:vm_id>/<str:run_id>',
        params={'dataset_id': 'dataset-id-does-not-exist', 'vm_id': 'example_participant', 'run_id': 'run-1'},
        groups=ADMIN,
        expected_status_code=200,
    ),    
    
    # TODO: The following methods return 50X at the moment, we should improve the setup so that it returns 200. But for the moment 50X is enough to separate authenticated from unauthenticated.
    route_to_test(
        url_pattern='tira-admin/reload-data',
        params={},
        groups=ADMIN,
        expected_status_code=500,
        hide_stdout=True
    ),
    route_to_test(
        url_pattern='tira-admin/reload-runs/<str:vm_id>',
        params={'vm_id': 'does-not-exist'},
        groups=ADMIN,
        expected_status_code=500,
        hide_stdout=True
    ),
    route_to_test(
        url_pattern='tira-admin/archive-vm',
        params={},
        groups=ADMIN,
        expected_status_code=501,
    ),
    route_to_test(
        url_pattern='tira-admin/create-task',
        params={},
        groups=ADMIN,
        expected_status_code=501,
    ),
    route_to_test(
        url_pattern='api/registration/add_registration/<str:vm_id>/<str:task_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant'},
        groups=ADMIN,
        expected_status_code=500,
        body='{"group": "X"}',
    ),

    # Some commands that delete stuff must be executed as last
    route_to_test(
        url_pattern='grpc/<str:vm_id>/run_delete/<str:dataset_id>/<str:run_id>',
        params={'vm_id': 'does-not-exist', 'dataset_id': f'dataset-1-{now}-training', 'run_id': 'run-1'},
        groups=ADMIN,
        expected_status_code=202
    ),
]


def access_matrix_for_user(user):
    ret = []
    for i in API_ACCESS_MATRIX:
        ret += [i]
    return ret

