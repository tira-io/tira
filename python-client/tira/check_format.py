import gzip
import json
import os
import re
import xml.dom.minidom
from collections.abc import Iterable
from enum import Enum
from glob import glob
from pathlib import Path
from typing import Any, Optional, Sequence, Union


class FormatMsgType(Enum):
    OK = 0
    WARN = 1
    ERROR = 2


_fmt = FormatMsgType


def log_message(message: str, level: _fmt):
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
    print(f"{symbol} {message}")


CONF_REQUIRED_FIELDS = "required_fields"
CONF_MINIMUM_LINES = "minimum_lines"
CONF_ID_FIELD = "id_field"
CONF_VALUE_FIELD = "value_field"

CONFIGURATION_FIELDS = {
    CONF_REQUIRED_FIELDS: "foo",
    CONF_MINIMUM_LINES: "foo",
    CONF_ID_FIELD: "foo",
    CONF_VALUE_FIELD: "foo",
}


class FormatBase:
    def all_lines(self, f: Path):
        try:
            f_size = f.stat().st_size
        except:
            raise ValueError(f"File {f} is not readable.")

        if f_size > self.max_size():
            raise ValueError(f"File {f} is too large (size {f_size} exceeds configured {self.max_size()}).")

        if str(f).endswith(".gz"):
            with gzip.open(f, "rt") as o:
                return o.readlines()
        else:
            with open(f, "r") as o:
                return o.readlines()

    def max_size(self):
        return 25 * 1024 * 1024

    def apply_configuration_and_throw_if_invalid(self, configuration: "Optional[dict[str, Any]]" = None):
        pass

    def check_format(self, run_output: Path):
        return [_fmt.ERROR, "not implemented"]


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
                    f'The run file has duplicate documents: the document with id "{line["docno"]}" appears multiple times for query "{line["qid"]}".',
                ]
            query_to_docs[line["qid"]].add(line["docno"])

        if len(query_to_docs.keys()) < 3:
            return [_fmt.ERROR, f"The run file has only {len(query_to_docs)} queries which is likely an error."]

        return [_fmt.OK, "The run.txt file has the correct format."]

    def all_lines(self, run_output):
        if (run_output / "run.txt").exists():
            ret = [i.strip() for i in super().all_lines(run_output / "run.txt")]
        elif (run_output / "run.txt.gz").exists():
            ret = [i.strip() for i in super().all_lines(run_output / "run.txt.gz")]
        else:
            raise ValueError("Could not find a file run.txt or run.txt.gz")

        ret_parsed = []
        for i in ret:
            cols = re.split("\\s+", i)
            if len(cols) != 6:
                raise ValueError(
                    f'Invalid line in the run file, expected 6 columns, but found a line "{i}" with {len(cols)} columns.'
                )
            qid, q0, docno, rank, score, system = cols
            try:
                rank = int(rank)
            except ValueError:
                raise ValueError(f"Could not parse the rank. Got {rank}. Line: {i}")

            try:
                score = float(score)
            except ValueError:
                raise ValueError(f"Could not parse the rank. Got {rank}. Line: {i}")

            ret_parsed.append({"qid": qid, "q0": q0, "docno": docno, "rank": rank, "score": score, "system": system})

        return ret_parsed


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

        if configuration:
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

    def has_id_and_value_field(self):
        return self.id_field is not None and self.value_field is not None


class JsonlFormat(KeyValueFormatBase):
    """Checks if a given output is a valid jsonl file."""

    def apply_configuration_and_throw_if_invalid(self, configuration: "Optional[dict[str, Any]]"):
        if not configuration:
            configuration = {}

        if CONF_REQUIRED_FIELDS not in configuration:
            configuration[CONF_REQUIRED_FIELDS] = ("id",)

        if CONF_MINIMUM_LINES not in configuration:
            configuration[CONF_MINIMUM_LINES] = 3

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

    def all_lines(self, run_output):
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

        ret_raw = [i.strip() for i in super().all_lines(matches[0])]
        ret = []
        for i in ret_raw:
            try:
                ret.append(json.loads(i))
            except:
                raise ValueError(f'The file {matches[0]} contains a line that could not be parsed: "{i}".')

        for i in ret:
            self.fail_if_json_line_is_not_valid(i)

        return ret


