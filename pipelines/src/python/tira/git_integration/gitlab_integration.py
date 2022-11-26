#!/usr/bin/env python3
import gitlab
import os
import uuid
import string
from subprocess import check_output

def read_creds(name):
    return open('/etc/tira-git-credentials/' + name).read().strip()

def gitlab_client():
    return gitlab.Gitlab('https://' + os.environ['CI_SERVER_HOST'], private_token=read_creds('GITCREDENTIALPRIVATETOKEN'))

def clean_job_suffix(ret):
    if "[32;1m$ env|grep 'TIRA' > task.env" in ret:
        ret = ret.split("[32;1m$ env|grep 'TIRA' > task.env")[0]
    if "section_end:" in ret:
        ret = ret.split("section_end:")[0]

    return ret.strip()

def clean_job_output(ret):
    ret = ''.join(filter(lambda x: x in string.printable, ret.strip()))
    if '$ eval "${TIRA_COMMAND_TO_EXECUTE}"[0;m' in ret:
        return clean_job_suffix(ret.split('$ eval "${TIRA_COMMAND_TO_EXECUTE}"[0;m')[1])
    elif '$ eval "${TIRA_EVALUATION_COMMAND_TO_EXECUTE}"[0;m' in ret:
        return clean_job_suffix(ret.split('$ eval "${TIRA_EVALUATION_COMMAND_TO_EXECUTE}"[0;m')[1])
    else:
        raise ValueError('The format of the output seems to be changed...\n\n' + ret)

def clean_job_command(ret):
    ret = ''.join(filter(lambda x: x in string.printable, ret.strip()))
    
    if '$ echo "${TIRA_COMMAND_TO_EXECUTE}"[0;m' in ret and '[32;1m$ eval "${TIRA_COMMAND_TO_EXECUTE}"' in ret:
        return ret.split('$ echo "${TIRA_COMMAND_TO_EXECUTE}"[0;m')[1].split('[32;1m$ eval "${TIRA_COMMAND_TO_EXECUTE}"')[0].strip()
    if '$ echo "${TIRA_EVALUATION_COMMAND_TO_EXECUTE}"[0;m' in ret and '[32;1m$ eval "${TIRA_EVALUATION_COMMAND_TO_EXECUTE}"' in ret:
        return ret.split('$ echo "${TIRA_EVALUATION_COMMAND_TO_EXECUTE}"[0;m')[1].split('[32;1m$ eval "${TIRA_EVALUATION_COMMAND_TO_EXECUTE}"')[0].strip()

    raise ValueError('The format of the output seems to be changed...\n\n' + ret)

def get_job(name):
    gl = gitlab_client()
    gl_project = gl.projects.get(int(os.environ['CI_PROJECT_ID']))
    gl_pipeline = gl_project.pipelines.get(int(os.environ['CI_PIPELINE_ID']))
    
    for job in gl_pipeline.jobs.list():
        if job.name == name:
            return gl_project.jobs.get(job.id)

    raise ValueError('I could not find the job trace.')

def job_trace(name):
    return clean_job_output(get_job(name).trace().decode('UTF-8'))
    
def job_command(name):
    return clean_job_command(get_job(name).trace().decode('UTF-8'))

def run_prototext(run_id, job_name):
    inputRun = os.environ['TIRA_RUN_ID'] if ('evaluate-software-result' == job_name) else 'none'
    software_id = os.environ['TIRA_SOFTWARE_ID'] if ('run-user-software' == job_name) else os.environ['TIRA_EVALUATION_SOFTWARE_ID']

    return '''softwareId: "''' + str(software_id) + '''"
runId: "'''+ run_id + '''"
inputDataset: "''' + os.environ['TIRA_DATASET_ID'] + '''"
inputRun: "''' + inputRun + '''"
downloadable: false
deleted: false
taskId: "''' + os.environ['TIRA_TASK_ID'] + '''"
accessToken: "''' + str(uuid.uuid4()) + '''"'''

def persist_tira_metadata_for_job(run_dir, run_id, job_name):
    with open(os.path.join(run_dir, 'run.prototext'), 'w') as f:
        f.write(run_prototext(run_id, job_name))

    with open(os.path.join(run_dir, 'file-list.txt'), 'wb') as f:
        file_list = check_output(['tree', '-ahv', os.path.join(run_dir, 'output')])
        f.write(file_list)

    with open(os.path.join(run_dir, 'stdout.txt'), 'w') as f:
        f.write(job_trace(job_name) + '\n')

    with open(os.path.join(run_dir, 'stderr.txt'), 'w') as f:
        f.write('################################################################\n# Executed Command\n################################################################\n'+  job_command(job_name) + '\n################################################################\n')

    with open(os.path.join(run_dir, 'size.txt'), 'wb') as f:
        f.write(check_output(['bash', '-c', '(du -sb "' + run_dir + '" && du -hs "' +  run_dir + '") | cut -f1']))
        f.write(check_output(['bash', '-c', 'find "' + os.path.join(run_dir, 'output') + '" -type f -exec cat {} + | wc -l']))
        f.write(check_output(['bash', '-c', 'find "' + os.path.join(run_dir, 'output') + '" -type f | wc -l']))
        f.write(check_output(['bash', '-c', 'find "' + os.path.join(run_dir, 'output') + '" -type d | wc -l']))

def yield_all_running_pipelines():
    gl = gitlab_client()
    gl_project = gl.projects.get(int(os.environ['CI_PROJECT_ID']))
    for status in ['scheduled', 'running', 'pending', 'created', 'waiting_for_resource', 'preparing']:
        for pipeline in gl_project.pipelines.list(status=status):
            yield (pipeline.ref + '---started-').split( '---started-')[0]


def delete_branch_of_repository():
    gl = gitlab_client()
    gl_project = gl.projects.get(int(os.environ['CI_PROJECT_ID']))
    gl_project.branches.delete(os.environ['TIRA_GIT_ID'])


if __name__ == '__main__':
    print(list(yield_all_running_pipelines()))
#    print('#####################################################################')
#    print(job_command('run-user-software') + '\n\n')
#    print(job_trace('run-user-software'))
#    print('\n\n\n#####################################################################')
#    print(job_command('evaluate-software-result') + '\n\n')
#    print(job_trace('evaluate-software-result'))

