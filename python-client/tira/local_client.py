import json
import os
from glob import glob

import pandas as pd
from packaging import version

from tira.local_execution_integration import LocalExecutionIntegration
from tira.pandas_integration import PandasIntegration
from tira.pyterrier_integration import PyTerrierIntegration
from tira.rest_api_client import Client as RestClient
from tira.tira_client import TiraClient
from tira.trectools_integration import TrecToolsIntegration


class Client(TiraClient):
    def __init__(self, directory=".", rest_client=None):
        self.pd = PandasIntegration(self)
        self.pt = PyTerrierIntegration(self)
        self.trectools = TrecToolsIntegration(self)
        self.directory = directory + "/"
        self.tira_cache_dir = os.environ.get("TIRA_CACHE_DIR", os.path.expanduser("~") + "/.tira")
        self.rest_client = rest_client if rest_client else RestClient()
        self.local_execution = LocalExecutionIntegration(self.rest_client)

    def all_datasets(self) -> pd.DataFrame:
        ret = []
        for i in glob(self.directory + "*/training-datasets/"):
            cnt = 0
            for j in glob(i + "*"):
                cnt += len(list(open(j)))

            ret += [{"dataset": i.split("/training-datasets/")[0], "records": cnt}]

        for i in set([j.split("/")[1] for j in glob(self.directory + "**/**/**/job-executed-on-*.txt")]):
            ret += [{"dataset": i}]

        return pd.DataFrame(ret).sort_values("dataset")

    def ___load_softwares(self):
        softwares = [json.loads(i) for i in open(self.directory + ".tira/submitted-software.jsonl")]

        return {i["TIRA_TASK_ID"] + "/" + i["TIRA_VM_ID"] + "/" + i["TIRA_SOFTWARE_NAME"]: i for i in softwares}

    def all_softwares(self) -> pd.DataFrame:
        ret = []
        for software_id, software_definition in self.___load_softwares().items():
            ret += [
                {
                    "approach": software_id,
                    "id": str(int(software_definition["TIRA_SOFTWARE_ID"].split("docker-software-")[1])),
                    "team": software_definition["TIRA_VM_ID"],
                    "image": software_definition["TIRA_IMAGE_TO_EXECUTE_IN_DOCKERHUB"],
                    "command": software_definition["TIRA_COMMAND_TO_EXECUTE"],
                    "ids_of_previous_stages": [str(int(i)) for i in software_definition["TIRA_IDS_OF_PREVIOUS_STAGES"]],
                }
            ]

        return pd.DataFrame(ret)

    def print_overview_of_all_software(self) -> None:
        pre_text = """# Software for [$TASK_ID](https://www.tira.io/task/$TASK_ID)

<p id="instructions">Place <code>todo-replace</code> in a directory <code>$PWD/input</code>.
Then run the software as described below to produce results in <code>$PWD/output</code>.</p>
<p>For each software three ways to run it are shown below:</p>
<ul>
<li id="description-docker"><b>Docker</b>: on the command line (requires
<a href="https://docs.docker.com/engine/installation/">Docker</a>
)</li>
<li id="description-tira-cli"><b>TIRA (CLI)</b>: on the command line with <code>tira-run</code> (requires
<a href="https://docs.docker.com/engine/installation/">Docker</a>
and the
<a href="https://pypi.org/project/tira/">Python TIRA package</a>
)</li>
<li id="description-tira-python"><b>TIRA (Python)</b>: in a Python script (requires
<a href="https://docs.docker.com/engine/installation/">Docker</a>
and the
<a href="https://pypi.org/project/tira/">Python TIRA package</a>
)</li>
</ul>
"""

        toc = ["## List of software"]
        template_toc_team = "- [Team \u0060$TEAM\u0060](#team-$TEAM_LINK)"
        template_toc_software = "  - [Software \u0060$SOFTWARE\u0060](#software-$SOFTWARE_LINK)"

        content = []
        template_team_header = "\n## Team \u0060$TEAM\u0060\n[See generic instructions above](#instructions)"
        template_software = """### Software \u0060$SOFTWARE\u0060
- [Docker](#description-docker):
  \u0060\u0060\u0060bash
  $CMD_TIRA_DOCKER
  \u0060\u0060\u0060
- [TIRA (CLI)](#description-tira-cli):
  \u0060\u0060\u0060bash
  $CMD_TIRA_CLI
  \u0060\u0060\u0060
- [TIRA (Python)](#description-tira-python):
  \u0060\u0060\u0060python
  $CMD_TIRA_PYTHON
  \u0060\u0060\u0060
"""
        separator = "---"

        softwares = self.all_softwares().sort_values(by=["approach"])

        prev_team = ""
        for _, i in softwares.iterrows():
            execution_info = self.local_execution.run(
                identifier=i["approach"], input_dir="$PWD/input", output_dir="$PWD/output", dry_run=True
            )

            software_name = i["approach"].split("/")[-1]
            software_link = software_name.lower().replace(" ", "-")
            team_name = i["team"]
            team_link = team_name.lower().replace(" ", "-")

            if team_name != prev_team:
                toc.append(template_toc_team.replace("$TEAM_LINK", team_link).replace("$TEAM", team_name))

                if len(prev_team) == 0:
                    pre_text = pre_text.replace("$TASK_ID", "/".join(i["approach"].split("/")[:-2]))
                else:
                    content.append(separator)
                content.append(template_team_header.replace("$TEAM", team_name))
                prev_team = team_name

            toc.append(
                template_toc_software.replace("$SOFTWARE_LINK", software_link).replace("$SOFTWARE", software_name)
            )

            content.append(
                template_software.replace("$SOFTWARE", software_name)
                .replace("$CMD_TIRA_CLI", execution_info["tira-run-cli"])
                .replace("$CMD_TIRA_PYTHON", execution_info["tira-run-python"])
                .replace("$CMD_TIRA_DOCKER", execution_info["docker"])
            )

        print(pre_text)
        print("\n".join(toc))
        print("\n".join(content))

    def __load_evaluators(self):
        evaluators = [json.loads(i) for i in open(self.directory + ".tira/evaluators.jsonl")]
        ret = {i["TIRA_DATASET_ID"]: i for i in evaluators}

        for evaluator in evaluators:
            dataset_id = evaluator["TIRA_DATASET_ID"]
            current_version = version.parse(ret[dataset_id]["TIRA_EVALUATION_IMAGE_TO_EXECUTE"].split(":")[-1])
            available_version = version.parse(evaluator["TIRA_EVALUATION_IMAGE_TO_EXECUTE"].split(":")[-1])

            if available_version > current_version:
                ret[dataset_id] = evaluator

        return ret

    def __load_job_data(self, job_file):
        job = [i.split("=", 1) for i in open(job_file, "r")]
        return {k.strip(): v.strip() for k, v in job}

    def all_evaluators(self) -> pd.DataFrame:
        ret = []
        for i in self.__load_evaluators().values():
            ret += [
                {
                    "dataset": i["TIRA_DATASET_ID"],
                    "image": i["TIRA_EVALUATION_IMAGE_TO_EXECUTE"],
                    "command": i["TIRA_EVALUATION_COMMAND_TO_EXECUTE"],
                }
            ]

        return pd.DataFrame(ret)

    def __extract_image_and_command(self, identifier, evaluator=False):
        softwares = self.___load_softwares() if not evaluator else self.__load_evaluators()

        if identifier in softwares and not evaluator:
            return softwares[identifier]["TIRA_IMAGE_TO_EXECUTE"], softwares[identifier]["TIRA_COMMAND_TO_EXECUTE"]
        if evaluator:
            for k, v in softwares.items():
                if k.startswith(identifier):
                    return (
                        v["TIRA_DATASET_ID"],
                        v["TIRA_EVALUATION_IMAGE_TO_EXECUTE"],
                        v["TIRA_EVALUATION_COMMAND_TO_EXECUTE"],
                    )

        raise ValueError(
            f'There is no {("evaluator" if evaluator else "software")} identified by "{identifier}". Choices are:'
            f" {sorted(list(softwares))}"
        )

    def all_evaluated_appraoches(self) -> pd.DataFrame:
        id_to_software_name = {
            int(i["TIRA_SOFTWARE_ID"].split("docker-software-")[1]): i["TIRA_SOFTWARE_NAME"]
            for i in self.___load_softwares().values()
        }
        ret = []
        for evaluation in glob("*/*/*/evaluation"):
            job_dir = glob(evaluation + "/../job-executed-on*.txt")
            if len(job_dir) != 1:
                raise ValueError("Can not handle multiple job definitions: ", job_dir)

            job_definition = self.__load_job_data(job_dir[0])
            job_identifier = (
                job_definition["TIRA_TASK_ID"]
                + "/"
                + job_definition["TIRA_VM_ID"]
                + "/"
                + id_to_software_name[int(job_definition["TIRA_SOFTWARE_ID"].split("docker-software-")[1])]
            )

            for eval_run in glob(f"{evaluation}/*/output/"):
                try:
                    i = {"approach": job_identifier, "dataset": job_definition["TIRA_DATASET_ID"]}
                    i.update(self.__load_output(eval_run, evaluation=True))
                    ret += [i]
                except Exception:
                    pass

        return pd.DataFrame(ret)

    def docker_software(self, approach, software_id=None):
        ret = []

        if not os.path.exists(self.directory + ".tira/submitted-software.jsonl"):
            from tira.rest_api_client import Client as RestClient

            ret = RestClient().docker_software_details(approach)["context"]
            return {
                "tira_image_name": ret["image"],
                "command": ret["command"],
                "id": None,
                "ids_of_previous_stages": [],
            }

        for _, i in self.all_softwares().iterrows():
            if (approach and i["approach"] == approach) or (
                software_id is not None and str(int(software_id)) == i["id"]
            ):
                ret += [
                    {
                        "tira_image_name": i["image"],
                        "command": i["command"],
                        "id": i["id"],
                        "ids_of_previous_stages": i["ids_of_previous_stages"],
                    }
                ]

        if len(ret) == 1:
            return ret[0]

        raise ValueError(
            f'Could not find a unique software with approach="{approach}" or software_id="{software_id}". Found {ret}'
        )

    def run_was_already_executed_on_dataset(self, approach, dataset):
        return self.get_run_execution_or_none(approach, dataset) is not None

    def get_run_output(self, approach, dataset, allow_without_evaluation=False):
        return self.directory + "/" + self.get_run_execution_or_none(approach, dataset)["run_id"]

    def get_run_execution_or_none(self, approach, dataset, previous_stage_run_id=None):
        task, team, software = approach.split("/")
        executions = [json.loads(i) for i in open(self.directory + ".tira/executions.jsonl")]

        executions = [
            i
            for i in executions
            if i["TIRA_TASK_ID"] == task
            and i["TIRA_VM_ID"] == team
            and i["TIRA_SOFTWARE_NAME"] == software
            and i["dataset"] == dataset
        ]

        return (
            None
            if len(executions) < 1
            else {"task": task, "dataset": dataset, "team": team, "run_id": executions[0]["output_directory"]}
        )

    def download_run(self, task, dataset, software, team=None, previous_stage=None, return_metadata=False):
        ret = self.get_run_execution_or_none(f"{task}/{team}/{software}", dataset, previous_stage)
        if not ret:
            raise ValueError(
                f'I could not find a run for the filter criteria task="{task}", dataset="{dataset}",'
                f' software="{software}", team={team}, previous_stage={previous_stage}'
            )

        ret = self.directory + "/" + ret["run_id"]

        if not os.path.exists(ret + "/run.txt"):
            ret = pd.read_json(ret + "/rerank.jsonl.gz", lines=True, orient="columns")
            ret["qid"] = ret["qid"].astype(str)
            ret["docno"] = ret["docno"].astype(str)
            ret["docid"] = ret["docno"]
            ret["query"] = ret["qid"]
        else:
            ret = pd.read_csv(ret + "/run.txt", sep="\\s+", names=["query", "q0", "docid", "rank", "score", "system"])
            ret["query"] = ret["query"].astype(str)
            ret["docid"] = ret["docid"].astype(str)
            ret["docno"] = ret["docid"]
            ret["qid"] = ret["query"]

        if return_metadata:
            return ret, "run_id"
        else:
            return ret
