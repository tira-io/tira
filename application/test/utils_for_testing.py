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
dataset_1 = f'dataset-1-{now}-training'
dataset_2 = f'dataset-2-{now}-test'
dataset_meta = f'meta-dataset-{now}-test'
software_non_public = 'docker-software-1'
software_public = 'docker-software-2'
software_with_inputs = 'docker-software-with_inputs'

from pathlib import Path
import shutil
from django.core.management import call_command
import tira.model as modeldb


def set_up_tira_filesystem():
    shutil.rmtree(Path('tira-root'), ignore_errors=True)

    call_command('flush', interactive=False)

    Path('tira-root/model/virtual-machines/').mkdir(parents=True, exist_ok=True)
    Path('tira-root/model/virtual-machine-hosts').mkdir(parents=True, exist_ok=True)
    Path('tira-root/model/tasks/').mkdir(parents=True, exist_ok=True)
    Path('tira-root/model/users/').mkdir(parents=True, exist_ok=True)
    Path('tira-root/data/runs/dataset-1/example_participant/run-1').mkdir(parents=True, exist_ok=True)
    Path('tira-root/data/runs/dataset-of-organizer/example_participant/run-of-organizer').mkdir(parents=True,
                                                                                                exist_ok=True)
    open('tira-root/model/virtual-machines/virtual-machines.txt', 'w').write('')
    open('tira-root/model/virtual-machine-hosts/virtual-machine-hosts.txt', 'w').write('')
    open('tira-root/model/users/users.prototext', 'w').write('')

