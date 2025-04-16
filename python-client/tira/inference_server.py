import importlib.util
import json
import logging
import os
import sys
from contextlib import contextmanager
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Dict, List, Union
from urllib.parse import parse_qs, urlparse

######################################
# START OF: HTTP response server #####
######################################

_STATUS_OK = {"Status": "OK"}
_STATUS_INTERNAL_ERROR = {"Status": "Internal error"}
_STATUS_BAD_REQUEST = {"Status": "Bad request"}

_predict = None


def _set_predict_function(predict: Callable):
    global _predict
    _predict = predict


def _handle_input(input_list: List) -> Dict:
    if _predict is None or not callable(_predict):
        return _STATUS_INTERNAL_ERROR

    if len(input_list) > 0:
        try:
            result = _predict(input_list)
        except RuntimeError as e:
            logging.error(f"Exception during handling of input '{input_list}':\n" + str(e))
            result = None
        if result is None or not isinstance(result, list):
            response = _STATUS_INTERNAL_ERROR
        else:
            response = _STATUS_OK
            response["output"] = result
    else:
        response = _STATUS_BAD_REQUEST

    return response


class InferenceServer(BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")  # for local development
        self.end_headers()

    def do_GET(self):
        logging.info(self.command)

        query = parse_qs(urlparse(self.path).query)
        payload_list = query.get("payload", None)

        input_list = None
        response = None

        if payload_list is not None:
            try:
                input_list = [json.loads(element) for element in payload_list]
            except json.JSONDecodeError:
                response = _STATUS_BAD_REQUEST

        if response is None and input_list is not None:
            response = _handle_input(input_list)

        self._set_headers()
        response_string = (json.dumps(response) + "\n").encode("utf-8")
        self.wfile.write(response_string)

    def do_POST(self):
        logging.info(self.command)

        length = int(self.headers.get("content-length"))
        payload = self.rfile.read(length)
        payload_string = payload.decode("utf-8", errors="ignore")

        # ensure list format
        if not payload_string.startswith("[") or not payload_string.endswith("]"):
            payload_string = "[" + payload_string + "]"

        input_list = None
        response = None
        try:
            input_list = json.loads(payload_string)
        except json.JSONDecodeError:
            response = _STATUS_BAD_REQUEST

        if response is None and input_list is not None:
            response = _handle_input(input_list)

        self._set_headers()
        response_string = (json.dumps(response) + "\n").encode("utf-8")
        self.wfile.write(response_string)

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        # Send allow-origin header for preflight POST XHRs.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.end_headers()

    # silence console log messages
    def log_message(self, format, *args):
        pass


####################################
# END OF: HTTP response server #####
####################################


def run_inference_server(base_module: str, absolute_path: str, internal_port: int = 8001, loglevel: int = logging.INFO):
    # logging
    log_filename = "inference_server_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
    _setup_logging(log_filename=log_filename, loglevel=loglevel)

    # load module and import predict function
    with _add_to_path(os.path.dirname(absolute_path)):
        predict = _load_predict_from_imported_module(module_name=base_module, absolute_path=absolute_path)
    if predict is None:
        sys.exit("unable to import predict predict function. See log file for details.")
    _set_predict_function(predict=predict)

    # start HTTP server
    server_address = ("", internal_port)
    httpd = HTTPServer(server_address, InferenceServer)
    logging.info(
        "serving at %s:%d" % (len(server_address[0]) > 0 and server_address[0] or "localhost", server_address[1])
    )
    # console output for safety
    print(
        "[%s] serving at %s:%d"
        % (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            len(server_address[0]) > 0 and server_address[0] or "localhost",
            server_address[1],
        )
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


def _setup_logging(log_filename: str, loglevel: int = logging.INFO):
    log_folder = "logs"

    if not os.path.isdir(log_folder):
        os.makedirs(log_folder)

    log_file = os.path.join(log_folder, log_filename)

    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s %(message)s", filename=log_file, level=loglevel, datefmt="%Y-%m-%d %H:%M:%S"
    )


def _load_predict_from_imported_module(module_name: str, absolute_path: str = None) -> "Union[Callable, None]":
    if module_name in sys.modules:
        logging.warning(f"{module_name!r} already in sys.modules")
        module = importlib.import_module(module_name)
        try:
            predict = getattr(module, "predict")
        except AttributeError:
            logging.error(f"No function 'predict' found in {module_name!r}")
            return None
    elif absolute_path is not None:
        spec = importlib.util.spec_from_file_location(module_name, absolute_path)
        if spec is not None:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            logging.info(f"{module_name!r} has been imported")
            try:
                predict = getattr(module, "predict")
            except AttributeError:
                logging.error(f"No function 'predict' found in {module_name!r}")
                return None
        else:
            logging.error(f"can't find the {module_name!r} module")
            return None
    else:
        logging.error(f"can't find the {module_name!r} module")
        return None

    return predict


@contextmanager
def _add_to_path(p):
    old_path = sys.path.copy()
    try:
        sys.path.insert(0, p)
        yield
    finally:
        sys.path = old_path
