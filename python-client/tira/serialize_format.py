import gzip
import tempfile
from pathlib import Path
from shutil import copyfile

DF_EXPECTED_COLUMNS = ["qid", "q0", "docid", "rank", "score", "system"]


class RunSerializer:
    """Serializes a run object into a directory."""

    def is_dataframe(self, data: any):
        try:
            import pandas as pd

            return isinstance(data, pd.DataFrame)
        except:
            return False

    def serialize(self, data, output_path: Path):
        output_path.mkdir(exist_ok=True, parents=True)

        if isinstance(data, str):
            return self.serialize(Path(data), output_path)
        if isinstance(data, Path):
            if not data.is_file():
                raise ValueError(f"The passed run file {data} is not a file.")
            copyfile(data, output_path / ("run.txt.gz" if (str(data).endswith(".gz")) else "run.txt"))
            return
        if self.is_dataframe(data):
            data = data.copy()
            orig_columns = [i for i in data.columns]
            if "q0" not in data.columns:
                data["q0"] = "Q0"

            if "qid" not in data.columns and "query" in data.columns:
                data["qid"] = data["query"]

            if "docno" in data.columns:
                data["docid"] = data["docno"]

            missing_columns = []
            for f in DF_EXPECTED_COLUMNS:
                if f not in data.columns:
                    missing_columns += [f]

            if len(missing_columns) > 0:
                raise ValueError(
                    f"The passed run is missing the required columns {missing_columns}. It has the columns {orig_columns}."
                )

            lines = []
            for _, i in data.iterrows():
                l = ""
                for f in DF_EXPECTED_COLUMNS:
                    if len(str(i[f]).strip().split()) > 1:
                        raise ValueError(
                            f'Fields in a run file are expected to not contain whitespaces. The value "{str(i[f]).strip()}" for the field "{f}" contains whitespaces.'
                        )
                    l += " " + str(i[f])
                lines += [l.strip()]

            with gzip.open(output_path / "run.txt.gz", "wt") as f:
                f.write("\n".join(lines))
            return
        if hasattr(data, "run_data") and self.is_dataframe(data.run_data):
            return self.serialize(data.run_data, output_path)

        raise ValueError("foo")


FORMAT_TO_SERIALIZER = {"run.txt": lambda: RunSerializer()}

SUPPORTED_FORMATS = set(sorted(list(FORMAT_TO_SERIALIZER.keys())))


def serialize_in_temporary_directory(data: any, format: str):
    """Check if the provided run output is in the specified format. Provides debug messages intended for users.

    Args:
        format (Union[str, Sequence[str]]): The allowed format or a list of allowed formats.
        run_output (Path): the output produced by some run that is to-be checked.
    """
    if format not in SUPPORTED_FORMATS:
        raise ValueError(f"Format {format} is not supported. Supported formats are {SUPPORTED_FORMATS}.")
    ret = tempfile.TemporaryDirectory()
    ret = Path(ret.name)
    serializer = FORMAT_TO_SERIALIZER[format]()
    serializer.serialize(data, ret)
    return ret
