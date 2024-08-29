import logging
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, JsonResponse

from tira.checks import check_permissions
from tira.endpoints.diffir_api import doc_file_for_run
from tira.views import add_context

logger = logging.getLogger("tira")


@add_context
@check_permissions
def serp(request, context, vm_id, dataset_id, task_id, run_id, topk):
    # podman --storage-opt mount_program=/usr/bin/fuse-overlayfs run -v /mnt/ceph:/mnt/ceph:ro -ti webis/tira-application:0.0.45-diffir diffir --dataset cranfield  /mnt/ceph/tira/data/runs/cranfield-20230107-training/tira-ir-starter/2023-02-13-12-40-07/output/run.txt

    if request.method == "GET":
        try:
            run_file = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / vm_id / run_id / "output" / "run.txt"

            if not run_file.is_file():
                raise ValueError(f"Error: The expected file {run_file} does not exist.")

            try:
                from diffir.run import diff_from_local_data
            except Exception as e:
                logger.exception(e)
                raise ValueError("Could not load dependency diffir")

            doc_file = doc_file_for_run(vm_id, dataset_id, task_id, run_id)
            if doc_file and doc_file.is_file():
                _, rendered_serp = diff_from_local_data(
                    [str(run_file.resolve())], [str(doc_file)], cli=False, web=True, print_html=False, topk=topk
                )

                return HttpResponse(rendered_serp)
        except Exception as e:
            print(e)
            logger.exception(e)
            return JsonResponse({"status": "1", "message": f"Encountered an exception: {e}"})
