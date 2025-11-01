import gzip
import json
import os
import re
import xml.dom.minidom
from collections.abc import Iterable
from enum import Enum
from glob import glob
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Union


class FormatMsgType(Enum):
    OK = 0
    WARN = 1
    ERROR = 2


_fmt = FormatMsgType


def fmt_message(message: str, level: _fmt) -> str:
    """
    Prints a formatted log message with a symbol indicating the status.

    Parameters:
    - message (str): The log message to display.
    - level (_fmt): The level of the message; can be _fmt.OK, _fmt.WARN, _fmt.ERROR.
    """
    symbols = {
        _fmt.OK: "\033[92m\u2713\033[0m",  # Green check mark
        _fmt.WARN: "\033[93m" + b"\xe2\x9a\xa0".decode("utf-8") + "\033[0m",  # Yellow warning
        _fmt.ERROR: "\033[91m" + b"\xe2\x9c\x96".decode("utf-8") + "\033[0m",  # Red cross
    }

    symbol = symbols[level]
    return f"{symbol} {message}"


def log_message(message: str, level: _fmt):
    """
    Prints a formatted log message with a symbol indicating the status.

    Parameters:
    - message (str): The log message to display.
    - level (_fmt): The level of the message; can be _fmt.OK, _fmt.WARN, _fmt.ERROR.
    """
    print(fmt_message(message, level))


CONF_REQUIRED_FIELDS = "required_fields"
CONF_MINIMUM_LINES = "minimum_lines"
CONF_ID_FIELD = "id_field"
CONF_VALUE_FIELD = "value_field"
CONF_MAX_SIZE_MB = "max_size_mb"
CONF_SPOT_CHECK = "spot_check"

CONFIGURATION_FIELDS = {
    CONF_REQUIRED_FIELDS: "foo",
    CONF_MINIMUM_LINES: "foo",
    CONF_ID_FIELD: "foo",
    CONF_VALUE_FIELD: "foo",
}


class FormatBase:
    def __init__(self):
        self.max_size_mb = 75
        self.spot_check = None

    def yield_next_entry(self, f: Path):
        try:
            f_size = f.stat().st_size
        except:
            raise ValueError(f"File {f} is not readable.")

        if f_size > self.max_size():
            raise ValueError(f"File {f} is too large (size {f_size} exceeds configured {self.max_size()}).")

        if str(f).endswith(".gz"):
            with gzip.open(f, "rt") as o:
                for line in o:
                    yield line.rstrip("\n")
        else:
            with open(f, "r") as o:
                for line in o:
                    yield line.rstrip("\n")

    def apply_configuration_and_throw_if_invalid(self, configuration: "Optional[dict[str, Any]]"):
        if configuration and hasattr(configuration, "__iter__") and CONF_MAX_SIZE_MB in configuration:
            self.max_size_mb = configuration[CONF_MAX_SIZE_MB]

        if configuration and hasattr(configuration, "__iter__") and CONF_SPOT_CHECK in configuration:
            self.spot_check = configuration[CONF_SPOT_CHECK]

    def all_lines(self, f: Path):
        return list(self.yield_next_entry(f))

    def max_size(self):
        return self.max_size_mb * 1024 * 1024

    def check_format(self, run_output: Path):
        return [_fmt.ERROR, "not implemented"]


class LearnedSparseRetrievalInputs(FormatBase):
    """Checks if a given output is a valid learned sparese retrieval input."""

    def apply_configuration_and_throw_if_invalid(self, configuration: "Optional[dict[str, Any]]"):
        self.docs = DocumentProcessorFormat()
        self.docs.apply_configuration_and_throw_if_invalid(configuration)

        self.queries = QueryProcessorFormat()
        self.queries.apply_configuration_and_throw_if_invalid(configuration)

    def check_format(self, run_output: Path):
        l, m = self.docs.check_format(run_output / "corpus.jsonl.gz")
        if l != _fmt.OK:
            return l, m

        l, m = self.queries.check_format(run_output / "queries.jsonl")
        if l != _fmt.OK:
            return l, m

        # TODO: IrMetadataFormat

        return [_fmt.OK, "The dataset is in the format for the lsr-benchmark."]


class RunFormat(FormatBase):
    """Checks if a given output is a valid run file."""

    def check_format(self, run_output: Path):
        if (run_output / "run.txt").exists() and (run_output / "run.txt.gz").exists():
            msg = f"Found multiple run.txt or run.txt.gz files: {os.listdir(run_output)} ."
            return [_fmt.ERROR, msg]
        if not (run_output / "run.txt").exists() and not (run_output / "run.txt.gz").exists():
            msg = "No file run.txt or run.txt.gz was found."
            try:
                msg += " Only the files " + str(os.listdir(run_output)) + " were available."
            except:
                pass
            return [_fmt.ERROR, msg]

        try:
            # maximum size of 10MB
            num_lines = 0
            lines = []
            for line in self.yield_next_entry(run_output):
                if self.spot_check and num_lines > self.spot_check:
                    break
                lines.append(line)
                num_lines += 1
        except Exception as e:
            return [_fmt.ERROR, e.args[0]]

        if len(lines) < 5:
            return [_fmt.ERROR, f"The run file contains only {len(lines)} lines, this is likely an error."]

        query_to_docs = {}
        for line in lines:
            if line["qid"] not in query_to_docs:
                query_to_docs[line["qid"]] = set()
            if line["docno"] in query_to_docs[line["qid"]]:
                return [
                    _fmt.ERROR,
                    f'The run file has duplicate documents: the document with id "{line["docno"]}" appears multiple times for query "{line["qid"]}".',
                ]
            query_to_docs[line["qid"]].add(line["docno"])

        if len(query_to_docs.keys()) < 3:
            return [_fmt.ERROR, f"The run file has only {len(query_to_docs)} queries which is likely an error."]

        return [_fmt.OK, "The run.txt file has the correct format."]

    def parse_single_line(self, line):
        cols = re.split("\\s+", line)
        if len(cols) != 6:
            raise ValueError(
                f'Invalid line in the run file, expected 6 columns, but found a line "{line}" with {len(cols)} columns.'
            )
        qid, q0, docno, rank, score, system = cols
        try:
            rank = int(rank)
        except ValueError:
            raise ValueError(f"Could not parse the rank. Got {rank}. Line: {line}")

        try:
            score = float(score)
        except ValueError:
            raise ValueError(f"Could not parse the rank. Got {rank}. Line: {line}")

        return {"qid": qid, "q0": q0, "docno": docno, "rank": rank, "score": score, "system": system}

    def yield_next_entry(self, run_output):
        if (run_output / "run.txt").exists():
            file_path = run_output / "run.txt"
        elif (run_output / "run.txt.gz").exists():
            file_path = run_output / "run.txt.gz"
        else:
            raise ValueError("Could not find a file run.txt or run.txt.gz")

        for line in super().yield_next_entry(file_path):
            yield self.parse_single_line(line.strip())


