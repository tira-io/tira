import os
from pathlib import Path
from typing import Sequence, Union


class RunFormat:
    """Checks if a given output is a valid run file."""

    def check_format(self, run_output: Path):
        if not (run_output / "run.txt").exists():
            msg = "No file run.txt was found, only the files "
            msg += str(os.listdir(run_output)) + " were available."
            return ["ERROR", msg]
        else:
            return ["OK", "The run.txt file has the correct format."]


def check_format(run_output: Path, format: Union[str, Sequence[str]]):
    """Check if the provided run output is in the specified format. Provides debug messages intended for users.

    Args:
        format (Union[str, Sequence[str]]): The allowed format or a list of allowed formats.
        run_output (Path): the output produced by some run that is to-be checked.
    """
    if format == "run.txt":
        return RunFormat().check_format(run_output)

    raise ValueError("Not yet implemented.", run_output, format)
