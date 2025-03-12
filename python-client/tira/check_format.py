import gzip
import json
import os
import re
import xml.dom.minidom
from enum import Enum
from glob import glob
from pathlib import Path
from typing import Sequence, Union


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


class RunFormat(FormatBase):
    """Checks if a given output is a valid run file."""

    def check_format(self, run_output: Path):
        if (run_output / "run.txt").exists() and (run_output / "run.txt.gz").exists():
            msg = f"Found multiple run.txt or run.txt.gz files: {os.listdir(run_output)} ."
            return [_fmt.ERROR, msg]
        if not (run_output / "run.txt").exists() and not (run_output / "run.txt.gz").exists():
            msg = "No file run.txt or run.txt.gz was found, only the files "
            msg += str(os.listdir(run_output)) + " were available."
            return [_fmt.ERROR, msg]

        try:
            # maximum size of 10MB
            lines = self.all_lines(run_output)
        except Exception as e:
            return [_fmt.ERROR, repr(e)]

        if len(lines) < 10:
            return [_fmt.ERROR, f"The run file contains only {len(lines)} lines, this is likely an error."]

        query_to_docs = {}
        for l in lines:
            l = l.strip()
            cols = re.split("\\s+", l)
            if len(cols) != 6:
                return [
                    _fmt.ERROR,
                    f'Invalid line in the run file, expected 6 columns, but found a line "{l}" with {len(cols)} columns.',
                ]
            qid, _, docno, _, _, _ = cols
            if qid not in query_to_docs:
                query_to_docs[qid] = set()
            if docno in query_to_docs[qid]:
                return [
                    _fmt.ERROR,
                    f'The run file has duplicate documents: the document with id "{docno}" appears multiple times for query "{qid}".',
                ]
            query_to_docs[qid].add(docno)

        if len(query_to_docs.keys()) < 3:
            return [_fmt.ERROR, f"The run file has only {len(query_to_docs)} queries which is likely an error."]

        return [_fmt.OK, "The run.txt file has the correct format."]

    def all_lines(self, run_output):
        if (run_output / "run.txt").exists():
            return [i.strip() for i in super().all_lines(run_output / "run.txt")]
        if (run_output / "run.txt.gz").exists():
            return [i.strip() for i in super().all_lines(run_output / "run.txt.gz")]
        else:
            raise ValueError("Could not find a file run.txt or run.txt.gz")


class JsonlFormat(FormatBase):
    """Checks if a given output is a valid jsonl file."""

    def __init__(self, required_fields=("id",), minimum_lines=3):
        self.required_fields = required_fields
        self.minimum_lines = minimum_lines

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


class GenIrSimulationFormat(JsonlFormat):
    def __init__(self):
        super().__init__(required_fields=(), minimum_lines=1)

    def fail_if_json_line_is_not_valid(self, line):
        if "simulation" not in line:
            raise ValueError('The json line misses the required field "simulation".')
        line = line["simulation"]

        if "configuration" not in line:
            raise ValueError('The json line misses the required field "simulation.configuration".')

        if "userTurns" not in line:
            raise ValueError('The json line misses the required field "simulation.userTurns".')


class TsvFormat(FormatBase):
    """Checks if a given output is a valid tsv file."""

    def check_format(self, run_output: Path):
        try:
            lines = self.all_lines(run_output)
        except Exception as e:
            return [_fmt.ERROR, str(e)]

        if len(lines) < 5:
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


FORMAT_TO_CHECK = {
    "run.txt": lambda: RunFormat(),
    "*.jsonl": lambda: JsonlFormat(),
    "*.tsv": lambda: TsvFormat(),
    "text-alignment-corpus": lambda: TextAlignmentCorpusFormat(),
    "text-alignment-features": lambda: TextAlignmentFeaturesFormat(),
    "style-change-detection-corpus": lambda: PanStyleChangeDetectionCorpusFormat(),
    "style-change-detection-predictions": lambda: PanStyleChangeDetectionPredictionFormat(),
    "GenIR-Simulation": lambda: GenIrSimulationFormat(),
}

SUPPORTED_FORMATS = set(sorted(list(FORMAT_TO_CHECK.keys())))


def lines_if_valid(run_output: Path, format: Union[str, Sequence[str]]):
    """Load all lines from a user file if they are valid

    Args:
        format (Union[str, Sequence[str]]): The allowed format or a list of allowed formats.
        run_output (Path): the output produced by some run that is to-be checked.
    """
    if format not in SUPPORTED_FORMATS:
        raise ValueError(f"Format {format} is not supported. Supported formats are {SUPPORTED_FORMATS}.")

    checker = FORMAT_TO_CHECK[format]()
    result, msg = checker.check_format(run_output)
    if result != _fmt.OK:
        raise ValueError(msg)

    return checker.all_lines(run_output)


def check_format(run_output: Path, format: Union[str, Sequence[str]]):
    """Check if the provided run output is in the specified format. Provides debug messages intended for users.

    Args:
        format (Union[str, Sequence[str]]): The allowed format or a list of allowed formats.
        run_output (Path): the output produced by some run that is to-be checked.
    """
    if format not in SUPPORTED_FORMATS:
        raise ValueError(f"Format {format} is not supported. Supported formats are {SUPPORTED_FORMATS}.")

    checker = FORMAT_TO_CHECK[format]()
    return checker.check_format(run_output)