class QrelFormat(FormatBase):
    """Checks if a given output is a valid qrel file."""

    def check_format(self, run_output: Path):
        if (run_output / "qrels.txt").exists() and (run_output / "qrels.txt.gz").exists():
            msg = f"Found multiple qrels.txt or qrels.txt.gz files: {os.listdir(run_output)} ."
            return [_fmt.ERROR, msg]
        if not (run_output / "qrels.txt").exists() and not (run_output / "qrels.txt.gz").exists():
            msg = "No unique qrels.txt file was found, only the files "
            msg += str(os.listdir(run_output)) + " were available."
            return [_fmt.ERROR, msg]

        try:
            # maximum size of 10MB
            lines = self.all_lines(run_output)
        except Exception as e:
            return [_fmt.ERROR, e.args[0]]

        if len(lines) < 10:
            return [_fmt.ERROR, f"The run file contains only {len(lines)} lines, this is likely an error."]

        query_to_docs = {}
        for line in lines:
            if line["qid"] not in query_to_docs:
                query_to_docs[line["qid"]] = set()
            if line["docno"] in query_to_docs[line["qid"]]:
                return [
                    _fmt.ERROR,
                    f'The qrel file has duplicate documents: the document with id "{line["docno"]}" appears multiple times for query "{line["qid"]}".',
                ]
            query_to_docs[line["qid"]].add(line["docno"])

        if len(query_to_docs.keys()) < 3:
            return [_fmt.ERROR, f"The run file has only {len(query_to_docs)} queries which is likely an error."]

        return [_fmt.OK, "The qrels are valid."]

    def all_lines(self, run_output):
        if (run_output / "qrels.txt").exists():
            ret = [i.strip() for i in super().all_lines(run_output / "qrels.txt")]
        elif (run_output / "qrels.txt.gz").exists():
            ret = [i.strip() for i in super().all_lines(run_output / "qrels.txt.gz")]
        else:
            raise ValueError("Could not find a file qrels.txt or qrels.txt.gz")

        ret_parsed = []
        for l in ret:
            l = l.strip()
            cols = re.split("\\s+", l)
            if len(cols) != 4:
                return [
                    _fmt.ERROR,
                    f'Invalid line in the qrel file, expected 4 columns, but found a line "{l}" with {len(cols)} columns.',
                ]
            qid, q0, docno, rel = cols
            try:
                rel = int(rel)
            except:
                raise ValueError(f"I expected that the relevance is an integer, got {rel} in line {l}")
            ret_parsed.append({"qid": qid, "q0": q0, "docno": docno, "rel": rel})
        return ret_parsed


class KeyValueFormatBase(FormatBase):
    def apply_configuration_and_throw_if_invalid(self, configuration: "Optional[dict[str, Any]]"):
        super().apply_configuration_and_throw_if_invalid(configuration)

        id_field = None
        value_field = None
        required_fields = set()
        minimum_lines = 1

        if configuration and hasattr(configuration, "__iter__"):
            if CONF_REQUIRED_FIELDS in configuration:
                required_fields = set(configuration[CONF_REQUIRED_FIELDS])
            if CONF_MINIMUM_LINES in configuration:
                minimum_lines = int(configuration[CONF_MINIMUM_LINES])

            if CONF_ID_FIELD in configuration:
                id_field = configuration[CONF_ID_FIELD]

            if CONF_VALUE_FIELD in configuration:
                value_field = configuration[CONF_VALUE_FIELD]

        self.required_fields = required_fields
        self.minimum_lines = minimum_lines
        self.id_field = id_field
        self.value_field = value_field

        if (self.id_field is None and self.value_field is not None) or (
            self.id_field is not None and self.value_field is None
        ):
            raise ValueError(
                f"Please set both id_field and value_field or none of both. Got id_field = {self.id_field} and value_field = {self.value_field}."
            )

    def has_id_and_value_field(self) -> bool:
        return self.id_field is not None and self.value_field is not None


class AggregatedResults(FormatBase):
    def check_format(self, run_output: Path):
        if not (run_output / "aggregated-results.json").exists():
            return [_fmt.ERROR, "No aggregated-results.json files."]

        try:
            val = json.load(open(run_output / "aggregated-results.json"))
        except:
            return [_fmt.ERROR, "The aggregated-results.json file is invalid json."]

        for required_field in [
            "title",
            "description",
            "ev_keys",
            "lines",
            "table_headers",
            "table_headers_small_layout",
            "table_sort_by",
        ]:
            if required_field not in val:
                return [_fmt.ERROR, "The aggregated-results.json misses the field " + required_field]

        return [_fmt.OK, "The agregated-results.json file has the correct format."]


