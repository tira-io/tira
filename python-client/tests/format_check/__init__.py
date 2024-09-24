from pathlib import Path

from tira.check_format import FormatMsgType

_ERROR = FormatMsgType.ERROR
_OK = FormatMsgType.OK
_WARN = FormatMsgType.WARN

RESOURCES = Path(__file__).parent.parent / "resources"
VALID_RUN_OUTPUT = RESOURCES / "ranking-outputs"
EMPTY_OUTPUT = RESOURCES / "input-run-01" / "1"
IR_QUERY_OUTPUT = RESOURCES / "query-processing-outputs" / "query-segmentation"
