from pathlib import Path

from tira.check_format import FormatMsgType

_ERROR = FormatMsgType.ERROR
_OK = FormatMsgType.OK
_WARN = FormatMsgType.WARN

RESOURCES = Path(__file__).parent.parent / "resources"
VALID_RUN_OUTPUT = RESOURCES / "ranking-outputs"
RUN_OUTPUT_WITH_TOO_FEW_QUERIES = RESOURCES / "ranking-output-invalid-too-few-queries"
RUN_OUTPUT_WITH_DUPLICATE_DOCUMENTS = RESOURCES / "ranking-output-invalid-duplicate-documents"
RUN_OUTPUT_WITH_TOO_FEW_COLUMNS = RESOURCES / "ranking-output-invalid-too-few-columns"
EMPTY_OUTPUT = RESOURCES / "input-run-01" / "1"
IR_QUERY_OUTPUT = RESOURCES / "query-processing-outputs" / "query-segmentation"
