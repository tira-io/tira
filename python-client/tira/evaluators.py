import os
from abc import ABC
from pathlib import Path
from typing import List, Optional, Union

from tira.check_format import _fmt, check_format, lines_if_valid, log_message
from tira.io_utils import to_prototext
from tira.rest_api_client import Client
from tira.tira_client import TiraClient


class TiraBaseEvaluator(ABC):
    def __init__(self, run_format: Union[str, List[str]], truth_format: Union[str, List[str]], measures: List[str]):
        self.run_format = run_format
        self.truth_format = truth_format
        self.measures = measures

    def evaluate(self, run: Path, truths: Path) -> dict:
        self.is_valid(run, self.run_format, True)
        self.is_valid(truths, self.truth_format)

        run_data = lines_if_valid(run, self.run_format)
        truth_data = lines_if_valid(truths, self.truth_format)

        return self._eval(run_data, truth_data)

    def is_valid(self, directory: Path, format: Union[str, List[str]], log: bool = False):
        ret = check_format(directory, format)
        if log:
            log_message(ret[1], ret[0])
        if ret[0] != _fmt.OK:
            raise ValueError(ret[1])

    def throw_if_conf_invalid(
        self, run_format: Union[str, List[str]], truth_format: Union[str, List[str]], config: dict
    ) -> None:
        raise ValueError("This is not implemented")

    def _eval(run_data, truth_data):
        raise ValueError("This is not implemented")


class RunFileEvaluator(TiraBaseEvaluator):
    def throw_if_conf_invalid(
        self, run_format: Union[str, List[str]], truth_format: Union[str, List[str]], config: dict
    ) -> None:
        if "run.txt" != run_format and "run.txt" not in run_format:
            raise ValueError("I can only use the RunFileEvaluator for run.txt format")

        self.run_format = "run.txt"
        if truth_format and "qrels.txt" != truth_format and "qrels.txt" not in truth_format:
            self.truth_format = "qrels.txt"

    def evaluate(self, run: Path, truths: Path) -> dict:
        self.is_valid(run, self.run_format, True)

        expected_queries = None
        if self.truth_format is not None:

            self.is_valid(truths, self.truth_format)
            expected_queries = lines_if_valid(truths, self.truth_format)
            expected_queries = set([i["qid"] for i in expected_queries])

        run_data = lines_if_valid(run, self.run_format)
        counts = {}

        for i in run_data:
            if expected_queries and i["qid"] not in expected_queries:
                continue
            if i["qid"] not in counts:
                counts[i["qid"]] = set()
            counts[i["qid"]].add(i["docno"])

        lengths = [len(i) for i in counts.values()]
        num_queries = len(counts.keys())

        ret = {
            "Docs Per Query (Avg)": sum(lengths) / num_queries,
            "Docs Per Query (Min)": min(lengths),
            "Docs Per Query (Max)": max(lengths),
            "NumQueries": num_queries,
        }

        return {k: ret[k] for k in self.measures}


class HuggingFaceEvaluator(TiraBaseEvaluator):
    def throw_if_conf_invalid(
        self, run_format: Union[str, List[str]], truth_format: Union[str, List[str]], config: dict
    ) -> None:
        if not run_format or not truth_format:
            raise ValueError(
                f"Configuration error. I need a run and truth format. Got: run_format={run_format} and truth_format={truth_format}."
            )

        if "run_label_column" not in config or "run_id_column" not in config:
            raise ValueError(f"Configuration error. I need to extract the label and id column from runs.")

        self.run_label_column = config["run_label_column"]
        self.run_id_column = config["run_id_column"]
        if "truth_label_column" not in config or "truth_id_column" not in config:
            raise ValueError(f"Configuration error. I need to extract the label and id column from truths.")

        self.truth_label_column = config["truth_label_column"]
        self.truth_id_column = config["truth_id_column"]
        if "additional_args" in config and config["additional_args"]:
            self.additional_args = config["additional_args"]
        else:
            self.additional_args = {}

        import evaluate
        from evaluate.utils.file_utils import DownloadConfig

        if os.environ.get("OFFLINE", False):
            evaluate.config.HF_EVALUATE_OFFLINE = True

    def _eval(self, run_data, truth_data):
        run_data = [{"id": i[self.run_id_column], "prediction": i[self.run_label_column]} for i in run_data]
        truth_data = [{"id": i[self.truth_id_column], "truth": i[self.truth_label_column]} for i in truth_data]

        import evaluate
        import pandas as pd
        from evaluate.utils.file_utils import DownloadConfig

        download_config = None
        if os.environ.get("OFFLINE", False):
            download_config = DownloadConfig(local_files_only=True)

        df = pd.merge(pd.DataFrame(run_data), pd.DataFrame(truth_data), left_index=True, right_index=True)
        run_data = df.iloc[:, 0].tolist()
        truth_data = df.iloc[:, 1].tolist()
        ret = {}
        for m in self.measures:
            ret[m] = evaluate.load(m, download_config=download_config).compute(
                predictions=run_data, references=truth_data, **self.additional_args
            )[m]
        return ret


