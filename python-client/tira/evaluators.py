from pathlib import Path
from typing import List, Optional, Union

from tira.check_format import _fmt, check_format, lines_if_valid, log_message
from tira.io_utils import to_prototext
from tira.rest_api_client import Client
from tira.tira_client import TiraClient


class TiraBaseEvaluator:
    def __init__(self, run_format: Union[str | List[str]], truth_format: Union[str | List[str]], measures: List[str]):
        self.run_format = run_format
        self.truth_format = truth_format
        self.measures = measures

    def evaluate(self, run: Path, truths: Path):
        self.is_valid(run, self.run_format, True)
        self.is_valid(truths, self.truth_format)

        run_data = lines_if_valid(run, self.run_format)
        truth_data = lines_if_valid(truths, self.truth_format)

        return self._eval(run_data, truth_data)

    def is_valid(self, directory: Path, format: Union[str | List[str]], log=False):
        ret = check_format(directory, format)
        if log:
            log_message(ret[1], ret[0])
        if ret[0] != _fmt.OK:
            raise ValueError(ret[1])

    def configuration_is_valid(run_format, truth_format, config):
        raise ValueError("This is not implemented")

    def _eval(run_data, truth_data):
        raise ValueError("This is not implemented")


class TrecToolsEvaluator(TiraBaseEvaluator):
    def configuration_is_valid(self, run_format, truth_format, config):
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


EVALUATORS = {"TrecTools": TrecToolsEvaluator}

MEASURE_TO_EVALUATORS = {"nDCG@10": "TrecTools", "RR": "TrecTools", "P@10": "TrecTools"}


def load_evaluator_config(config: Union[dict, str], client: Optional[TiraClient] = None):
    if isinstance(config, str):
        if client is None:
            client = Client()
        dataset_config = client.get_dataset(config)
        if "trusted_evaluator" not in dataset_config or not dataset_config["trusted_evaluator"]:
            raise ValueError(f'No trusted evaluation is configured for the dataset "{config}".')

        return load_evaluator_config(dataset_config["trusted_evaluator"])

    if "evaluator" not in config:
        raise ValueError("Configuration of the evaluator is invalid: No evaluator name is specified.")

    if "measures" not in config or not config["measures"]:
        raise ValueError("Configuration of the evaluator is invalid: No measures are specified.")

    if "run_format" not in config:
        raise ValueError("Configuration of the evaluator is invalid: No run_format is specified.")

    if "truth_format" not in config:
        raise ValueError("Configuration of the evaluator is invalid: No truth_format is specified.")

    return config


def get_evaluators_if_valid(config: Union[dict, str], client: Optional[TiraClient] = None):
    config = load_evaluator_config(config, client)

    evaluator_to_measures = {}
    for measure in config["measures"]:
        evaluator = MEASURE_TO_EVALUATORS[measure]
        if evaluator not in evaluator_to_measures:
            evaluator_to_measures[evaluator] = []
        evaluator_to_measures[evaluator] += [measure]

    ret = []
    for evaluator, measures in evaluator_to_measures.items():
        ret.append(EVALUATORS[evaluator](config["run_format"], config["truth_format"], measures))

    return ret


def evaluate(
    run: Path,
    truths: Path,
    config: Union[dict, str],
    output_dir: Optional[Path] = None,
    client: Optional[TiraClient] = None,
):
    config = load_evaluator_config(config, client)
    evaluators = get_evaluators_if_valid(config, client)
    ret = {}
    for evaluator in evaluators:
        evaluation = evaluator.evaluate(run, truths)
        ret.update(evaluation)

    if output_dir:
        prototext = to_prototext([ret])
        with open(output_dir / "evaluation.prototext") as f:
            f.write(prototext)

    return ret