class JsonlFormat(KeyValueFormatBase):
    """Checks if a given output is a valid jsonl file."""

    def apply_configuration_and_throw_if_invalid(self, configuration: "Optional[dict[str, Any]]"):
        if not configuration:
            configuration = {}

        if CONF_REQUIRED_FIELDS not in configuration:
            configuration[CONF_REQUIRED_FIELDS] = set()

        if CONF_MINIMUM_LINES not in configuration:
            configuration[CONF_MINIMUM_LINES] = 2

        super().apply_configuration_and_throw_if_invalid(configuration)

    def check_format(self, run_output: Path):
        try:
            lines = self.all_lines(run_output)

            if len(lines) < self.minimum_lines:
                return [_fmt.ERROR, f"The *.jsonl file contains only {len(lines)} lines, this is likely an error."]

            return [_fmt.OK, "The jsonl file has the correct format."]
        except Exception as e:
            return [_fmt.ERROR, str(e)]

    def fail_if_json_line_is_not_valid(self, line):
        for field in self.required_fields:
            if not line or field not in line:
                raise ValueError(f'The json line misses the required field "{field}": "{json.dumps(line)}".')
        if self.has_id_and_value_field():
            if not line or self.id_field not in line:
                raise ValueError(f'The json line misses the required field "{self.id_field}": "{json.dumps(line)}".')
            if not line or self.value_field not in line:
                raise ValueError(f'The json line misses the required field "{self.value_field}": "{json.dumps(line)}".')

    def yield_next_entry(self, run_output):
        if (str(run_output).endswith(".jsonl") or str(run_output).endswith(".jsonl.gz")) and run_output.is_file():
            matches = [run_output]
        else:
            matches = [
                run_output / i for i in os.listdir(run_output) if i.endswith(".jsonl") or i.endswith(".jsonl.gz")
            ]

        if len(matches) != 1:
            raise ValueError(
                "No unique *.jsonl file was found, only the files " + str(os.listdir(run_output)) + " were available."
            )

        for line in super().yield_next_entry(matches[0]):
            line = line.strip()
            try:
                parsed_line = json.loads(line)
                self.fail_if_json_line_is_not_valid(parsed_line)
                yield parsed_line
            except json.JSONDecodeError:
                raise ValueError(f'The file {matches[0]} contains a line that could not be parsed: "{line}".')


class ToucheImageRetrieval(JsonlFormat):
    def apply_configuration_and_throw_if_invalid(self, configuration: "Optional[dict[str, Any]]"):
        super().apply_configuration_and_throw_if_invalid(
            {CONF_REQUIRED_FIELDS: ["argument_id", "method", "image_id", "rank", "tag"]}
        )

    def yield_next_entry(self, run_output):
        for i in super().yield_next_entry(run_output):
            yield {
                "qid": i["argument_id"],
                "q0": "0",
                "docno": i["image_id"],
                "rank": i["rank"],
                "score": 1000 - i["rank"],
                "system": i["tag"],
            }


class LongEvalLags(FormatBase):
    def apply_configuration_and_throw_if_invalid(self, configuration: "Optional[dict[str, Any]]"):
        if not configuration or "lags" not in configuration or not configuration["lags"]:
            raise ValueError(
                'Please pass a configuration "lags" that points out on which lags an dataset should run. '
                + 'E.g., {"lags": ["lag-1", "lag-2"]}. '
                + f"I got: {configuration}"
            )

        self.lags = configuration["lags"]
        if isinstance(self.lags, str):
            self.lags = [self.lags]
        format = "run.txt"
        if "format" in configuration:
            format = configuration["format"]
        self.format = format

        self.max_size_mb = 250
        if configuration and hasattr(configuration, "__iter__") and CONF_MAX_SIZE_MB in configuration:
            self.max_size_mb = configuration[CONF_MAX_SIZE_MB]
        self.spot_check = 25000
        if configuration and hasattr(configuration, "__iter__") and CONF_SPOT_CHECK in configuration:
            self.spot_check = configuration[CONF_SPOT_CHECK]

    def check_ir_metadata(self, run_output: Path):
        if not (run_output / "ir-metadata.yml").exists():
            return _fmt.ERROR, "\n\t" + fmt_message(
                f"I expected a file ir-metadata.yml in the directory {run_output} but did not find one.", _fmt.ERROR
            )
        else:
            required_fields = {
                "tag": {"type": str, "default": "ENTER_VALUE_HERE"},
                "actor": {"team": {"type": str, "default": "ENTER_VALUE_HERE"}},
                "research goal": {"description": {"type": str, "default": "ENTER_VALUE_HERE"}},
                "platform": {"software": {"libraries": {"type": list, "default": "ENTER_VALUE_HERE"}}},
                "implementation": {"source": {"repository": {"type": str, "default": "ENTER_VALUE_HERE"}}},
                "data": {"training data": {"name": {"type": str, "default": "ENTER_VALUE_HERE"}}},
                "method": {
                    "automatic": {"type": bool, "default": "ENTER_VALUE_HERE"},
                    "indexing": {
                        "tokenizer": {"type": str, "default": "ENTER_VALUE_HERE"},
                        "stemmer": {"type": str, "default": "ENTER_VALUE_HERE"},
                        "stopwords": {"type": str, "default": "ENTER_VALUE_HERE"},
                    },
                    "retrieval": {
                        "name": {"type": str, "default": "ENTER_VALUE_HERE"},
                        "lexical": {"type": bool, "default": "ENTER_VALUE_HERE"},
                        "deep_neural_model": {"type": bool, "default": "ENTER_VALUE_HERE"},
                        "sparse_neural_model": {"type": bool, "default": "ENTER_VALUE_HERE"},
                        "single_stage_retrieval": {"type": bool, "default": "ENTER_VALUE_HERE"},
                    },
                },
            }
            return check_format(
                run_output / "ir-metadata.yml",
                "ir_metadata",
                {"required_fields": required_fields},
            )

    def check_format(self, run_output: Path):
        ret_msg = f"I will check that the data in {run_output} is valid ..."
        ret_code = _fmt.OK

        if self.check_ir_metadata(run_output)[0] != _fmt.OK:
            return _fmt.ERROR, "\n\t" + fmt_message(
                f"The file {run_output}/ir-metadata.yml is not valid. Errors: " + self.check_ir_metadata(run_output)[1],
                _fmt.ERROR,
            )

        for lag in self.lags:
            status, msg = check_format(
                run_output / lag, self.format, {CONF_MAX_SIZE_MB: self.max_size_mb, CONF_SPOT_CHECK: self.spot_check}
            )
            if status != _fmt.OK:
                ret_code = _fmt.ERROR
                ret_msg += "\n\t" + fmt_message(
                    f"I expected a run file in the subdirectory {lag}. Error: {msg}", _fmt.ERROR
                )
            else:
                ret_msg += "\n\t" + fmt_message(f"The run in subdirectory {lag} is valid.", _fmt.OK)

        ret_msg += "\n\t" + fmt_message("The file ir-metadata.yml is valid.", _fmt.OK)

        return [ret_code, ret_msg]