class LongEvalLags(FormatBase):
    def apply_configuration_and_throw_if_invalid(self, configuration: "Optional[dict[str, Any]]"):
        if not configuration or "lags" not in configuration or not configuration["lags"]:
            raise ValueError(
                'Please pass a configuration "lags" that points out on which lags an dataset should run. E.g., {"lags": ["lag-1", "lag-2"]}.'
            )

        self.lags = configuration["lags"]
        format = "run.txt"
        if "format" in configuration:
            format = configuration["format"]
        self.format = format

    def check_format(self, run_output: Path):
        for lag in self.lags:
            status, msg = check_format(run_output / lag, self.format)
            if status != _fmt.OK:
                return [_fmt.ERROR, f"The Lag {lag} is invalid: {msg}"]

        return [_fmt.OK, f"All lags {self.lags} are valid."]


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

        if configuration:
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

    def all_lines(self, run_output):
        matches = [i for i in os.listdir(run_output) if i.endswith(".tsv")]
        if len(matches) != 1:
            msg = "No unique *.tsv file was found, only the files "
            msg += str(os.listdir(run_output)) + " were available."
            raise ValueError(msg)

        f = run_output / matches[0]
        with open(f, "r") as tsv_file:
            columns = None
            ret = []
            for l in tsv_file:
                l_parsed = l.strip().split("\t")
                if columns is None:
                    columns = len(l_parsed)
                if len(l_parsed) != columns:
                    raise ValueError("The *.tsv file is invalid: The number of columns varies.")
                ret += [l_parsed]
            return ret


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


class IrMetadataFormat(FormatBase):
    """Checks if a given output contains valid ir_metadata."""

    def __init__(self, positive_fields=("platform", "implementation", "resources")):
        self.positive_fields = positive_fields

    def check_format(self, run_output: Path):
        try:
            lines = list(self.yield_lines(run_output))

            if len(lines) < 1:
                return [_fmt.ERROR, "At least one valid ir_metadata file was expected, but there was none."]

            return [_fmt.OK, "The output provides valid ir_metadata."]
        except Exception as e:
            return [_fmt.ERROR, str(e)]

    def all_lines(self, run_output):
        return [i for i in self.yield_lines(run_output)]

    def yield_lines(self, run_output: Path):
        import yaml

        candidates = [str(run_output)]
        for pattern in ["/*.yml", "/*.yaml", "/.*.yml", "/.*.yaml"]:
            for depth in ["", "/**", "/**/**"]:
                candidates += glob(str(run_output) + depth + pattern)

        for candidate in candidates:
            if not Path(candidate).exists() or not Path(candidate).is_file():
                continue

            with open(candidate) as stream:
                try:
                    content = yaml.safe_load(stream)
                    at_least_one_positive_field = any(i in content for i in self.positive_fields)

                    if not at_least_one_positive_field:
                        continue

                    yield {"name": candidate.split("/")[-1], "content": content}
                except yaml.YAMLError:
                    pass


FORMAT_TO_CHECK = {
    "run.txt": lambda: RunFormat(),
    "*.jsonl": lambda: JsonlFormat(),
    "*.tsv": lambda: TsvFormat(),
    "text-alignment-corpus": lambda: TextAlignmentCorpusFormat(),
    "text-alignment-features": lambda: TextAlignmentFeaturesFormat(),
    "style-change-detection-corpus": lambda: PanStyleChangeDetectionCorpusFormat(),
    "style-change-detection-predictions": lambda: PanStyleChangeDetectionPredictionFormat(),
    "GenIR-Simulation": lambda: GenIrSimulationFormat(),
    "ir_metadata": lambda: IrMetadataFormat(),
    "qrels.txt": QrelFormat,
    "LongEvalLags": LongEvalLags,
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


def report_valid_formats(run_output: Path):
    valid_formats = {}
    if _fmt.OK == check_format(run_output, "ir_metadata")[0]:
        valid_formats["ir_metadata"] = sorted([i["name"] for i in lines_if_valid(run_output, "ir_metadata")])
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
        else:
            error_msg = [i[1] for i in ret.values() if i[0] != _fmt.OK]

            return [_fmt.ERROR, "The output is not valid. Problems: " + " ".join(error_msg)]

    if format not in SUPPORTED_FORMATS:
        raise ValueError(f"Format {format} is not supported. Supported formats are {SUPPORTED_FORMATS}.")

    checker = check_format_configuration_if_valid(format, configuration)
    return checker.check_format(run_output)
