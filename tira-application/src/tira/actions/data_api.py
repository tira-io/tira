import logging
from tira.forms import *
from django.conf import settings

include_navigation = True if settings.DEPLOYMENT == "legacy" else False

logger = logging.getLogger("tira")
logger.info("ajax_routes: Logger active")