class PowerAndIdeologyFormat(FormatBase):
    def __init__(self, prefix_pattern, suffix_pattern, languages=None, tasks=None):
        if not languages:
            languages = [
                "at",
                "ba",
                "be",
                "bg",
                "cz",
                "dk",
                "ee",
                "es-ct",
                "es-ga",
                "es-pv",
                "es",
                "fi",
                "fr",
                "gb",
                "gr",
                "hr",
                "hu",
                "is",
                "it",
                "lv",
                "nl",
                "no",
                "pl",
                "pt",
                "rs",
                "se",
                "si",
                "tr",
                "ua",
            ]
        if not tasks:
            tasks = ["orientation", "power", "populism"]

        self.languages = languages
        self.tasks = tasks
        self.prefix_pattern = prefix_pattern
        self.suffix_pattern = suffix_pattern

    def yield_next_entry(self, f: Path):
        for language in self.languages:
            for task in self.tasks:
                matching_files = glob(
                    str(f) + "/" + self.prefix_pattern + task + "-" + language + self.suffix_pattern + ".tsv"
                )
                for file in matching_files:
                    with open(file, "rt") as f:
                        for l in f:
                            if len(l.split("\t")) != 2:
                                raise ValueError(f"Invalid tsv line in {f}. Got '" + l + "'.")
                            l = l.split("\t")
                            yield {"id": l[0], "language": language, task: "task", "label": l[1]}

    def check_format(self, run_output: Path):
        lines = list(self.all_lines(run_output))
        if len(lines) < 3:
            return [
                _fmt.ERROR,
                f"I did not find any files in the power and ideology pattern.\n\n\tThe pattern is:\n\t{self.prefix_pattern}TASK-LANGUAGE{self.suffix_pattern}.tsv",
            ]
        return [_fmt.OK, f"I found {len(lines)} entries in the ideology and power task"]


class GenIrSimulationFormat(JsonlFormat):
    def fail_if_json_line_is_not_valid(self, line):
        if "simulation" not in line:
            raise ValueError('The json line misses the required field "simulation".')
        line = line["simulation"]

        if "configuration" not in line:
            raise ValueError('The json line misses the required field "simulation.configuration".')

        if "userTurns" not in line:
            raise ValueError('The json line misses the required field "simulation.userTurns".')

    def apply_configuration_and_throw_if_invalid(self, configuration: "Optional[dict[str, Any]]"):
        super().apply_configuration_and_throw_if_invalid(configuration)

        required_fields = set()
        minimum_lines = 1

        if configuration and hasattr(configuration, "__iter__"):
            if CONF_REQUIRED_FIELDS in configuration:
                required_fields = set(configuration[CONF_REQUIRED_FIELDS])
            if CONF_MINIMUM_LINES in configuration:
                minimum_lines = int(configuration[CONF_MINIMUM_LINES])

        self.required_fields = required_fields
        self.minimum_lines = minimum_lines


class TsvFormat(KeyValueFormatBase):
    """Checks if a given output is a valid tsv file."""

    def apply_configuration_and_throw_if_invalid(self, configuration: "Optional[dict[str, Any]]"):
        if not configuration:
            configuration = {}

        if CONF_MINIMUM_LINES not in configuration:
            configuration[CONF_MINIMUM_LINES] = 5

        super().apply_configuration_and_throw_if_invalid(configuration)

    def check_format(self, run_output: Path):
        try:
            lines = self.all_lines(run_output)
        except Exception as e:
            return [_fmt.ERROR, str(e)]

        if len(lines) < self.minimum_lines:
            return [_fmt.ERROR, f"The *.tsv file contains only {len(lines)} lines, this is likely an error."]

        if len(lines[0]) < 2:
            return [_fmt.ERROR, "The *.tsv file contains only one column, this is likely an error."]

        return [_fmt.OK, "The tsv file has the correct format."]

    def yield_next_entry(self, run_output):
        matches = [i for i in os.listdir(run_output) if i.endswith(".tsv")]
        if len(matches) != 1:
            msg = "No unique *.tsv file was found, only the files "
            msg += str(os.listdir(run_output)) + " were available."
            raise ValueError(msg)

        f = run_output / matches[0]
        columns = None

        for line in super().yield_next_entry(f):
            l_parsed = line.strip().split("\t")
            if columns is None:
                columns = len(l_parsed)
            if len(l_parsed) != columns:
                raise ValueError("The *.tsv file is invalid: The number of columns varies.")
            yield l_parsed


