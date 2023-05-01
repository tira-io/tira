import logging
import time

from tira.forms import *
import tira.tira_model as model
from tira.checks import check_permissions, check_resources_exist
from tira.views import add_context

from django.http import JsonResponse, HttpResponse
from django.conf import settings
from os.path import abspath
from pathlib import Path
from tira.endpoints.diffir_api import load_irds_metadata_of_task

logger = logging.getLogger("tira")

@add_context
@check_permissions
def serp(request, context, vm_id, dataset_id, task_id, run_id):
    from tira.util import run_cmd_as_documented_background_process
    import tira.model as modeldb
    #podman --storage-opt mount_program=/usr/bin/fuse-overlayfs run -v /mnt/ceph:/mnt/ceph:ro -ti webis/tira-application:0.0.45-diffir diffir --dataset cranfield  /mnt/ceph/tira/data/runs/cranfield-20230107-training/tira-ir-starter/2023-02-13-12-40-07/output/run.txt

    if request.method == 'GET':
        try:
            run = model.get_run(dataset_id=None, vm_id=None, run_id=run_id)
            run_file = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / \
                       vm_id / run_id / 'output' / 'run.txt'
            serp_file = Path(settings.TIRA_ROOT) / "state" / "serp" / "version-0.0.1" / "runs" / dataset_id / vm_id / run_id / "serp.html"
            serp_dir = (serp_file / "..").resolve()
            Path.mkdir(serp_dir, parents=True, exist_ok=True)
            
            if not run_file.is_file():
                raise ValueError(f'Error: The expected file {run_file} does not exist.')

            if serp_file.is_file():
                return HttpResponse(open(serp_file).read())

            irds_id = load_irds_metadata_of_task(task_id, run['dataset'])['ir_datasets_id']
            image = model.get_dataset(run['dataset'])['irds_docker_image']
            command = [
                ['sudo', 'podman', '--storage-opt', 'mount_program=/usr/bin/fuse-overlayfs', 'run',
                 '-v', f'{serp_dir}:/output-tira-tmp/',
                 '--entrypoint', 'sh', image, '-c', f'diffir --dataset {irds_id} --web $outputDir/run.txt > /tmp/run.html && mv /tmp/run.html /output-tira-tmp/serp.html']
            ]

            descriptions = ['### RUN diffir']

            process_id = run_cmd_as_documented_background_process(cmd=command, vm_id=vm_id, task_id=task_id,
                                                            title=f'Render SERP for run  {run_id}',
                                                            descriptions=descriptions)

            while True:
                time.sleep(2)
                running_process = modeldb.BackendProcess.objects.get(id=process_id)
                if running_process.exit_code is not None:
                    return HttpResponse(open(serp_file).read())
        except Exception as e:
            logger.exception(e)
            logger.exception(e)
            return JsonResponse({"status": "0", "message": f"Encountered an exception: {e}"})