class TrecToolsEvaluator(TiraBaseEvaluator):
    def throw_if_conf_invalid(
        self, run_format: Union[str, List[str]], truth_format: Union[str, List[str]], config: dict
    ) -> None:
        if "run.txt" != run_format and "run.txt" not in run_format:
            raise ValueError("I can only use trectools for run.txt format")

        if "qrels.txt" != run_format and "qrels.txt" not in truth_format:
            raise ValueError("I can only use trectools for run.txt format")

        self.run_format = "run.txt"
        self.truth_format = "qrels.txt"

        # check that dependencies are available
        import pandas as pd
        from trectools import TrecEval, TrecQrel, TrecRun

    def _eval(self, run_data, truth_data):
        import pandas as pd
        from trectools import TrecEval, TrecQrel, TrecRun

        run = TrecRun()
        run.run_data = pd.DataFrame(run_data)
        run.run_data["query"] = run.run_data["qid"]
        run.run_data["docid"] = run.run_data["docno"]

        qrels = TrecQrel()
        qrels.qrels_data = pd.DataFrame(truth_data)
        qrels.qrels_data["query"] = qrels.qrels_data["qid"]
        qrels.qrels_data["docid"] = qrels.qrels_data["docno"]

        te = TrecEval(run, qrels)

        ret = {}
        if "nDCG@10" in self.measures:
            ret["nDCG@10"] = te.get_ndcg(depth=10)

        if "P@10" in self.measures:
            ret["P@10"] = te.get_precision(depth=10)

        if "RR" in self.measures:
            ret["RR"] = te.get_reciprocal_rank()

        return {k: ret[k] for k in self.measures}


EVALUATORS: dict[str, TiraBaseEvaluator] = {
    "TrecTools": TrecToolsEvaluator,
    "RunFileEvaluator": RunFileEvaluator,
    "HuggingFaceEvaluator": HuggingFaceEvaluator,
}

MEASURE_TO_EVALUATORS: dict[str, str] = {
    "nDCG@10": "TrecTools",
    "RR": "TrecTools",
    "P@10": "TrecTools",
    "Docs Per Query (Avg)": "RunFileEvaluator",
    "Docs Per Query (Min)": "RunFileEvaluator",
    "Docs Per Query (Max)": "RunFileEvaluator",
    "NumQueries": "RunFileEvaluator",
    "accuracy": "HuggingFaceEvaluator",
    "recall": "HuggingFaceEvaluator",
    "precision": "HuggingFaceEvaluator",
    "f1": "HuggingFaceEvaluator",
}


def load_evaluator_config(config: Union[dict, str], client: Optional[TiraClient] = None) -> dict:
    if isinstance(config, str):
        if client is None:
            client = Client()
        dataset_config = client.get_dataset(config)
        if "trusted_evaluator" not in dataset_config or not dataset_config["trusted_evaluator"]:
            raise ValueError(f'No trusted evaluation is configured for the dataset "{config}".')

        return load_evaluator_config(dataset_config["trusted_evaluator"])

    if "measures" not in config or not config["measures"]:
        raise ValueError("Configuration of the evaluator is invalid: No measures are specified.")

    if "run_format" not in config:
        raise ValueError("Configuration of the evaluator is invalid: No run_format is specified.")

    if "truth_format" not in config:
        raise ValueError("Configuration of the evaluator is invalid: No truth_format is specified.")

    return config


def get_evaluators_if_valid(config: Union[dict, str], client: Optional[TiraClient] = None) -> List[TiraBaseEvaluator]:
    config = load_evaluator_config(config, client)

    evaluator_to_measures = {}
    for measure in config["measures"]:
        evaluator = MEASURE_TO_EVALUATORS[measure]
        if evaluator not in evaluator_to_measures:
            evaluator_to_measures[evaluator] = []
        evaluator_to_measures[evaluator] += [measure]

    ret = []
    for evaluator, measures in evaluator_to_measures.items():
        impl = EVALUATORS[evaluator](config["run_format"], config["truth_format"], measures)
        impl.throw_if_conf_invalid(config["run_format"], config["truth_format"], config)
        ret.append(impl)

    return ret


def evaluate(
    run: Path,
    truths: Path,
    config: Union[dict, str],
    output_dir: Optional[Path] = None,
    client: Optional[TiraClient] = None,
) -> dict:
    config = load_evaluator_config(config, client)
    evaluators = get_evaluators_if_valid(config, client)
    ret = {}
    for evaluator in evaluators:
        evaluation = evaluator.evaluate(run, truths)
        ret.update(evaluation)

    if output_dir:
        prototext = to_prototext([ret])
        (output_dir / "evaluation.prototext").write_text(prototext)

    return ret