def set_up_tira_environment():
    set_up_tira_filesystem()

    tira_model.edit_organizer('organizer', 'organizer', 'years', 'web', [])
    tira_model.edit_organizer('organizer-2', 'organizer-2', 'years', 'web', [])
    tira_model.edit_organizer('EXAMPLE-ORGANIZER', 'EXAMPLE_ORGANIZER', 'years', 'web', [])
    evaluator = modeldb.Evaluator.objects.update_or_create(evaluator_id=f'big-evaluator-for-everything')[0]
    tira_model.add_vm('master-vm-for-task-1', 'user_name', 'initial_user_password', 'ip', 'host', '123', '123')
    tira_model.add_vm('example_participant', 'user_name', 'initial_user_password', 'ip', 'host', '123', '123')
    tira_model.add_vm('participant-1', 'user_name', 'initial_user_password', 'ip', 'host', '123', '123')
    tira_model.add_vm('participant-2', 'user_name', 'initial_user_password', 'ip', 'host', '123', '123')
    tira_model.add_vm('PARTICIPANT-FOR-TEST-1', 'user_name', 'initial_user_password', 'ip', 'host', '123', '123')

    tira_model.create_task('task-of-organizer-1', 'task_name', 'task_description', False, 'master-vm-for-task-1', 'EXAMPLE-ORGANIZER',
                           'website', False, False, False, 'help_command', '', '')
    
    tira_model.create_task('shared-task-1', 'task_name', 'task_description', False, 'master-vm-for-task-1', 'organizer',
                           'website', False, False, False, 'help_command', '', '')

    tira_model.add_dataset('shared-task-1', 'dataset-1', 'training', 'dataset-1', 'upload-name')

    tira_model.add_dataset('shared-task-1', 'dataset-2', 'test', 'dataset-2', 'upload-name')
    tira_model.add_dataset('shared-task-1', 'dataset-not-published', 'training', 'dataset-published', 'upload-name')

    tira_model.add_dataset('shared-task-1', 'meta-dataset', 'test', 'meta-dataset', 'upload-name')
    tira_model.add_dataset('task-of-organizer-1', 'dataset-of-organizer', 'training', 'dataset-of-organizer', 'upload-name')


    d = modeldb.Dataset.objects.get(dataset_id=f'dataset-not-published-{now}-training')
    d.is_confidential = True
    d.save()
    del d

    d = modeldb.Dataset.objects.get(dataset_id=f'dataset-of-organizer-{now}-training')
    d.is_confidential = True
    d.save()
    del d

    tira_model.add_dataset('task-of-organizer-1', 'dataset-without-a-name', 'training', '', 'upload-name')
    tira_model.add_software(task_id='shared-task-1', vm_id='PARTICIPANT-FOR-TEST-1')

    modeldb.DockerSoftware.objects.create(
        display_name=software_non_public, vm=modeldb.VirtualMachine.objects.get(vm_id='PARTICIPANT-FOR-TEST-1'),
        task=modeldb.Task.objects.get(task_id='shared-task-1'), deleted=False)

    modeldb.DockerSoftware.objects.create(
        display_name=software_public, vm=modeldb.VirtualMachine.objects.get(vm_id='PARTICIPANT-FOR-TEST-1'),
        task=modeldb.Task.objects.get(task_id='shared-task-1'), public_image_name='some image identifier', deleted=False)

    modeldb.DockerSoftware.objects.create(
        display_name=software_with_inputs, vm=modeldb.VirtualMachine.objects.get(vm_id='PARTICIPANT-FOR-TEST-1'),
        task=modeldb.Task.objects.get(task_id='shared-task-1'), deleted=False)

    s1_tmp = modeldb.DockerSoftware.objects.filter(
        vm=modeldb.VirtualMachine.objects.get(vm_id='PARTICIPANT-FOR-TEST-1'),
        task=modeldb.Task.objects.get(task_id='shared-task-1'), display_name=software_with_inputs)[0]

    s2_tmp = modeldb.DockerSoftware.objects.filter(
        vm=modeldb.VirtualMachine.objects.get(vm_id='PARTICIPANT-FOR-TEST-1'),
        task=modeldb.Task.objects.get(task_id='shared-task-1'), display_name=software_public)[0]

    s3_tmp = modeldb.DockerSoftware.objects.filter(
        vm=modeldb.VirtualMachine.objects.get(vm_id='PARTICIPANT-FOR-TEST-1'),
        task=modeldb.Task.objects.get(task_id='shared-task-1'), display_name=software_non_public)[0]

    es1 = modeldb.DockerSoftware.objects.create(
        display_name='software_e1', vm=modeldb.VirtualMachine.objects.get(vm_id='example_participant'),
        task=modeldb.Task.objects.get(task_id='shared-task-1'), deleted=False)

    modeldb.DockerSoftwareHasAdditionalInput.objects.create(position=1, docker_software=s1_tmp,
                                                            input_docker_software=s2_tmp)
    modeldb.DockerSoftwareHasAdditionalInput.objects.create(position=3, docker_software=s1_tmp,
                                                            input_docker_software=s2_tmp)
    modeldb.DockerSoftwareHasAdditionalInput.objects.create(position=2, docker_software=s1_tmp,
                                                            input_docker_software=s3_tmp)

    d = modeldb.Dataset.objects.get(dataset_id=dataset_meta)
    d.meta_dataset_of = dataset_1 + ',' + dataset_2
    d.save()

    k_1 = 2.0
    k_2 = 1.0

    d = modeldb.Dataset.objects.get(dataset_id=dataset_1)
    for i in range(10):

        for participant in ['example_participant', 'participant-1', 'participant-2']:
            run_id = f'run-{i}-{participant}'
            Path(f'tira-root/data/runs/dataset-1/{participant}/{run_id}/').mkdir(parents=True, exist_ok=True)
            with open(f'tira-root/data/runs/dataset-1/{participant}/{run_id}/run.prototext', 'w') as f:
                f.write(f'\nsoftwareId: "upload"\nrunId: "{run_id}"\ninputDataset: "dataset-1-{now}-training"\ndownloadable: true\ndeleted: false\n')

            tira_model.add_run(dataset_id='dataset-1', vm_id=participant, run_id=run_id)
            run = modeldb.Run.objects.get(run_id=run_id)
            if participant == 'example_participant':
                run.docker_software = es1
                run.save()

            eval_run = modeldb.Run.objects.create(run_id=f'run-{i}-{participant}-eval', input_run=run, input_dataset=d,
                                                  evaluator=evaluator)
            # SERPS of participant-1 are unblinded and published
            modeldb.Review.objects.create(run=eval_run, published=participant in {'example_participant', 'participant-1'}, blinded=participant != 'participant-1')

            if i > 8:
                modeldb.Review.objects.update_or_create(run_id=run_id, defaults={'published': participant in {'example_participant', 'participant-1'}, 'blinded': participant != 'participant-1'})

            modeldb.Evaluation.objects.create(measure_key='k-1', measure_value=k_1, run=eval_run)
            modeldb.Evaluation.objects.create(measure_key='k-2', measure_value=k_2, run=eval_run)

            k_1 -= 0.1
            k_2 += 0.1

    d = modeldb.Dataset.objects.get(dataset_id=dataset_2)
    for i in range(2):
        for participant in ['participant-1', 'participant-2']:
            run_id = f'run-ds2-{i}-{participant}'
            Path(f'tira-root/data/runs/dataset-2/{participant}/{run_id}/').mkdir(parents=True, exist_ok=True)
            with open(f'tira-root/data/runs/dataset-2/{participant}/{run_id}/run.prototext', 'w') as f:
                f.write(
                    f'\nsoftwareId: "upload"\nrunId: "{run_id}"\ninputDataset: "dataset-2-{now}-test"\ndownloadable: true\ndeleted: false\n')

            tira_model.add_run(dataset_id='dataset-2', vm_id=participant, run_id=run_id)
            run = modeldb.Run.objects.get(run_id=run_id)

            eval_run = modeldb.Run.objects.create(run_id=f'run-ds2-{i}-{participant}-eval', input_run=run,
                                                  input_dataset=d, evaluator=evaluator)

            modeldb.Review.objects.create(run=eval_run, published=participant == 'participant-1')
            modeldb.Evaluation.objects.create(measure_key='k-1', measure_value=k_1, run=eval_run)
            modeldb.Evaluation.objects.create(measure_key='k-2', measure_value=k_2, run=eval_run)

            k_1 -= 0.1
            k_2 += 0.1

    with open('tira-root/data/runs/dataset-of-organizer/example_participant/run-of-organizer/run.prototext', 'w') as f:
        f.write(f'\nsoftwareId: "upload"\nrunId: "run-of-organizer"\ninputDataset: "dataset-of-organizer-{now}-training"\ndownloadable: true\ndeleted: false\n')

    tira_model.add_run(dataset_id='dataset-of-organizer', vm_id='example_participant', run_id='run-of-organizer')

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

    ret.GET = {}
    
    if params and 'organizer_id' in params and '<str:organizer_id>' in ret.path_info:
        ret.path_info = ret.path_info.replace('<str:organizer_id>', params['organizer_id'])

    if params and 'dataset_id' in params and '<str:dataset_id>' in ret.path_info:
        ret.path_info = ret.path_info.replace('<str:dataset_id>', str(params['dataset_id']))

    if params and 'vm_id' in params and '<str:vm_id>' in ret.path_info:
        ret.path_info = ret.path_info.replace('<str:vm_id>', params['vm_id'])

    if params and 'run_id' in params and '<str:run_id>' in ret.path_info:
        ret.path_info = ret.path_info.replace('<str:run_id>', params['run_id'])

    if params and 'task_id' in params and '<str:task_id>' in ret.path_info:
        ret.path_info = ret.path_info.replace('<str:task_id>', params['task_id'])

    if params and 'software_name' in params and '<str:software_name>' in ret.path_info:
        ret.path_info = ret.path_info.replace('<str:software_name>', params['software_name'])

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