class MultiAuthorWritingStyleAnalysis(FormatBase):
    def __init__(self, prefix):
        self.prefix = prefix

    def apply_configuration_and_throw_if_invalid(self, configuration: "Optional[dict[str, Any]]"):
        if not configuration:
            configuration = {}

        if CONF_MINIMUM_LINES not in configuration:
            configuration[CONF_MINIMUM_LINES] = 3

        self.minimum_lines = configuration[CONF_MINIMUM_LINES]

    def yield_next_entry(self, run_output):
        suffix = ".json" if self.prefix != "problem" else ".txt"
        matches = (
            glob(f"{run_output}/{self.prefix}-*{suffix}")
            + glob(f"{run_output}/**/{self.prefix}-*{suffix}")
            + glob(f"{run_output}/**/**/{self.prefix}-*{suffix}")
        )

        if len(matches) < self.minimum_lines:
            raise ValueError(
                f"There are no files matching the multi-author-style file pattern of '{self.prefix}-*{suffix}' in the directory {run_output}."
            )

        tasks = set(["easy", "medium", "hard"])

        for f in matches:
            task = [i for i in tasks if i in f]
            if len(task) != 1:
                raise ValueError("fooo")

            with open(f, "r") as fh:
                f = Path(f).relative_to(run_output)
                problem = fh.read()
                if suffix == ".json":
                    ret = {
                        "file": f,
                        "task": task[0],
                    }
                    ret.update(json.loads(problem))
                    yield ret
                else:
                    yield {
                        "file": str(f),
                        "task": task[0],
                        "problem": problem,
                        "paragraphs": problem.split("\n"),
                    }

    def check_format(self, run_output: Path):
        try:
            lines = self.all_lines(run_output)
            return [_fmt.OK, f"Valid Multi-Author-Writing-Style directory with {len(lines)} entries."]
        except Exception as e:
            return [_fmt.ERROR, str(e)]


class TextAlignmentFeaturesFormat(FormatBase):
    """
    The code was refactored from https://github.com/pan-webis-de/pan-code/blob/master/sepln09/pan09-plagiarism-detection-performance-measures.py#L276
    """

    def check_format(self, run_output: Path):
        try:
            lines = self.all_lines(run_output)
        except Exception as e:
            return [_fmt.ERROR, str(e)]

        if len(lines) < 3:
            return [
                _fmt.ERROR,
                f"The text-alignment-feature directory contains only {len(lines)} instances, this is likely an error.",
            ]

        return [_fmt.OK, "The directory has the correct format."]

    def all_lines(self, run_output):
        return self.extract_annotations_from_files(run_output, ["plagiarism", "detected-plagiarism"])

    def extract_annotations_from_file(self, xmlfile, tagnames):
        """Returns a set of plagiarism annotations from an XML file."""
        doc = xml.dom.minidom.parse(xmlfile)
        annotations = []
        if not doc.documentElement.hasAttribute("reference"):
            return annotations
        t_ref = doc.documentElement.getAttribute("reference")
        for node in doc.documentElement.childNodes:
            for tagname in tagnames:
                if (
                    node.nodeType == xml.dom.Node.ELEMENT_NODE
                    and node.hasAttribute("name")
                    and node.getAttribute("name").endswith(tagname)
                ):
                    ann = self.extract_annotation_from_node(node, t_ref)
                    if ann:
                        ann["type"] = tagname
                        annotations.append(ann)
        return annotations

    def extract_annotation_from_node(self, xmlnode, t_ref):
        """Returns a plagiarism annotation from an XML feature tag node."""
        if not (xmlnode.hasAttribute("this_offset") and xmlnode.hasAttribute("this_length")):
            return False
        t_off = int(xmlnode.getAttribute("this_offset"))
        t_len = int(xmlnode.getAttribute("this_length"))
        s_ref, s_off, s_len, ext = "", 0, 0, False
        if (
            xmlnode.hasAttribute("source_reference")
            and xmlnode.hasAttribute("source_offset")
            and xmlnode.hasAttribute("source_length")
        ):
            s_ref = xmlnode.getAttribute("source_reference")
            s_off = int(xmlnode.getAttribute("source_offset"))
            s_len = int(xmlnode.getAttribute("source_length"))
            ext = True
        return {
            "this_reference": t_ref,
            "this_offset": t_off,
            "this_length": t_len,
            "source_reference": s_ref,
            "source_offset": s_off,
            "source_length": s_len,
            "is_external": ext,
        }

    def extract_annotations_from_files(self, path, tagnames):
        """Returns a set of plagiarism annotations from XML files below path."""
        if not os.path.exists(path):
            raise ValueError(f"Path not accessible: {path}")

        annotations = []
        xmlfiles = glob(os.path.join(path, "*.xml"))
        xmlfiles.extend(glob(os.path.join(path, os.path.join("*", "*.xml"))))
        for xmlfile in xmlfiles:
            annotations += self.extract_annotations_from_file(xmlfile, tagnames)
        return annotations


class PanStyleChangeDetectionCorpusFormat(FormatBase):
    """Checks if a given directory contains a valid style-change-detection PAN corpus. An example is located here: https://pan.webis.de/clef24/pan24-web/style-change-detection.html"""

    def check_format(self, run_output: Path):
        try:
            lines = [i for i in self.yield_lines(run_output, False)]
        except Exception as e:
            return [_fmt.ERROR, str(e)]

        if len(lines) < 3:
            return [
                _fmt.ERROR,
                f"The style-change-detection directory contains only {len(lines)} instances, this is likely an error.",
            ]

        return [_fmt.OK, "The directory has the correct format."]

    def all_lines(self, run_output):
        return [i for i in self.yield_lines(run_output, True)]

    def yield_lines(self, directory, load_content):
        matches = (
            glob(f"{directory}/problem-*.txt")
            + glob(f"{directory}/*/problem-*.txt")
            + glob(f"{directory}/*/*/problem-*.txt")
            + glob(f"{directory}/*/*/*/problem-*.txt")
        )

        for i in matches:
            entry = {"id": i.split("/")[-1].replace(".txt", "")}

            if load_content:
                with open(i, "r", newline="") as f:
                    entry["text"] = f.read()

            yield entry


