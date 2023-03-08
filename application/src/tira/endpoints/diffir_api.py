import logging
import json
from tira.forms import *
import tira.tira_model as model
from tira.checks import check_permissions, check_resources_exist
from tira.views import add_context

from django.http import JsonResponse, HttpResponse
from django.conf import settings
from os.path import abspath
from pathlib import Path

logger = logging.getLogger("tira")


def load_irds_metadata_of_task(task, dataset):
    dataset_type = 'training-datasets' if dataset.endswith('-training') else 'test-datasets'

    metadata_file = Path(settings.TIRA_ROOT) / "data" / "datasets" / dataset_type / task / dataset / 'metadata.json'

    if not metadata_file.is_file():
        raise ValueError(f'Configuration error: The expected file {metadata_file} does not exist.')

    return json.load(open(metadata_file, 'r'))


@check_resources_exist('json')
@add_context
def diffir(request, context, task_id, run_id_1, run_id_2):
    if request.method == 'GET':
        try:
            from diffir.run import diff
            run_1 = model.get_run(dataset_id=None, vm_id=None, run_id=run_id_1)
            run_2 = model.get_run(dataset_id=None, vm_id=None, run_id=run_id_2)

            if run_1['dataset'] != run_2['dataset']:
                raise ValueError(f'Run {run_id_1} has dataset {run_1["dataset"]} while run {run_id_2} has dataset ' +
                                 f'{run_2["dataset"]}. Expected both to be identical')

            run_dir = Path(settings.TIRA_ROOT) / "data" / "runs" / run_1['dataset']
            run_1_file = run_dir / run_1['vm'] / run_id_1 / 'output' / 'run.txt'
            run_2_file = run_dir / run_2['vm'] / run_id_2 / 'output' / 'run.txt'

            if not run_1_file.is_file():
                raise ValueError(f'Error: The expected file {run_1_file} does not exist.')

            if not run_2_file.is_file():
                raise ValueError(f'Error: The expected file {run_2_file} does not exist.')

            irds_id = load_irds_metadata_of_task(task_id, run_1['dataset'])['ir_datasets_id']
            config = {
                "dataset": irds_id, "measure": "qrel", "metric": "nDCG@10", "topk": 10,
                "weight": {"weights_1": None, "weights_2": None}
            }
            _, ret = diff([abspath(run_1_file), abspath(run_2_file)], config=config, cli=False, web=True, print_html=False)

            return HttpResponse(ret)
        except Exception as e:
            logger.exception(e)
            return JsonResponse({"status": "0", "message": f"Encountered an exception: {e}"})
