from django.test import TestCase
from utils_for_testing import route_to_test, assert_all_url_patterns_are_tested, execute_method_behind_url_and_return_status_code
from parameterized import parameterized
import json
from tira.tira_model import model as tira_model
from datetime import datetime

#Used for some tests
now = datetime.now().strftime("%Y%m%d")

ADMIN = 'tira_reviewer'
ROUTES_TO_TEST = [
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
        url_pattern='grpc/<str:vm_id>/run_delete/<str:dataset_id>/<str:run_id>',
        params={'vm_id': 'does-not-exist', 'dataset_id': f'dataset-1-{now}-training', 'run_id': 'run-1'},
        groups=ADMIN,
        expected_status_code=202
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

    
]

#ROUTES_TO_TEST = ROUTES_TO_TEST[-1:]

class TestAccessibilityOfEndpointsForAdminUser(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tested_urls = []
        tira_model.edit_organizer('organizer', 'organizer', 'years', 'web', [])
        tira_model.add_vm('master-vm-for-task-1', 'user_name', 'initial_user_password', 'ip', 'host', '123', '123')
        tira_model.add_vm('example_participant', 'user_name', 'initial_user_password', 'ip', 'host', '123', '123')
        tira_model.create_task('shared-task-1', 'task_name', 'task_description', False, 'master-vm-for-task-1', 'organizer',
                'website', False, False, False, 'help_command', '', '')
        tira_model.add_dataset('shared-task-1', 'dataset-1', 'training', 'dataset-1', 'upload-name')
        tira_model.add_dataset('shared-task-1', 'dataset-2', 'test', 'dataset-2', 'upload-name')
        
        with open('tira-root/data/runs/dataset-1/example_participant/run-1/run.prototext', 'w') as f:
            f.write(f'\nsoftwareId: "upload"\nrunId: "run-1"\ninputDataset: "dataset-1-{now}-training"\ndownloadable: true\ndeleted: false\n')
        
        tira_model.add_run(dataset_id='dataset-1', vm_id='example_participant', run_id='run-1')
        
        

    @parameterized.expand(ROUTES_TO_TEST)
    def test_route(self, url_pattern, method_bound_to_url_pattern, request, expected_status_code, hide_stdout):
        status_code = execute_method_behind_url_and_return_status_code(
            method_bound_to_url_pattern,
            request,
            hide_stdout
        )
        
        assert status_code == expected_status_code, \
            f'Expected response for url_pattern {url_pattern} is {expected_status_code}. But I got {status_code}'

        self.tested_urls += [url_pattern]

    @classmethod
    def tearDownClass(cls):
        assert_all_url_patterns_are_tested(cls.tested_urls)    