class PanStyleChangeDetectionPredictionFormat(FormatBase):
    """Checks if a given directory contains a valid style-change-detection PAN predictions. An example is located here: https://pan.webis.de/clef24/pan24-web/style-change-detection.html"""

    def check_format(self, run_output: Path):
        try:
            lines = [i for i in self.yield_lines(run_output, False)]
        except Exception as e:
            return [_fmt.ERROR, str(e)]

        if len(lines) < 3:
            return [
                _fmt.ERROR,
                f"The style-change-detection directory contains only {len(lines)} instances, this is likely an error.",
            ]

        return [_fmt.OK, "The directory has the correct format."]

    def all_lines(self, run_output):
        return [i for i in self.yield_lines(run_output, True)]

    def yield_lines(self, directory, load_content):
        matches = (
            glob(f"{directory}/*-problem-*.json")
            + glob(f"{directory}/*/*-problem-*.json")
            + glob(f"{directory}/*/*/*-problem-*.json")
            + glob(f"{directory}/*/*/*/*-problem-*.json")
        )

        for i in matches:
            prediction_type, problem_id = i.split("/")[-1].replace(".json", "").split("-problem-")
            entry = {"problem": problem_id, "type": prediction_type}

            if load_content:
                with open(i, "r", newline="") as f:
                    entry.update(json.loads(f.read()))

            yield entry


class TextAlignmentCorpusFormat(FormatBase):
    """Checks if a given directory contains a valid PAN text alignment corpus. The code was refactored from https://github.com/pan-webis-de/pan-code/blob/master/clef12/text-alignment/pan12-text-alignment-baseline.py#L202"""

    def check_format(self, run_output: Path):
        try:
            lines = [i for i in self.yield_lines(run_output, False)]
        except Exception as e:
            return [_fmt.ERROR, str(e)]

        if len(lines) < 3:
            return [
                _fmt.ERROR,
                f"The text-alignment directory contains only {len(lines)} instances, this is likely an error.",
            ]

        return [_fmt.OK, "The directory has the correct format."]

    def all_lines(self, run_output):
        return [i for i in self.yield_lines(run_output, True)]

    def yield_lines(self, run_output, load_content):
        matches = [i for i in os.listdir(run_output) if i.endswith("pairs")]
        if len(matches) != 1:
            msg = "No unique pair file was found, only the files "
            msg += str(os.listdir(run_output)) + " were available."
            raise ValueError(msg)

        f = run_output / matches[0]
        with open(f, "r") as tsv_file:
            for l in tsv_file:
                l_parsed = l.strip().split()
                if len(l_parsed) != 2:
                    raise ValueError("The pair file is invalid: I expect always two lines per entry.")
                entry = {}
                for k, v in zip(l_parsed, ["suspicious", "source"]):
                    entry[f"{v}_document_id"] = k.replace(".txt", "")
                    matches = (
                        glob(f"{run_output}/{k}")
                        + glob(f"{run_output}/{k}.txt")
                        + glob(f"{run_output}/*/{k}")
                        + glob(f"{run_output}/*/{k}.txt")
                    )

                    if len(matches) != 1:
                        msg = f"No unique text file was found for id {k}. Only "
                        msg += str(os.listdir(run_output)) + " were available."

                        raise ValueError(msg)
                    if load_content:
                        with open(matches[0]) as f:
                            entry[f"{v}_document_text"] = f.read()

                yield entry


class QueryProcessorFormat(JsonlFormat):
    """Checks if a given output is a valid query processor output in JSONL format."""

    def __init__(self, qid_name="qid"):
        super().__init__()
        self.qid_name = qid_name

    def apply_configuration_and_throw_if_invalid(self, configuration):
        self.minimum_lines = 1

    def fail_if_json_line_is_not_valid(self, line):
        if "qid" not in line and "query_id" not in line:
            raise ValueError('At least one of "qid" or "query_id" fields is required.')

        if "qid" in line and "query_id" in line and line["qid"] != line["query_id"]:
            raise ValueError('If both "qid" and "query_id" fields are present, they must be equal.')

    def yield_next_entry(self, run_output):
        seen_query_ids = set()

        for line in super().yield_next_entry(run_output):
            # Create a new dictionary to avoid modifying the original
            normalized_line = dict(line)

            if "qid" in line:
                query_id_value = line["qid"]
            elif "query_id" in line:
                query_id_value = line["query_id"]

            query_id_value = str(query_id_value)

            if query_id_value in seen_query_ids:
                raise ValueError(f"Query ID {query_id_value} is not unique.")
            seen_query_ids.add(query_id_value)

            # Remove redundant ID fields if they differ from the normalized name
            if "qid" in normalized_line and "qid" != self.qid_name:
                del normalized_line["qid"]
            if "query_id" in normalized_line and "query_id" != self.qid_name:
                del normalized_line["query_id"]

            normalized_line[self.qid_name] = query_id_value

            yield normalized_line


class DocumentProcessorFormat(JsonlFormat):
    """Checks if a given output is a valid document processor output in JSONL format."""

    def __init__(self, docno_name="docno"):
        super().__init__()
        self.docno_name = docno_name

    def apply_configuration_and_throw_if_invalid(self, configuration):
        super().apply_configuration_and_throw_if_invalid(configuration)
        self.minimum_lines = 1
        self.doc_ids = ["docno", "docid", "doc_id"]

    def extract_docno_or_fail(self, line):
        ret = None
        for doc_id in self.doc_ids:
            if doc_id in line and line[doc_id]:
                if ret is None or ret == line[doc_id]:
                    ret = line[doc_id]
                else:
                    raise ValueError(f"Inconsistent fields for the document identifier: {line}.")

        if ret is None:
            raise ValueError(f"At least one of {self.doc_ids} fields is required.")
        return ret

    def fail_if_json_line_is_not_valid(self, line):
        self.extract_docno_or_fail(line)

    def yield_next_entry(self, run_output):
        seen_query_ids = set()

        for line in super().yield_next_entry(run_output):
            # Create a new dictionary to avoid modifying the original
            normalized_line = dict(line)
            id_value = self.extract_docno_or_fail(normalized_line)
            for doc_id in self.doc_ids:
                if doc_id in normalized_line:
                    del normalized_line[doc_id]
            normalized_line[self.docno_name] = id_value
            yield normalized_line


