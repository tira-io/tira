import logging
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
    if request.method == 'GET':
        try:
            from diffir import diff
            run = model.get_run(dataset_id=None, vm_id=None, run_id=run_id)
            run_file = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / \
                       vm_id / run_id / 'output' / 'run.txt'

            if not run_file.is_file():
                raise ValueError(f'Error: The expected file {run_file} does not exist.')

            irds_id = load_irds_metadata_of_task(task_id, run['dataset'])['ir_datasets_id']
            config = {
                "dataset": irds_id, "measure": "qrel", "metric": "nDCG@10", "topk": 10,
                "weight": {"weights_1": None, "weights_2": None}
            }
            _, ret = diff([abspath(run_file)], config=config, cli=False, web=True, print_html=False)

            return HttpResponse(ret)
        except Exception as e:
            logger.exception(e)
            return JsonResponse({"status": "0", "message": f"Encountered an exception: {e}"})
