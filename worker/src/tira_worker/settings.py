import logging
import os

import yaml
from pyaml_env import parse_config

# Open Config
_CONF_PATH = os.environ.get("TIRA_WORKER_CONFIG")
logging.info(f"Load settings from {_CONF_PATH}.")
_config = parse_config(_CONF_PATH, default_value=None, loader=yaml.FullLoader)

# Read Settings
# - Distributed Queue
QUEUE_BROKER_URL = _config["queue_broker_url"]
QUEUE_RESULTS_BACKEND_URL = _config["queue_results_backend_url"]
# - TIRA API
TIRA_API_KEY = _config["tira_api_key"]

# Delete the remaining config
del _config