class IrDatasetsCorpus(FormatBase):
    def __init__(self):
        self.docs_processor = DocumentProcessorFormat()
        self.query_processor = QueryProcessorFormat()

    def apply_configuration_and_throw_if_invalid(self, configuration):
        self.docs_processor.apply_configuration_and_throw_if_invalid(configuration)
        self.query_processor.apply_configuration_and_throw_if_invalid(configuration)

    def yield_next_entry(self, run_output):
        raise ValueError("not implemented")

    def check_format(self, run_output: Path):
        code, message = self.query_processor.check_format(Path(run_output) / "queries.jsonl")

        if code != _fmt.OK:
            return [_fmt.ERROR, f"No ir-dataset found. {message}"]

        code, message = self.docs_processor.check_format(Path(run_output) / "corpus.jsonl.gz")

        if code != _fmt.OK:
            return [_fmt.ERROR, f"No ir-dataset found. {message}"]

        return [_fmt.OK, "Valid ir-dataset found."]


class LightningIrDocumentEmbeddings(FormatBase):
    def yield_next_entry(self, run_output):
        raise ValueError("not implemented")

    def check_format(self, run_output: Path):
        for expected_file in ["doc-ids.txt", "doc-embeddings.npz"]:
            if (
                len(glob(f"{Path(run_output)}/{expected_file}")) == 0
                and len(glob(f"{Path(run_output)}/**/{expected_file}")) == 0
            ):
                return [_fmt.ERROR, f"No lightning-ir embeddings found. I expected a file {expected_file}"]
        return [_fmt.OK, "Valid lightning-ir embeddings found."]


class LightningIrQueryEmbeddings(FormatBase):
    def yield_next_entry(self, run_output):
        raise ValueError("not implemented")

    def check_format(self, run_output: Path):
        for expected_file in ["query-embeddings.npz", "query-ids.txt"]:
            if (
                len(glob(f"{Path(run_output)}/{expected_file}")) == 0
                and len(glob(f"{Path(run_output)}/**/{expected_file}")) == 0
            ):
                return [_fmt.ERROR, f"No lightning-ir embeddings found. I expected a file {expected_file}"]
        return [_fmt.OK, "Valid lightning-ir embeddings found."]


class TerrierIndex(FormatBase):
    def apply_configuration_and_throw_if_invalid(self, configuration):
        pass

    def check_format(self, run_output: Path):
        if not run_output.is_dir():
            return [_fmt.ERROR, "The directory is no valid terrier index, it misses an index directory."]

        if not (run_output / "index").is_dir():
            return [_fmt.ERROR, "The directory is no valid terrier index, it misses an index directory."]

        if not (run_output / "index" / "data.properties").is_file():
            return [_fmt.ERROR, "The directory is no valid terrier index, it misses an index/data.properties file."]

        if not (run_output / "index" / "data.meta.idx").is_file():
            return [_fmt.ERROR, "The directory is no valid terrier index, it misses an index/data.meta.idx file."]

        return [_fmt.OK, "The directory seems to be a valid pyterrier index."]

    def yield_next_entry(self, f):
        pass


class IrMetadataFormat(FormatBase):
    """Checks if a given output contains valid ir_metadata."""

    def __init__(self, positive_fields=("platform", "implementation", "resources")):
        self.positive_fields = positive_fields

    def apply_configuration_and_throw_if_invalid(self, configuration):
        self.required_fields = None
        if configuration and hasattr(configuration, "__iter__") and CONF_REQUIRED_FIELDS in configuration:
            self.required_fields = configuration[CONF_REQUIRED_FIELDS]

    def check_format(self, run_output: Path):
        try:
            lines = list(self.yield_lines(run_output))

            if self.required_fields:
                for line in lines:
                    errors = self.report_missing_fields(line["content"], self.required_fields)
                    msg = ""
                    if len(errors) > 0:
                        for error in errors:
                            msg += f"\n\t\t- {error}"
                        return [_fmt.ERROR, msg]

            if len(lines) < 1:
                return [_fmt.ERROR, "At least one valid ir_metadata file was expected, but there was none."]

            return [_fmt.OK, "The output provides valid ir_metadata."]
        except Exception as e:
            return [_fmt.ERROR, str(e)]

    def all_lines(self, run_output):
        return [i for i in self.yield_lines(run_output)]

    def report_missing_fields(self, yml_dict, required_fields, prefix=None):
        ret = []
        for k, v in required_fields.items():
            k_display = ("" if prefix is None else prefix + ".") + k
            try:
                if not yml_dict or k not in yml_dict:
                    ret.append(f"The required field {k_display} is missing.")

                    continue
            except Exception as e:
                ret.append(f"The required field {k_display} is missing.")
                continue

            check_type = "type" in v and "default" in v
            values = [yml_dict[k]] if not isinstance(yml_dict[k], list) or check_type else yml_dict[k]

            for val in values:
                if check_type:
                    if val == v["default"] or (isinstance(val, str) and v["default"] in val):
                        ret.append(f"The required field {k_display} still contains the default value {v['default']}.")
                    elif not isinstance(val, v["type"]):
                        ret.append(
                            f"The required field {k_display} has the wrong type {type(val)}. I expected {v['type']}."
                        )
                else:
                    ret.extend(self.report_missing_fields(val, v, k_display))

        return ret

    def yield_lines(self, run_output: Path):
        import yaml

        candidates = [str(run_output)]
        for pattern in ["/*.yml", "/*.yaml", "/.*.yml", "/.*.yaml"]:
            for depth in ["", "/**", "/**/**", "/.**", "/.**/**", "/.**/.**"]:
                candidates += glob(str(run_output) + depth + pattern)

        for candidate in candidates:
            if not Path(candidate).exists() or not Path(candidate).is_file():
                continue

            with open(candidate) as stream:
                try:
                    content = yaml.safe_load(stream)
                    if not content:
                        raise ValueError("The ir_metadata file is empty.")

                    if not self.required_fields:
                        at_least_one_positive_field = any(i in content for i in self.positive_fields)

                        if not at_least_one_positive_field:
                            continue
                    name = candidate.split("/")[-1]
                    if len(candidate.split("/")) > 1 and candidate.split("/")[-2].startswith("."):
                        name = str(candidate.split("/")[-2]) + "/" + name

                    yield {"name": name, "content": content}
                except yaml.YAMLError:
                    pass


