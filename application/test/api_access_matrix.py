from utils_for_testing import route_to_test
from datetime import datetime

#Used for some tests
now = datetime.now().strftime("%Y%m%d")

ADMIN = 'tira_reviewer'
GUEST = ''
PARTICIPANT = 'tira_vm_PARTICIPANT-FOR-TEST-1'

API_ACCESS_MATRIX = [
    route_to_test(
        url_pattern='',
        params=None,
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task',
        params=None,
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='tasks',
        params=None,
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>',
        params={'task_id': 'this-task-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 404,
            GUEST: 404,
            PARTICIPANT: 404,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>',
        params={'task_id': 'shared-task-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/dataset/<str:dataset_id>',
        params={'task_id': 'shared-task-1', 'dataset_id': 'this-dataset-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 404,
            GUEST: 404,
            PARTICIPANT: 404,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/dataset/<str:dataset_id>',
        params={'task_id': 'shared-task-1', 'dataset_id': f'dataset-1-{now}-training'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/dataset/<str:dataset_id>',
        params={'task_id': 'shared-task-1', 'dataset_id': f'dataset-2-{now}-test'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip',
        params={'task_id': 'shared-task-1', 'dataset_id': f'dataset-1-{now}-training', 'vm_id': 'example_participant', 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302, # TODO: Look at this again. Should be 405?
            PARTICIPANT: 302, # TODO: Look at this again. Should be 405?
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip',
        params={'task_id': 'shared-task-1', 'dataset_id': f'dataset-1-{now}-training', 'vm_id': PARTICIPANT.split('_')[-1], 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302, # TODO: Look at this again. Should be 405?
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip',
        params={'task_id': 'shared-task-1', 'dataset_id': f'dataset-2-{now}-test', 'vm_id': 'example_participant', 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip',
        params={'task_id': 'shared-task-1', 'dataset_id': f'dataset-2-{now}-test', 'vm_id': PARTICIPANT.split('_')[-1], 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'participant-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 302,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'participant-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 302,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>',
        params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/run/<str:run_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'dataset_id': f'dataset-1-{now}-training', 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/run/<str:run_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'dataset_id': f'dataset-2-{now}-test', 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
           PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/run/<str:run_id>',
        params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1], 'dataset_id': f'dataset-1-{now}-training', 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/run/<str:run_id>',
        params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1], 'dataset_id': f'dataset-2-{now}-test', 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200, # TODO: This should definitively be 302? As it is a test dataset that was not unblinded?
        },
    ),
    route_to_test(
        url_pattern='request_vm',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='login',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='logout',
        params={},
        group_to_expected_status_code={
            ADMIN: 302,
            GUEST: 302,
            PARTICIPANT: 302,
       },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/add_software/vm',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/add_software/vm',
        params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/add_software/docker',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/add_software/docker',
        params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/save_software/docker/<str:docker_software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'docker_software_id': 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/save_software/docker/<str:docker_software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1], 'docker_software_id': 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/save_software/vm/<str:software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'software_id': 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/save_software/vm/<str:software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1], 'software_id': 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/delete_software/vm/<str:software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'software_id': 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/delete_software/vm/<str:software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1], 'software_id': 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/delete_software/docker/<str:docker_software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'software_id': 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/delete_software/docker/<str:docker_software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1], 'software_id': 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/upload/<str:dataset_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant', 'dataset_id': 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302
        },
    ),
    route_to_test(
        url_pattern='task/<str:task_id>/vm/<str:vm_id>/upload/<str:dataset_id>',
        params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1], 'dataset_id': 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200
        },
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_info',
        params={'vm_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    # Skip for the moment, takes too long. Maybe mock later?
    #route_to_test(
    #    url_pattern='grpc/<str:vm_id>/vm_info',
    #    params={'vm_id': PARTICIPANT.split('_')[-1]},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #    },
    #),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_state',
        params={'vm_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_state',
        params={'vm_id': PARTICIPANT.split('_')[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_start',
        params={'vm_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    # Skip for the moment, takes too long. Maybe mock later?
    #route_to_test(
    #    url_pattern='grpc/<str:vm_id>/vm_start',
    #    params={'vm_id': PARTICIPANT.split('_')[-1]},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 302,
    #    },
    #),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_shutdown',
        params={'vm_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    # Skip for the moment, takes too long. Maybe mock later?
    #route_to_test(
    #    url_pattern='grpc/<str:vm_id>/vm_shutdown',
    #    params={'vm_id': PARTICIPANT.split('_')[-1]},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #    },
    #),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_stop',
        params={'vm_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    # Skip for the moment, takes too long. Maybe mock later?
    #route_to_test(
    #    url_pattern='grpc/<str:vm_id>/vm_stop',
    #    params={'vm_id': PARTICIPANT.split('_')[-1]},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #    },
    #),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/run_abort',
        params={'vm_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    # Skip for the moment, takes too long. Maybe mock later?
    #route_to_test(
    #    url_pattern='grpc/<str:vm_id>/run_abort',
    #    params={'vm_id': PARTICIPANT.split('_')[-1]},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #    },
    #),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/vm_running_evaluations',
        params={'vm_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    # Skip for the moment, takes too long. Maybe mock later?
    #route_to_test(
    #    url_pattern='grpc/<str:vm_id>/vm_running_evaluations',
    #    params={'vm_id': PARTICIPANT.split('_')[-1]},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #    },
    #),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/get_running_evaluations',
        params={'vm_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/get_running_evaluations',
        params={'vm_id': PARTICIPANT.split('_')[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='grpc/<str:task_id>/<str:vm_id>/run_execute/vm/<str:software_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'does-not-exist', 'software_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    # TODO Add later
    #route_to_test(
    #    url_pattern='grpc/<str:task_id>/<str:vm_id>/run_execute/vm/<str:software_id>',
    #    params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1], 'software_id': f'software-of-{PARTICIPANT.split("_")[-1]}'},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        GUEST: 200,
    #    },
    #),
    route_to_test(
        url_pattern='grpc/<str:task_id>/<str:vm_id>/run_execute/docker/<str:dataset_id>/<str:docker_software_id>/<str:docker_resources>',
        params={'task_id': 'shared-task-1', 'vm_id': 'does-not-exist', 'dataset_id': 'does-not-exist', 'docker_software_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
        },
    ),
    route_to_test(
        url_pattern='grpc/<str:task_id>/<str:vm_id>/run_execute/docker/<str:dataset_id>/<str:docker_software_id>/<str:docker_resources>',
        params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1], 'dataset_id': 'does-not-exist', 'docker_software_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
        },
    ),
    route_to_test(
        url_pattern='grpc/<str:vm_id>/run_eval/<str:dataset_id>/<str:run_id>',
        params={'vm_id': 'does-not-exist', 'dataset_id': f'dataset-1-{now}-training', 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302
        },
    ),
    route_to_test(
        url_pattern='grpc/<str:task_id>/<str:user_id>/stop_docker_software/<str:run_id>',
        params={'user_id': 'example_participant', 'task_id': f'shared-task-1', 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302 # Was error
        },
    ),
    route_to_test(
        url_pattern='tira-admin',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/reload/vms',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/reload/datasets',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/reload/tasks',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/create-vm',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/modify-vm',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/edit-task/<str:task_id>',
        params={'task_id': 'shared-task-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/delete-task/<str:task_id>',
        params={'task_id': 'task-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/add-dataset',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/import-irds-dataset',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/edit-dataset/<str:dataset_id>',
        params={'dataset_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/delete-dataset/<str:dataset_id>',
        params={'dataset_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/add-organizer/<str:organizer_id>',
        params={'organizer_id': 'organizer-id-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/edit-organizer/<str:organizer_id>',
        params={'organizer_id': 'organizer-id-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/edit-review/<str:dataset_id>/<str:vm_id>/<str:run_id>',
        params={'dataset_id': 'dataset-does-not-exist', 'vm_id': 'vm-id-does-not-exist', 'run_id': 'run-id-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='tira-admin/create-group/<str:vm_id>',
        params={'vm_id': 'vm-id-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='publish/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>',
        params={'dataset_id': 'dataset-does-not-exist', 'vm_id': 'vm-id-does-not-exist', 'run_id': 'run-id-does-not-exist', 'value': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302, # TODO: Make consistent.
        },
    ),
    route_to_test(
        url_pattern='blind/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>',
        params={'dataset_id': 'dataset-does-not-exist', 'vm_id': 'vm-id-does-not-exist', 'run_id': 'run-id-does-not-exist', 'value': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405
        },
    ),
    route_to_test(
        url_pattern='api/evaluations/<str:task_id>/<str:dataset_id>',
        params={'task_id': 'task-does-not-exist', 'dataset_id': 'dataset-id-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200, # TODO Make consistent with "api/evaluation/<str:vm_id>/<str:run_id>"
        },
    ),
    route_to_test(
        url_pattern='api/evaluation/<str:vm_id>/<str:run_id>',
        params={'vm_id': 'example-participant', 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,  # TODO Make consistent with "api/evaluations/<str:task_id>/<str:dataset_id>"
        },
    ),
    route_to_test(
        url_pattern='api/submissions/<str:task_id>/<str:dataset_id>',
        params={'task_id': 'task-id-does-not-exist', 'dataset_id': 'dataset-id-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200, # TODO: Add more fine-grained tests, as admin gets different response
            GUEST: 200
        },
    ),
    route_to_test(
        url_pattern='api/ova-list',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
        },
    ),
    route_to_test(
        url_pattern='api/host-list',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
        },
    ),
    route_to_test(
        url_pattern='api/organizer-list',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
        },
    ),
    route_to_test(
        url_pattern='api/task-list',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
        },
    ),
    route_to_test(
        url_pattern='api/task/<str:task_id>',
        params={'task_id': 'task-id-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
        },
    ),
    route_to_test(
        url_pattern='api/dataset/<str:dataset_id>',
        params={'dataset_id': 'dataset-id-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
        },
    ),
    route_to_test(
        url_pattern='api/datasets_by_task/<str:task_id>',
        params={'task_id': 'task-id-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
        },
    ),
    route_to_test(
        url_pattern='api/organizer/<str:organizer_id>',
        params={'organizer_id': 'organizer-id-id-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
        },
    ),
    route_to_test(
        url_pattern='api/role',
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
        },
    ),
    route_to_test(
        url_pattern='api/task/<str:task_id>/user/<str:user_id>',
        params={'task_id': 'task-id-does-not-exist', 'user_id': 'user-id-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200, # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
        },
    ),
    route_to_test(
        url_pattern='api/task/<str:task_id>/user/<str:user_id>/refresh-docker-images',
        params={'task_id': 'task-id-does-not-exist', 'user_id': 'user-id-does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200, # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
        },
    ),
    route_to_test(
        url_pattern='api/task/<str:task_id>/user/<str:user_id>/software/running/<str:force_cache_refresh>',
        params={'task_id': 'task-id-does-not-exist', 'user_id': 'user-id-does-not-exist', 'force_cache_refresh': 'ignore'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200, # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
        },
    ),
    route_to_test(
        url_pattern='api/review/<str:dataset_id>/<str:vm_id>/<str:run_id>',
        params={'dataset_id': 'dataset-id-does-not-exist', 'vm_id': 'example_participant', 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
        },
    ),
    route_to_test(
        url_pattern='api/review/<str:dataset_id>/<str:vm_id>/<str:run_id>',
        params={'dataset_id': f'dataset-1-{now}-training', 'vm_id': 'example_participant', 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302, # TODO: Is this inconsistent with api/review/<str:dataset_id>/<str:vm_id>/<str:run_id> above?
        },
    ),
    
    
    # TODO: The following methods return 50X at the moment, we should improve the setup so that it returns 200. But for the moment 50X is enough to separate authenticated from unauthenticated.
    route_to_test(
        url_pattern='tira-admin/reload-data',
        params={},
        group_to_expected_status_code={
            ADMIN: 500,
            GUEST: 405,
        },
        hide_stdout=True
    ),
    route_to_test(
        url_pattern='tira-admin/reload-runs/<str:vm_id>',
        params={'vm_id': 'does-not-exist'},
        group_to_expected_status_code={
            ADMIN: 500,
            GUEST: 405,
        },
        hide_stdout=True
    ),
    route_to_test(
        url_pattern='tira-admin/archive-vm',
        params={},
        group_to_expected_status_code={
            ADMIN: 501,
            GUEST: 405,
        },
    ),
    route_to_test(
        url_pattern='tira-admin/create-task',
        params={},
        group_to_expected_status_code={
            ADMIN: 501,
            GUEST: 405,    
        },
    ),
    route_to_test(
        url_pattern='api/registration/add_registration/<str:vm_id>/<str:task_id>',
        params={'task_id': 'shared-task-1', 'vm_id': 'example_participant'},
        group_to_expected_status_code={
            ADMIN: 500,
            GUEST: 500, # TODO: Would we expect an 404 here?
        },
        body='{"group": "X"}',
    ),

    # Some commands that delete stuff must be executed as last
    route_to_test(
        url_pattern='grpc/<str:vm_id>/run_delete/<str:dataset_id>/<str:run_id>',
        params={'vm_id': 'does-not-exist', 'dataset_id': f'dataset-1-{now}-training', 'run_id': 'run-1'},
        group_to_expected_status_code={
            ADMIN: 202,
            GUEST: 302,
        }
    ),
]


def access_matrix_for_user(user):
    ret = []
    for i in API_ACCESS_MATRIX:
        if user not in i[2]:
            continue
        params = i[2][user]['params']
        expected_status_code = i[2][user]['expected_status_code']
        
        ret += [(i[0], i[1], params, expected_status_code, i[3])]
    return ret

