from tira.urls import urlpatterns

from mockito import when, mock, unstub
import inspect
from copy import deepcopy
import os
import io
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
import json
from tira.tira_model import model as tira_model

#Used for some tests
now = datetime.now().strftime("%Y%m%d")
from pathlib import Path
import shutil
from django.core.management import call_command


def set_up_tira_environment():
    call_command('flush', interactive=False)
    shutil.rmtree(Path('tira-root'))
    Path('tira-root/model/virtual-machines/').mkdir(parents=True, exist_ok=True)
    Path('tira-root/model/virtual-machine-hosts').mkdir(parents=True, exist_ok=True)
    Path('tira-root/model/tasks/').mkdir(parents=True, exist_ok=True)
    Path('tira-root/model/users/').mkdir(parents=True, exist_ok=True)
    Path('tira-root/data/runs/dataset-1/example_participant/run-1').mkdir(parents=True, exist_ok=True)
    open('tira-root/model/virtual-machines/virtual-machines.txt', 'w').write('')
    open('tira-root/model/virtual-machine-hosts/virtual-machine-hosts.txt', 'w').write('')
    open('tira-root/model/users/users.prototext', 'w').write('')

    tira_model.edit_organizer('organizer', 'organizer', 'years', 'web', [])
    tira_model.edit_organizer('organizer-2', 'organizer-2', 'years', 'web', [])
    tira_model.edit_organizer('EXAMPLE-ORGANIZER', 'EXAMPLE_ORGANIZER', 'years', 'web', [])
    
    
    tira_model.add_vm('master-vm-for-task-1', 'user_name', 'initial_user_password', 'ip', 'host', '123', '123')
    tira_model.add_vm('example_participant', 'user_name', 'initial_user_password', 'ip', 'host', '123', '123')
    tira_model.add_vm('PARTICIPANT-FOR-TEST-1', 'user_name', 'initial_user_password', 'ip', 'host', '123', '123')
    
    tira_model.create_task('task-of-organizer-1', 'task_name', 'task_description', False, 'master-vm-for-task-1', 'EXAMPLE-ORGANIZER',
                           'website', False, False, False, 'help_command', '', '')
    
    tira_model.create_task('shared-task-1', 'task_name', 'task_description', False, 'master-vm-for-task-1', 'organizer',
                           'website', False, False, False, 'help_command', '', '')

    tira_model.add_dataset('shared-task-1', 'dataset-1', 'training', 'dataset-1', 'upload-name')
    tira_model.add_dataset('shared-task-1', 'dataset-2', 'test', 'dataset-2', 'upload-name')
    tira_model.add_software(task_id='shared-task-1', vm_id='PARTICIPANT-FOR-TEST-1')
        
    with open('tira-root/data/runs/dataset-1/example_participant/run-1/run.prototext', 'w') as f:
        f.write(f'\nsoftwareId: "upload"\nrunId: "run-1"\ninputDataset: "dataset-1-{now}-training"\ndownloadable: true\ndeleted: false\n')
        
    tira_model.add_run(dataset_id='dataset-1', vm_id='example_participant', run_id='run-1')

def mock_request(groups, url_pattern, method='GET', body=None, params=None):
    if 'DISRAPTOR_APP_SECRET_KEY' not in os.environ:
        os.environ['DISRAPTOR_APP_SECRET_KEY'] = 'my-disraptor-key'
    ret = mock()
    ret.headers = {
        'X-Disraptor-App-Secret-Key': 'my-disraptor-key',
        'X-Disraptor-User': 'ignored-user.',
        'X-Disraptor-Groups': groups,
    }
    ret.path_info = '/' + url_pattern
    
    if params and 'organizer_id' in params and '<str:organizer_id>' in ret.path_info:
        ret.path_info = ret.path_info.replace('<str:organizer_id>', params['organizer_id'])
    
    ret.META = {
        'CSRF_COOKIE': 'aasa',
    }
    ret.current_app = 'tira'
    if method:
        ret.method = method
    if body:
        ret.body = body
    
    return ret


def method_for_url_pattern(url_pattern):
    method_bound_to_url_pattern = None
    
    for pattern in urlpatterns:
        if str(url_pattern) == str(pattern.pattern):
            method_bound_to_url_pattern = pattern.callback

    assert method_bound_to_url_pattern, f'No method is bound to pattern "{url_pattern}".'
    
    return method_bound_to_url_pattern


def route_to_test(url_pattern, params, group_to_expected_status_code, method='GET', hide_stdout=False, body=None):
    metadata_for_groups = {}
    
    for group, expected_status_code in group_to_expected_status_code.items():
        params_for_group = deepcopy({} if not params else params)
        params_for_group['request'] = mock_request(group, url_pattern, method=method, body=body, params=params)
        
        metadata_for_groups[group] = {'params': params_for_group, 'expected_status_code': expected_status_code}
    
    return (url_pattern, method_for_url_pattern(url_pattern), metadata_for_groups, hide_stdout)


def execute_method_behind_url_and_return_status_code(method_bound_to_url_pattern, request, hide_stdout):
    if hide_stdout:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            ret = method_bound_to_url_pattern(**request)
    else:
        ret = method_bound_to_url_pattern(**request)
    
    if str(type(ret)) == "<class 'django.http.response.Http404'>":
        return 404
    return ret.status_code


def assert_all_url_patterns_are_tested(tested_url_patterns):
    tested_url_patterns = set(tested_url_patterns)
    for url_pattern in urlpatterns:
        assert str(url_pattern.pattern) in tested_url_patterns, f'The pattern "{url_pattern.pattern}" is not tested.'