FORMAT_TO_CHECK = {
    "run.txt": RunFormat,
    "*.jsonl": JsonlFormat,
    "*.tsv": TsvFormat,
    "text-alignment-corpus": TextAlignmentCorpusFormat,
    "text-alignment-features": TextAlignmentFeaturesFormat,
    "style-change-detection-corpus": PanStyleChangeDetectionCorpusFormat,
    "style-change-detection-predictions": PanStyleChangeDetectionPredictionFormat,
    "GenIR-Simulation": GenIrSimulationFormat,
    "query-processor": QueryProcessorFormat,
    "document-processor": DocumentProcessorFormat,
    "ir_metadata": IrMetadataFormat,
    "lsr-benchmark-inputs": LearnedSparseRetrievalInputs,
    "qrels.txt": QrelFormat,
    "LongEvalLags": LongEvalLags,
    "terrier-index": TerrierIndex,
    "multi-author-writing-style-analysis-problems": lambda: MultiAuthorWritingStyleAnalysis("problem"),
    "multi-author-writing-style-analysis-solutions": lambda: MultiAuthorWritingStyleAnalysis("solution-problem"),
    "multi-author-writing-style-analysis-truths": lambda: MultiAuthorWritingStyleAnalysis("truth-problem"),
    "power-and-identification-truths": lambda: PowerAndIdeologyFormat("", "-*-labels"),
    "power-and-identification-predictions": lambda: PowerAndIdeologyFormat("*", "*-predictions"),
    "touche-image-retrieval": ToucheImageRetrieval,
    "ir-dataset-corpus": IrDatasetsCorpus,
    "lightning-ir-document-embeddings": LightningIrDocumentEmbeddings,
    "lightning-ir-query-embeddings": LightningIrQueryEmbeddings,
    "aggregated-results.json": AggregatedResults,
}

SUPPORTED_FORMATS = set(sorted(list(FORMAT_TO_CHECK.keys())))


def check_format_configuration_if_valid(
    format: Union[str, Sequence[str]], configuration: "Optional[dict[str, Any]]" = None
) -> "FormatBase":
    if isinstance(format, str):
        ret = FORMAT_TO_CHECK[format]()
        ret.apply_configuration_and_throw_if_invalid(configuration)
        return ret
    else:
        ret = []
        for i in format:
            ret.append(check_format_configuration_if_valid(i, configuration))

        if len(ret) == 1:
            return ret[0]
        else:
            return ret


def lines_if_valid(
    run_output: Path, format: "Union[str, Sequence[str]]", configuration: "Optional[dict[str, Any]]" = None
):
    """Load all lines from a user file if they are valid

    Args:
        format (Union[str, Sequence[str]]): The allowed format or a list of allowed formats.
        run_output (Path): the output produced by some run that is to-be checked.
        configuration (Optional[dict[str, Any]]): the configuration to apply to the formatter.
    """
    if not isinstance(format, str) and isinstance(format, Iterable):
        if len(format) == 0 or len(format) > 1:
            raise ValueError("Configuration error, I do not know in which format to read the file, I got {format}")
        else:
            format = format[0]

    if format not in SUPPORTED_FORMATS:
        raise ValueError(f"Format {format} is not supported. Supported formats are {SUPPORTED_FORMATS}.")

    checker = check_format_configuration_if_valid(format, configuration)
    result, msg = checker.check_format(run_output)
    if result != _fmt.OK:
        raise ValueError(msg)

    return checker.all_lines(run_output)


def report_valid_formats(run_output: Path) -> Dict[str, Any]:
    valid_formats: Dict[str, Any] = {}
    if _fmt.OK == check_format(run_output, "ir_metadata")[0]:
        valid_formats["ir_metadata"] = sorted([i["name"] for i in lines_if_valid(run_output, "ir_metadata")])

    for f in ["run.txt", "query-processor", "document-processor", "terrier-index"]:
        if _fmt.OK == check_format(run_output, f)[0]:
            valid_formats[f] = True

    return valid_formats


def check_format(
    run_output: Path, format: "Union[str, Sequence[str]]", configuration: "Optional[dict[str, Any]]" = None
):
    """Check if the provided run output is in the specified format. Provides debug messages intended for users.

    Args:
        format (Union[str, Sequence[str]]): The allowed format or a list of allowed formats.
        run_output (Path): the output produced by some run that is to-be checked.
        configuration (Optional[dict[str, Any]]): the configuration to apply to the formatter.
    """
    if not isinstance(format, str) and isinstance(format, Iterable):
        ret = {}
        for f in format:
            ret[f] = check_format(run_output, f, configuration)

        if all(i[0] == _fmt.OK for i in ret.values()):
            return [_fmt.OK, "The output is valid."]

        error_msg = [i[1] for i in ret.values() if i[0] != _fmt.OK]

        if "ir_metadata" in ret:
            metadata_valid = ret["ir_metadata"][0] == _fmt.OK
            one_payload_valid = any(v[0] == _fmt.OK for k, v in ret.items() if k != "ir_metadata")

            if metadata_valid and one_payload_valid:
                return [_fmt.OK, "The output is valid."]
            else:
                return [_fmt.ERROR, "The output is not valid. Problems: " + " ".join(error_msg)]

        ret = {k: v for k, v in ret.items() if v[0] == _fmt.OK}

        if len(ret) > 0:
            return [_fmt.OK, list(ret.values())[0][1]]
        else:
            return [_fmt.ERROR, "The output is not valid. Problems: " + " ".join(error_msg)]

    if format not in SUPPORTED_FORMATS:
        raise ValueError(f"Format {format} is not supported. Supported formats are {SUPPORTED_FORMATS}.")

    checker = check_format_configuration_if_valid(format, configuration)

    return checker.check_format(run_output)
