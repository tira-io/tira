import gzip
import os
import re
from enum import Enum
from glob import glob
from pathlib import Path
from typing import Sequence, Union


class FormatMsgType(Enum):
    OK = 0
    WARN = 1
    ERROR = 2


_fmt = FormatMsgType


class FormatBase:
    def all_lines(self, f: Path):
        try:
            f_size = f.stat().st_size
            if f_size > self.max_size():
                raise ValueError(f"File {f} is too large (size {f_size} exceeds configured {self.max_size()}).")
        except:
            raise ValueError(f"File {f} is not readable.")

        if str(f).endswith(".gz"):
            with gzip.open(f, "rt") as o:
                return o.readlines()
        else:
            with open(f, "r") as o:
                return o.readlines()

    def max_size(self):
        return 10 * 1024 * 1024


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

    def check_format(self, run_output: Path):
        matches = [i for i in os.listdir(run_output) if i.endswith(".jsonl")]
        if len(matches) != 1:
            msg = "No unique *.jsonl file was found, only the files "
            msg += str(os.listdir(run_output)) + " were available."
            return [_fmt.ERROR, msg]
        else:
            return [_fmt.OK, "The jsonl file has the correct format."]


FORMAT_TO_CHECK = {"run.txt": lambda: RunFormat(), "*.jsonl": lambda: JsonlFormat()}

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
