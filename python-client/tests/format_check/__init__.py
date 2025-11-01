from pathlib import Path

from tira.check_format import FormatMsgType

_ERROR = FormatMsgType.ERROR
_OK = FormatMsgType.OK
_WARN = FormatMsgType.WARN

RESOURCES = Path(__file__).parent.parent / "resources"
VALID_RUN_OUTPUT = RESOURCES / "ranking-outputs"
VALID_QREL_PATH = RESOURCES / "valid-qrels"
VALID_RUN_WITH_METADATA_OUTPUT = RESOURCES / "ranking-with-metadata"
RUN_OUTPUT_WITH_TOO_FEW_QUERIES = RESOURCES / "ranking-output-invalid-too-few-queries"
RUN_OUTPUT_WITH_DUPLICATE_DOCUMENTS = RESOURCES / "ranking-output-invalid-duplicate-documents"
RUN_OUTPUT_WITH_TOO_FEW_COLUMNS = RESOURCES / "ranking-output-invalid-too-few-columns"
EMPTY_OUTPUT = RESOURCES / "input-run-01" / "1"
LSR_BENCHMARK_INPUTS = RESOURCES / "example-datasets" / "learned-sparse-retrieval"
IDEOLOGY_AND_POWER_PREDICTIONS = RESOURCES / "ideology-and-power-predictions"
IDEOLOGY_AND_POWER_LABELS = RESOURCES / "ideology-and-power-labels"
MAWSA_PROBLEMS = RESOURCES / "multi-author-writing-style-analysis-problems"
MAWSA_SOLUTIONS = RESOURCES / "multi-author-writing-style-analysis-solutions"
MAWSA_TRUTHS = RESOURCES / "multi-author-writing-style-analysis-truths"
IR_DOCUMENT_OUTPUT = RESOURCES / "valid-document-processor"
IR_DATASET = RESOURCES / "valid-irds-corpus"
LIGTHNING_IR_DOCUMENT_EMBEDDINGS = RESOURCES / "lightning-ir" / "document-embeddings"
LIGTHNING_IR_QUERY_EMBEDDINGS = RESOURCES / "lightning-ir" / "query-embeddings"
TEXT_ALIGNMENT_CORPUS_VALID_1 = RESOURCES / "text-alignment" / "1"
TEXT_ALIGNMENT_CORPUS_VALID_2 = RESOURCES / "text-alignment" / "2"
TEXT_ALIGNMENT_CORPUS_INVALID = RESOURCES / "text-alignment" / "invalid"
TEXT_ALIGNMENT_FEATURES_VALID = RESOURCES / "text-alignment" / "features"
TSV_OUTPUT_WITH_VARYING_COLUMNS = RESOURCES / "tsv-varying-columns"
TSV_OUTPUT_VALID = RESOURCES / "tsv-valid"
AGGREGATED_RESULTS_OUTPUT_VALID = RESOURCES / "aggregated-results-correct"
IR_METADATA_SINGLE_VALID = RESOURCES / "valid-single-ir-metadata"
IR_METADATA_INVALID = RESOURCES / "invalid-ir-metadata"
IR_METADATA_MULTIPLE_VALID = RESOURCES / "valid-multiple-ir-metadata"
IR_QUERY_OUTPUT = RESOURCES / "query-processing-outputs" / "query-segmentation"
JSONL_OUTPUT_VALID = RESOURCES / "jsonl-valid"
GEN_IR_SIM_OUTPUT_VALID = RESOURCES / "gen-ir-sim-valid"
JSONL_GZ_OUTPUT_VALID = RESOURCES / "jsonl-valid-gz"
TOUCHE_IMAGE_RETRIEVAL = RESOURCES / "touche-image-retrieval-valid"
JSONL_OUTPUT_INVALID = RESOURCES / "jsonl-invalid"
STYLE_CHANGE_CORPUS_VALID = RESOURCES / "pan24-style-change-detection"
STYLE_CHANGE_PREDICTIONS_VALID = RESOURCES / "pan24-style-change-detection-prediction"
