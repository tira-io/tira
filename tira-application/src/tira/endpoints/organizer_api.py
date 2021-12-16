import logging

from tira.checks import actions_check_permissions, check_resources_exist
from tira.forms import *
from django.http import JsonResponse
from django.conf import settings

import tira.tira_model as model

include_navigation = True if settings.DEPLOYMENT == "legacy" else False

logger = logging.getLogger("tira")
logger.info("ajax_routes: Logger active")

# ---------------------------------------------------------------------
#   Review actions
# ---------------------------------------------------------------------

@actions_check_permissions({"tira", "admin"})
@check_resources_exist('json')
def publish(request, vm_id, dataset_id, run_id, value):
    value = (True if value == 'true' else False)
    if request.method == 'GET':
        status = model.update_review(dataset_id, vm_id, run_id, published=value)
        if status:
            context = {"status": "0", "published": value,  "message": f"Published is now: {value}"}
        else:
            context = {"status": "1", "published": (not value),  "message": f"Published is now: {value}"}

        return JsonResponse(context)


@actions_check_permissions({"tira", "admin"})
@check_resources_exist('json')
def blind(request, vm_id, dataset_id, run_id, value):
    value = (False if value == 'false' else True)

    if request.method == 'GET':
        status = model.update_review(dataset_id, vm_id, run_id, blinded=value)
        if status:
            context = {"status": "0", "blinded": value,  "message": f"Blinded is now: {value}"}
        else:
            context = {"status": "1", "blinded": (not value),  "message": f"Blinded is now: {value}"}
        return JsonResponse(context)

