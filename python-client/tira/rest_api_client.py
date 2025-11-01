import hashlib
import io
import json
import logging
import os
import shutil
import tempfile
import time
import zipfile
from functools import lru_cache
from glob import glob
from pathlib import Path
from random import randint
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import requests
from tqdm import tqdm

from tira.check_format import _fmt, check_format, fmt_message
from tira.local_execution_integration import LocalExecutionIntegration
from tira.pandas_integration import PandasIntegration
from tira.profiling_integration import ProfilingIntegration
from tira.pyterrier_integration import PyTerrierAnceIntegration, PyTerrierIntegration, PyTerrierSpladeIntegration
from tira.third_party_integrations import temporary_directory
from tira.tira_redirects import (
    RESOURCE_REDIRECTS,
    TASKS_WITH_REDIRECT_MERGING,
    dataset_ir_redirects,
    mirror_url,
    redirects,
)
from tira.trectools_integration import TrecToolsIntegration

from .tira_client import TiraClient


class Client(TiraClient):
    base_url: str

    def __init__(
        self,
        base_url: "Optional[str]" = None,
        api_key: str = None,
        failsave_retries: int = 5,
        failsave_max_delay: int = 15,
        api_user_name: "Optional[str]" = None,
        tira_cache_dir: "Optional[str]" = None,
        verify: bool = None,
        allow_local_execution: bool = False,
        archive_base_url: "Optional[str]" = None,
        base_url_api: str = None,
    ):
        self._settings = None
        self.logged: "set[str]" = set()
        self.tira_cache_dir = (
            tira_cache_dir if tira_cache_dir else os.environ.get("TIRA_CACHE_DIR", os.path.expanduser("~") + "/.tira")
        )
        self.base_url = base_url or self.load_settings()["base_url"]
        self.base_url_api = base_url_api or self.load_settings()["base_url_api"]
        self.archive_base_url = archive_base_url or self.load_settings()["archive_base_url"]

        self.verify = verify if verify is not None else self.load_settings()["verify"]
        self.failsave_max_delay = failsave_max_delay

        self.json_cache = {}

        if api_key is None:
            self.api_key = self.load_settings()["api_key"]
            self.api_user_name = self.load_settings()["api_user_name"]
        else:
            self.api_key = api_key
            self.api_user_name = api_user_name

        self.failsave_retries = 1
        if self.api_key != "no-api-key":
            self.fail_if_api_key_is_invalid()
        self.failsave_retries = failsave_retries
        self.pd: PandasIntegration = PandasIntegration(self)
        self.pt: PyTerrierIntegration = PyTerrierIntegration(self)
        self.trectools: TrecToolsIntegration = TrecToolsIntegration(self)
        self.profiling: ProfilingIntegration = ProfilingIntegration(self)
        self.pt_ance: PyTerrierAnceIntegration = PyTerrierAnceIntegration(self)
        self.pt_splade: PyTerrierSpladeIntegration = PyTerrierSpladeIntegration(self)
        self.local_execution: LocalExecutionIntegration = LocalExecutionIntegration(self)
        self.allow_local_execution = allow_local_execution

    def load_settings(self):
        if self._settings is None:
            try:
                ret = json.load(open(self.tira_cache_dir + "/.tira-settings.json", "r"))
                if "api_key" not in ret:
                    ret["api_key"] = "no-api-key"
                if "api_user_name" not in ret:
                    ret["api_user_name"] = "no-api-key-user"
                self._settings = ret
            except Exception:
                if "load_settings" not in self.logged:
                    logging.info(
                        f"No settings given in {self.tira_cache_dir}/.tira-settings.json. I will use defaults."
                    )
                    self.logged.add("load_settings")
                self._settings = {"api_key": "no-api-key", "api_user_name": "no-api-key-user"}

            if "base_url" not in self._settings:
                self._settings["base_url"] = "https://www.tira.io"
            if "base_url_api" not in self._settings:
                self._settings["base_url_api"] = "https://api.tira.io"
            if "archive_base_url" not in self._settings:
                self._settings["archive_base_url"] = "https://tira.io"

            if "verify" not in self._settings:
                self._settings["verify"] = True

            self._settings["verify"] = bool(self._settings["verify"])

        return self._settings

    def update_settings(self, k: str, v: Any) -> None:
        settings = self.load_settings()
        settings[k] = v
        os.makedirs(self.tira_cache_dir, exist_ok=True)
        json.dump(settings, open(Path(self.tira_cache_dir) / ".tira-settings.json", "w+"))

        if k == "api_key":
            self.api_key = settings["api_key"]

    def datasets(self, task: str, force_reload: bool = False) -> Dict:
        url = f"/api/datasets_by_task/{task}"

        try:
            resp = self.archived_json_response(url, force_reload=force_reload)
        except:
            resp = self.archived_json_response(url, force_reload=True)

        return json.loads(resp["context"]["datasets"])

    def dataset_only_available_locally(self, dataset):
        if not Path(dataset).exists():
            return False
        dataset_identifier = self._TiraClient__extract_dataset_identifier(dataset)
        url = "/v1/datasets/all"

        try:
            datasets = self.archived_json_response(url)
        except:
            datasets = self.archived_json_response(url, force_reload=True)

        return self._TiraClient__matching_dataset(datasets, dataset_identifier) is None

    def dataset_exists_in_tira(self, dataset):
        if "TIRA_INPUT_DATASET" in os.environ:
            return True
        ds_identifier = self._TiraClient__extract_dataset_identifier(dataset)
        try:
            datasets = self.archived_json_response("/v1/datasets/all")
        except:
            datasets = self.archived_json_response("/v1/datasets/all", force_reload=True)

        ret = self._TiraClient__matching_dataset(datasets, ds_identifier)
        return ret is not None

    def claim_ownership(self, uuid: str, team: str, system: str, description: str, task_id: str) -> Dict:
        headers = self.authentication_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        self.fail_if_api_key_is_invalid()

        upload_group = None

        try:
            upload_group = self.get_upload_group_id(task_id, team, system, failsave=True)
        except:
            pass

        url = f"{self.base_url}/v1/anonymous/claim/{team}/{uuid}"
        if upload_group:
            content = {"upload_group": upload_group}
        else:
            content = {
                "display_name": system,
                "description": description,
                "paper_link": "",
            }

        response = requests.post(url, headers=headers, json=content, verify=self.verify)
        ret = response.content.decode("utf8")
        return json.loads(ret)

    def get_dataset(self, dataset) -> dict:
        """Get the TIRA representation of an dataset identified by the passed dataset argument.

        Args:
            dataset (Union[str, IrDataset, PyTerrierDataset): The dataset that is either the string id of the dataset in TIRA, the string id of an ir_dataset, the string id of an PyTerrier dataset, or an instantiation of an ir_dataset or an PyTerrier dataset.
        Returns:
            dict: The TIRA representation of the dataset.
        """

        dataset_identifier = self._TiraClient__extract_dataset_identifier(dataset)
        if self.dataset_exists_in_tira(dataset):
            datasets = self.archived_json_response("/v1/datasets/all")
            return self._TiraClient__matching_dataset(datasets, dataset_identifier)

        # retry with force_reload.
        datasets = self.archived_json_response("/v1/datasets/all", force_reload=True)
        ret = self._TiraClient__matching_dataset(datasets, dataset_identifier)
        if ret is not None:
            return ret

        msg = f'The dataset "{dataset_identifier}" is not publicly available in TIRA. Please visit https://tira.io/datasets for an overview of all public datasets.'
        print(msg)
        raise ValueError(msg)

    def docker_software_id(self, approach):
        return self.docker_software(approach)["docker_software_id"]

    def all_softwares(self, task_id):
        """
        Return all public submissions.
        """
        return [
            task_id + "/" + i["vm_id"] + "/" + i["display_name"]
            for i in self.json_response(f"/api/task/{task_id}/public-submissions")["context"]["public_submissions"]
        ]

    def all_tasks(self):
        return self.json_response(f"/tira-backend/api/task-list")["context"]["task_list"]

    def docker_software(self, approach):
        task, team, software = approach.split("/")
        return self.json_response(f"/api/task/{task}/submission-details/{team}/{software}")["context"]["submission"]

    def docker_credentials(self, task_name, team_name):
        ret = self.metadata_for_task(task_name, team_name)
        if ret and "status" in ret and ret["status"] == 0 and "context" in ret and "docker" in ret["context"]:
            return (
                ret["context"]["docker"]["docker_registry_user"],
                ret["context"]["docker"]["docker_registry_token"],
                self.docker_registry(),
            )
        return None, None, self.docker_registry()

    def docker_software_details(self, approach):
        task, team, software = approach.split("/")
        ret = self.json_response(f"/task/{task}/vm/{team}/software_details/{software}")

        return ret

    def metadata_for_task(self, task_name: str, team_name: "Optional[str]" = None) -> Dict:
        if team_name is None:
            return self.json_response(f"/api/task/{task_name}")
        else:
            return self.json_response(f"/api/task/{task_name}/user/{team_name}")

    def add_docker_software(
        self,
        image,
        command,
        tira_vm_id,
        tira_task_id,
        code_repository_id,
        build_environment,
        previous_stages=[],
        mount_hf_model=[],
        source_code_remotes=None,
        source_code_commit=None,
        source_code_active_branch=None,
        try_run_metadata_uuid=None,
    ):
        headers = self.authentication_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        self.fail_if_api_key_is_invalid()
        url = f"{self.base_url}/task/{tira_task_id}/vm/{tira_vm_id}/add_software/docker"
        content = {
            "action": "post",
            "image": image,
            "command": command,
            "code_repository_id": code_repository_id,
            "build_environment": json.dumps(build_environment),
        }

        if previous_stages and len(previous_stages) > 0:
            content["inputJob"] = previous_stages

        if mount_hf_model and len(mount_hf_model) > 0:
            content["mount_hf_model"] = mount_hf_model

        if source_code_remotes:
            content["source_code_remotes"] = json.dumps(source_code_remotes)

        if source_code_commit:
            content["source_code_commit"] = source_code_commit

        if source_code_active_branch:
            content["source_code_active_branch"] = source_code_active_branch

        if try_run_metadata_uuid:
            content["try_run_metadata_uuid"] = try_run_metadata_uuid

        try:
            work_dir = self.local_execution.docker_image_work_dir(image)
            if work_dir and len(work_dir) > 2:
                content["tira_image_workdir"] = work_dir
        except:
            pass

        ret = requests.post(url, headers=headers, json=content, verify=self.verify)
        response_code = ret.status_code
        ret = ret.content.decode("utf8")
        try:
            ret = json.loads(ret)
        except Exception:
            msg = f"Upload of software failed with error {ret} and response code {response_code}."
            print(msg)
            raise ValueError(msg)

        if ret["status"] != 0:
            msg = f"Upload of software failed with error {ret}"
            print(msg)
            raise ValueError(msg)

        print(f'Software with name {ret["context"]["display_name"]} was created.')
        logging.info(f'Software with name {ret["context"]["display_name"]} was created.')
        logging.info(
            f"Please visit {self.base_url}/submit/{tira_task_id}/user/{tira_vm_id}/docker-submission to run your"
            " software."
        )
        return ret["context"]

    def submissions(self, task, dataset):
        response = self.json_response(f"/api/submissions/{task}/{dataset}")["context"]
        ret = []

        for vm in response["vms"]:
            for run in vm["runs"]:
                if "review" in run:
                    for k, v in run["review"].items():
                        run["review_" + k] = v
                    del run["review"]

                ret += [
                    {**{"task": response["task_id"], "dataset": response["dataset_id"], "team": vm["vm_id"]}, **run}
                ]

        return pd.DataFrame(ret)

    def upload_submissions(self, task_id, vm_id, upload_id, dataset=None):
        ret = self.json_response(f"/api/upload-group-details/{task_id}/{vm_id}/{upload_id}")
        ret = ret["context"]["upload_group_details"]["runs"]

        return [i for i in ret if dataset is None or dataset == i["dataset"]]

    def submissions_with_evaluation_or_none(self, task, dataset, team, software):
        """This method returns all runs of the specified software in the task on the dataset by the team.
        This is especially suitable to batch evaluate all submissions of the software because the evaluation is none if
        no successfull evaluation was conducted (or there is a new evaluator).
        E.g., by code like:

        .. code:: py

            for approach in ['approach-1', ..., 'approach-n]:
                runs_for_approach = tira.submissions_with_evaluation_or_none(task, dataset, team, approach)
                for i in runs_for_approach:
                    if not i['evaluation']:
                        tira.evaluate_run(team, dataset, i['run_id'])
        """
        submissions = self.submissions(task, dataset)
        evaluations = self.evaluations(task, dataset, join_submissions=False)
        run_to_evaluation = {}
        for _, i in evaluations.iterrows():
            i = i.to_dict()
            run_id = i["run_id"]
            del i["task"]
            del i["dataset"]
            del i["team"]
            del i["run_id"]
            run_to_evaluation[run_id] = i

        if len(submissions) < 1:
            return []

        submissions = submissions[
            (submissions["task"] == task)
            & (submissions["dataset"] == dataset)
            & (submissions["team"] == team)
            & (submissions["software"] == software)
        ]
        ret = []
        for run_id in submissions.run_id.unique():
            ret += [
                {
                    "run_id": run_id,
                    "task": task,
                    "dataset": dataset,
                    "team": team,
                    "software": software,
                    "evaluation": run_to_evaluation.get(run_id, None),
                }
            ]

        return ret

    def evaluations(self, task, dataset, join_submissions=True):
        response = self.json_response(f"/api/evaluations/{task}/{dataset}")["context"]
        ret = []
        evaluation_keys = response["ev_keys"]

        if join_submissions:
            runs_to_join = {}
            for _, i in self.submissions(task, dataset).iterrows():
                i = i.to_dict()
                runs_to_join[(i["team"], i["run_id"])] = {
                    "software": i["software"],
                    "input_run_id": i["input_run_id"],
                    "is_upload": i["is_upload"],
                    "is_docker": i["is_docker"],
                }

        for evaluation in response["evaluations"]:
            run = {
                "task": response["task_id"],
                "dataset": response["dataset_id"],
                "team": evaluation["vm_id"],
                "run_id": evaluation["input_run_id"],
                "evaluation_run_id": evaluation["run_id"],
                "published": evaluation["published"],
                "blinded": evaluation["blinded"],
            }

            if join_submissions and (run["team"], run["run_id"]) in runs_to_join:
                software = runs_to_join[(run["team"], run["run_id"])]
                for k, v in software.items():
                    run[k] = v

            for measure_id, measure in zip(range(len(evaluation_keys)), evaluation_keys):
                run[measure] = evaluation["measures"][measure_id]

            ret += [run]

        return pd.DataFrame(ret)

    def run_was_already_executed_on_dataset(self, approach, dataset):
        return self.get_run_execution_or_none(approach, dataset) is not None

    def load_resource(self, resource: str):
        """Load a resource (usually a zip) from TIRA/Zenodo. Serves as utikity function in case some additional
        resources must be loaded.

        Args:
            resource (str): The resource identifier

        Raises:
            ValueError: If the resource is not known.

        Returns:
            str: The path to the downloaded resource.
        """
        target_file = f"{self.tira_cache_dir}/raw_resources/{resource}"
        if os.path.exists(target_file):
            return target_file

        if resource not in RESOURCE_REDIRECTS:
            raise ValueError(f"Resource {resource} not supported.")

        os.makedirs(f"{self.tira_cache_dir}/raw_resources", exist_ok=True)
        self.download_and_extract_zip(RESOURCE_REDIRECTS[resource], target_file, extract=False)
        return target_file

    def get_run_output(self, approach: str, dataset: str, allow_without_evaluation: bool = False) -> Path:
        """
        Downloads the run (or uses the cached version) of the specified approach on the specified dataset.
        Returns the directory containing the outputs of the run.
        """
        mounted_output_in_sandbox = self.input_run_in_sandbox(approach)
        if mounted_output_in_sandbox:
            return Path(mounted_output_in_sandbox)

        task, team, software = approach.split("/")
        if "/" in dataset and not Path(dataset).exists():
            dataset = dataset.split("/")[-1]

        run_execution = self.get_run_execution_or_none(approach, dataset)

        if run_execution:
            return self.download_zip_to_cache_directory(task, dataset, team, run_execution["run_id"])

        run_execution = self.submissions_with_evaluation_or_none(task, dataset, team, software)
        run_execution = [
            i for i in run_execution if ("evaluation" in i and i["evaluation"]) or allow_without_evaluation
        ]

        if run_execution is None or len(run_execution) < 1:
            raise ValueError(f'Could not get run for approach "{approach}" on dataset "{dataset}".')

        return self.download_zip_to_cache_directory(
            run_execution[0]["task"], run_execution[0]["dataset"], run_execution[0]["team"], run_execution[0]["run_id"]
        )

    def public_runs(self, task, dataset, team, software):
        ret = self.json_response(f"/api/list-runs/{task}/{dataset}/{team}/" + software.replace(" ", "%20"))
        if ret and "context" in ret and "runs" in ret["context"] and ret["context"]["runs"]:
            return ret["context"]
        else:
            return None

    def public_system_details(self, team_name, system_name, force_reload=False):
        endpoint = f"/v1/systems/{team_name}/{system_name}".replace(" ", "%20")
        ret = None

        try:
            ret = self.archived_json_response(endpoint, force_reload=force_reload)
        except:
            pass

        if ret is None:
            try:
                ret = self.archived_json_response(endpoint, force_reload=True)
            except:
                pass

        if ret is None:
            msg = f'The software "{system_name}" by team {team_name} is not publicly available in TIRA. Please visit https://tira.io/systems for an overview of all public systems.'
            print(msg)
            raise ValueError(msg)

        return ret

    def get_run_execution_or_none(self, approach: str, dataset: str, previous_stage_run_id: str = None) -> Dict:
        task, team, software = approach.split("/")
        system_details = self.public_system_details(team, software)
        redirect = redirects(approach, dataset)

        if redirect is not None and "run_id" in redirect and redirect["run_id"] is not None:
            return {"task": task, "dataset": dataset, "team": team, "run_id": redirect["run_id"]}

        if self.dataset_only_available_locally(dataset) and self.allow_local_execution:
            return self.local_execution.run_and_return_tira_execution(task, dataset, team, system_details)

        public_runs = self.public_runs(task, dataset, team, software)
        if public_runs:
            return {"task": task, "dataset": dataset, "team": team, "run_id": public_runs["runs"][0]}

        if not self.api_key_is_valid():
            raise ValueError(
                f'No public submissions for "{approach} on "{dataset}" and you are not authenticated. Please authenticate to access private submissions'
            )

        df_eval = self.submissions_of_team(task=task, dataset=dataset, team=team)
        if len(df_eval) <= 0:
            return None

        ret = df_eval[(df_eval["dataset"] == dataset) & (df_eval["software"] == software)]
        if len(ret) <= 0:
            return None

        if team:
            ret = ret[ret["team"] == team]

        # FIXME: Is this really necessary or is it checked with the if len(ret) <= 0 later on?
        if len(ret) <= 0:
            return None

        if previous_stage_run_id:
            ret = ret[ret["input_run_id"] == previous_stage_run_id]

        if len(ret) <= 0:
            return None

        return ret[["task", "dataset", "team", "run_id"]].iloc[0].to_dict()

    def download_run(self, task, dataset, software, team=None, previous_stage=None, return_metadata=False):
        mounted_output_in_sandbox = self.input_run_in_sandbox(f"{task}/{team}/{software}")
        if mounted_output_in_sandbox:
            ret = pd.read_csv(
                mounted_output_in_sandbox + "/run.txt",
                sep="\\s+",
                names=["query", "q0", "docid", "rank", "score", "system"],
                dtype={"query": str, "docid": str},
            )
            if return_metadata:
                return ret, "run-id"
            else:
                return ret

        if "/" in dataset and not Path(dataset).exists():
            dataset = dataset.split("/")[-1]
        ret = self.get_run_execution_or_none(f"{task}/{team}/{software}", dataset, previous_stage)
        if not ret:
            raise ValueError(
                f'I could not find a run for the filter criteria task="{task}", dataset="{dataset}",'
                f' software="{software}", team={team}, previous_stage={previous_stage}'
            )
        run_id = ret["run_id"]

        ret = self.download_zip_to_cache_directory(**{i: ret[i] for i in ["task", "dataset", "team", "run_id"]})
        ret = pd.read_csv(
            ret / "run.txt",
            sep="\\s+",
            names=["query", "q0", "docid", "rank", "score", "system"],
            dtype={"query": str, "docid": str},
        )
        if return_metadata:
            return ret, run_id
        else:
            return ret

    def download_evaluation(self, task, dataset, software, team):
        ret = self.submissions_with_evaluation_or_none(task, dataset, team, software)
        if not ret or len(ret) < 1:
            raise ValueError(
                f'I could not find a run for the filter criteria task="{task}", dataset="{dataset}",'
                f' software="{software}", team={team}.'
            )
        run_id = ret[0]["run_id"]

        submissions = self.submissions(task, dataset)
        submissions = submissions[(submissions["input_run_id"] == run_id) & (submissions["is_evaluation"])]

        if submissions is None or len(submissions) < 1:
            raise ValueError(
                f'I could not find a evaluation for the filter criteria task="{task}", dataset="{dataset}",'
                f' software="{software}", team={team}, run_id={run_id}.'
            )

        return self.download_zip_to_cache_directory(task, dataset, team, submissions.iloc[0].to_dict()["run_id"])

    def download_dataset(
        self, task: Optional[str], dataset: str, truth_dataset: bool = False, allow_local_dataset: bool = False
    ) -> Path:
        """
        Download the dataset. Set truth_dataset to true to load the truth used for evaluations.
        """
        if "TIRA_INPUT_DATASET" in os.environ:
            return Path(os.environ["TIRA_INPUT_DATASET"])
        if allow_local_dataset and Path(dataset).exists():
            return Path(dataset)
        if "/" in dataset and not Path(dataset).exists():
            dataset = dataset.split("/")[-1]

        meta_data = self.get_dataset(f"{task}/{dataset}" if task else dataset)
        data_type = "training" if dataset.endswith("-training") else "test"
        suffix = "inputs" if not truth_dataset else "truths"
        url = None
        expected_md5 = None
        subdirectory = None
        rename_to = None
        if (
            not meta_data
            or "mirrors" not in meta_data
            or suffix not in meta_data["mirrors"]
            or not meta_data["mirrors"][suffix]
        ):
            dataset = dataset_ir_redirects(dataset)
        else:
            url = list(meta_data["mirrors"][suffix].values())[0]

            if suffix in meta_data["mirrors"] and f"{suffix}-md5_sum" in meta_data["mirrors"]:
                expected_md5 = meta_data["mirrors"][f"{suffix}-md5_sum"]
                subdirectory = meta_data["mirrors"].get(f"{suffix}-subdirectory", None)
                rename_to = meta_data["mirrors"].get(f"{suffix}-rename_to", None)

        target_dir = f"{self.tira_cache_dir}/extracted_datasets/{task}/{dataset}/"
        suffix = "input-data" if not truth_dataset else "truth-data"
        if os.path.isdir(target_dir + suffix):
            return Path(target_dir + suffix)

        if not url:
            url = f'{self.base_url}/data-download/{data_type}/input-{("" if not truth_dataset else "truth")}/{dataset}.zip'

        if expected_md5:
            self.download_and_extract_zip_with_md5(url, target_dir + suffix, expected_md5, subdirectory, rename_to)
        else:
            self.download_and_extract_zip(url, target_dir)

            os.rename(target_dir + f"/{dataset}", target_dir + suffix)

        return Path(target_dir + suffix)

    def download_zip_to_cache_directory(self, task: str, dataset: str, team: str, run_id: str) -> Path:
        target_dir = f"{self.tira_cache_dir}/extracted_runs/{task}/{dataset}/{team}"
        if "/" in dataset:
            dataset = dataset.split("/")[-1]

        if os.path.isdir(target_dir + f"/{run_id}"):
            return Path(target_dir + f"/{run_id}/output")

        potential_local_matches = glob(f"{self.tira_cache_dir}/extracted_runs/{task}/{dataset}/*/{run_id}/output")
        if task in TASKS_WITH_REDIRECT_MERGING and len(potential_local_matches) == 1:
            return Path(potential_local_matches[0])

        self.download_and_extract_zip(
            f"{self.base_url}/task/{task}/user/{team}/dataset/{dataset}/download/{run_id}.zip", target_dir
        )

        return Path(target_dir) / run_id / "output"

    def add_run_to_leaderboard(self, task, team, dataset, evaluation_run_id=None, run_id=None):
        """
        Publish the specified run to the leaderboard.

        This is especially suitable to batch add all submissions of submissions, e.g., by code like:

        .. code:: py

            for approach in ['approach-1', ..., 'approach-n']:
                runs_for_approach = tira.submissions_with_evaluation_or_none(task, dataset, team, approach)
                for i in runs_for_approach:
                    if i['evaluation']:
                        tira.add_run_to_leaderboard(TASK, team, dataset, run_id=i['run_id'])

        """
        if run_id and evaluation_run_id:
            raise ValueError(
                "Please pass either a evaluation_run_id or a run_id, but both were passed:"
                f" evaluation_run_id={evaluation_run_id}, run_id={run_id}"
            )
        if run_id and not evaluation_run_id:
            submissions = self.submissions(task, dataset)
            submissions = submissions[(submissions["input_run_id"] == run_id) & (submissions["is_evaluation"])]

            for evaluation_run_id in submissions["run_id"].unique():
                self.add_run_to_leaderboard(task, team, dataset, evaluation_run_id=evaluation_run_id)

        if evaluation_run_id:
            self.publish_run(evaluation_run_id, dataset, team)

    def get_configuration_of_evaluation(self, task_id, dataset_id):
        """Get the configuration of the evaluator for the passed dataset inside the task specified by task_id."""
        ret = self.json_response(f"/api/configuration-of-evaluation/{task_id}/{dataset_id}")

        if "status" not in ret or "0" != str(ret["status"]):
            raise ValueError(f"Failed to load configuration of an evaluator. Got {ret}")

        return ret["context"]["dataset"]

    def evaluate_run(self, team, dataset, run_id):
        """Evaluate the run of the specified team and identified by the run_id (the run must be submitted on the
        specified dataset)."""
        ret = self.json_response(f"/grpc/{team}/run_eval/{dataset}/{run_id}")

        if "status" not in ret or "0" != str(ret["status"]):
            raise ValueError(f"Failed to evaluate the run. Got {ret}")

        return ret

    def download_and_extract_zip_with_md5(self, url, target_dir, expected_md5, subdirectory, rename_to=None):
        if expected_md5 is None or not expected_md5:
            raise ValueError("foo")

        if not (Path(self.tira_cache_dir) / ".archived" / expected_md5).exists():
            r = requests.get(url, stream=True)
            total = int(r.headers.get("content-length", 0))
            status_code = r.status_code
            if status_code < 200 or status_code >= 300:
                raise ValueError(f"Got non 200 status code {status_code} for {url}.")
            response_content = io.BytesIO()
            with tqdm(
                desc="Download",
                total=total,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in r.iter_content(chunk_size=1024):
                    size = response_content.write(data)
                    bar.update(size)

            actual_md5 = hashlib.md5(response_content.getbuffer()).hexdigest()
            if actual_md5 != expected_md5:
                raise ValueError(
                    f'MD5 is unexpected: I expected "{expected_md5}" but got "{actual_md5}" for URL "{url}".'
                )

            print("Download finished. Persist...")
            with open(Path(self.tira_cache_dir) / ".archived" / expected_md5, "wb") as file_out:
                file_out.write(response_content.getbuffer())

        if rename_to and not subdirectory:
            Path(target_dir).mkdir(exist_ok=True, parents=True)
            shutil.copy(src=Path(self.tira_cache_dir) / ".archived" / expected_md5, dst=Path(target_dir) / rename_to)
        else:
            z = zipfile.ZipFile((Path(self.tira_cache_dir) / ".archived" / expected_md5))

            members_to_extract = []
            for i in z.namelist():
                if i and not i.endswith("/") and (not subdirectory or i.startswith(subdirectory)):
                    members_to_extract.append(i)

            if len(members_to_extract) == 0:
                raise ValueError("I found no files in te zip.")

            with tempfile.TemporaryDirectory() as tmpdirname:
                for i in members_to_extract:
                    z._extract_member(i, Path(tmpdirname), pwd=None)

                src_dir = Path(tmpdirname)
                if subdirectory:
                    src_dir = src_dir / subdirectory
                Path(target_dir).parent.mkdir(exist_ok=True, parents=True)
                shutil.move(src=src_dir, dst=target_dir)

        return

    def download_and_extract_zip(self, url: str, target_dir: str, extract: bool = True):
        url = redirects(url=url)["urls"][0]
        if "://" in url and url.split("://")[1].startswith("files.webis.de"):
            print(f"Download from the Incubator: {url}")
            print("\tThis is only used for last spot checks before archival to Zenodo.")

        if "://" in url and url.split("://")[1].startswith("zenodo.org"):
            print(f"Download from Zenodo: {url}")

        run_id = None if ("/download/" not in url or ".zip" not in url) else url.split("/download/")[1].split(".zip")[0]

        for _ in range(self.failsave_retries):
            status_code = None
            try:

                headers = self.authentication_headers()
                r = requests.get(url, headers=headers, stream=True, verify=self.verify)
                total = int(r.headers.get("content-length", 0))
                status_code = r.status_code
                if (
                    status_code == 302
                    and r.headers
                    and "X-Disraptor-Location" in r.headers
                    and "/dataset/" in url
                    and "/user/" in url
                    and run_id is not None
                ):
                    new_url = r.headers["X-Disraptor-Location"]
                    uuid = new_url.split("/v1/anonymous/")[1].split(".zip")[0]
                    self.download_and_extract_zip(new_url, Path(target_dir) / run_id, extract)
                    src_dir = Path(target_dir) / run_id
                    shutil.move(src_dir / uuid, src_dir / "output")
                    return
                if status_code < 200 or status_code >= 300:
                    raise ValueError(f"Got non 200 status code {status_code} for {url}.")

                response_content = io.BytesIO()
                with tqdm(
                    desc="Download",
                    total=total,
                    unit="iB",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for data in r.iter_content(chunk_size=1024):
                        size = response_content.write(data)
                        bar.update(size)
                if extract:
                    print("Download finished. Extract...")
                    z = zipfile.ZipFile(response_content)
                    z.extractall(target_dir)
                    print("Extraction finished: ", target_dir)
                else:
                    print("Download finished. Persist...")
                    with open(target_dir, "wb") as file_out:
                        file_out.write(response_content.getbuffer())
                    print("Download finished: ", target_dir)

                return
            except Exception as e:
                sleep_time = randint(1, self.failsave_max_delay)
                print(f"Code: {status_code}")
                print(f"Error occured while fetching {url}: {e}. I will sleep {sleep_time} seconds and continue.")
                url = mirror_url(url)
                time.sleep(sleep_time)

    def login(self, token: str) -> None:
        self.api_key = token

        if not self.api_key_is_valid():
            msg = f"The api key {token} is not valid"
            print(msg)
            raise ValueError(msg)

        self.update_settings("api_key", token)

    def get_authentication_cookie(self, user, password):
        resp = requests.get(f"{self.base_url}/session/csrf", headers={"x-requested-with": "XMLHttpRequest"})

        header = {
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "cookie": "_forum_session=" + resp.cookies["_forum_session"],
            "x-csrf-token": resp.json()["csrf"],
            "x-requested-with": "XMLHttpRequest",
        }

        resp = requests.post(f"{self.base_url}/session", data=f"login={user}&password={password}", headers=header)

        return f'_t={resp.cookies["_t"]}; _forum_session={resp.cookies["_forum_session"]}'

    def authentication_headers(self) -> Dict:
        ret = {}
        if self.api_key != "no-api-key":
            ret["Api-Key"] = self.api_key
        if self.api_user_name != "no-api-key-user":
            ret["Api-Username"] = self.api_user_name

        if "Header" in self.load_settings():
            for k, v in self.load_settings()["Header"].items():
                ret[k] = v

        return ret

    def run_software(self, approach, dataset, resources, rerank_dataset="none", software_id=None):
        task, team, software = approach.split("/")
        authentication_cookie = self.get_authentication_cookie(
            self.load_settings()["user"], self.load_settings()["password"]
        )

        if not software_id:
            software_id = self.docker_software_id(approach)
        if not software_id:
            raise ValueError(f'Could not find software id for "{approach}". Got: "{software_id}".')

        url = (
            f"{self.base_url}/grpc/{task}/{team}/run_execute/docker/"
            "{dataset}/{software_id}/{resources}/{rerank_dataset}"
        )
        logging.info(f"Start software...\n\t{url}\n")

        csrf_token = self.get_csrf_token()
        headers = {
            # 'Api-Key': self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cookie": authentication_cookie,
            "x-csrftoken": csrf_token,
        }

        ret = requests.post(url, headers=headers, json={"csrfmiddlewaretoken": csrf_token, "action": "post"})
        ret = ret.content.decode("utf8")
        logging.info(ret)
        ret = json.loads(ret)
        assert ret["status"] == 0

    def review_run(
        self,
        run_id: str,
        dataset_id: str,
        team: str,
        no_errors: bool,
        output_error: bool,
        software_error: bool,
        comment: str,
    ):
        dataset_id = "trec-28-deep-learning-passages-20250926-training"
        team = "reneuir-baselines"
        review = {
            "no_errors": no_errors,
            "output_error": output_error,
            "software_error": software_error,
            "comment": comment,
        }

        ret = self.execute_post_return_json(
            f"/tira-admin/edit-review/{dataset_id}/{team}/{run_id}", json_payload=review
        )
        print(ret)

        assert ret["status"] == 0

    def publish_run(self, run_id: str, dataset: str, team: str):
        logging.info(f"Publish run: {run_id}.")
        ret = self.json_response(f"/publish/{team}/{dataset}/{run_id}/true")

        if ("status" not in ret) or ("0" != ret["status"]) or ("published" not in ret) or (not ret["published"]):
            raise ValueError(f"Publishing the run failed. Got {ret}")

    def unblind_run(self, run_id: str, dataset: str, team: str):
        logging.info(f"Unblind run: {run_id}.")
        ret = self.json_response(f"/blind/{team}/{dataset}/{run_id}/false")
        if ("status" not in ret) or ("0" != ret["status"]) or ("blinded" not in ret) or (ret["blinded"]):
            raise ValueError(f"Publishing the run failed. Got {ret}")

    def get_upload_group_id(self, task_id: str, vm_id: str, display_name: str, failsave: bool = False) -> int:
        """Get the id of the upload group of user specified with vm_id for the task task_id with the display_name.
        Raises an error if no matching upload_group was found."""
        url = f"/api/submissions-for-task/{task_id}/{vm_id}/upload"
        ret = self.json_response(url)
        if "context" not in ret or "all_uploadgroups" not in ret["context"]:
            logging.error("Failed to get upload id, response does not contain the expected fields.")
            raise ValueError(f"Invalid response for request {url}: {ret}.")

        for upload_group in ret["context"]["all_uploadgroups"]:
            if display_name is not None and upload_group["display_name"] == display_name:
                return upload_group["id"]

        if not failsave:
            logging.error(
                f"Could not find upload with display_name {display_name} for task {task_id} of user {vm_id}. Got:",
                ret["context"]["all_uploadgroups"],
            )
            raise ValueError(
                "Could not find upload with display_name {display_name} for task {task_id} of user {vm_id}. Got:",
                ret["context"]["all_uploadgroups"],
            )

    def create_upload_group(self, task_id: str, vm_id: str, display_name: str) -> "Optional[str]":
        # TODO: check that task_id and vm_id don't contain illegal characters (e.g., '/')
        # TODO: Make this idempotent: reuse existing upload group if it already exists.
        url = f"{self.base_url}/task/{task_id}/vm/{vm_id}/add_software/upload"
        logging.debug(f"Creating a new upload at {url}")
        ret = self.json_response(url)

        logging.debug(f"Created new upload with id {ret['upload']}")
        return ret["upload"]

    def upload_run_admin(self, dataset: str, team: str, file_path: Path) -> None:
        from tira.io_utils import zip_dir

        zip_file = zip_dir(file_path)
        self.execute_post_return_json(f"/v1/admin/upload-response/{dataset}/{team}", file_path=zip_file)

    def upload_run_anonymous(self, file_path: Path, dataset_id: str, dry_run: bool = False, verbose: bool = False):
        print(f"I check that the submission in directory '{file_path}' is valid...")
        upload_to_tira = self.get_dataset(dataset_id)

        if isinstance(file_path, str):
            file_path = Path(file_path)

        accepted_formats = []
        error_msg = ""

        if isinstance(upload_to_tira.get("format"), list):
            accepted_formats = upload_to_tira.get("format")
        if len(accepted_formats) == 0:
            accepted_formats = ["run.txt"]  # default format

        format_configuration = upload_to_tira.get("format_configuration")

        for format in accepted_formats:
            status_code, msg = check_format(file_path, format, format_configuration)

            if status_code != _fmt.OK:
                error_msg += "\n" + msg
            else:
                print("\t" + fmt_message(msg.strip(), status_code))
                error_msg = ""
                break

        if error_msg:
            print(error_msg)

            print(
                "\nResult:\n\t"
                + fmt_message(
                    f"Could not upload to TIRA as the directory {file_path} is not a valid submission.", _fmt.ERROR
                )
            )
            return False
        from tira.io_utils import TqdmUploadFile, flush_stdout_and_stderr, zip_dir

        if dry_run:
            print(
                "\nResult:\n\t"
                + fmt_message("The run is valid. I skip upload to TIRA as --dry-run was passed.", _fmt.OK)
            )
            return

        zip_file = zip_dir(file_path)
        print("\n", flush=True)
        tqdm_zip_file = TqdmUploadFile(zip_file, f"Upload {file_path} to TIRA")

        headers = {"Accept": "application/json"}
        files = {"file": (os.path.basename(zip_file), tqdm_zip_file)}

        resp = requests.post(
            url=f"{self.base_url_api}/api/v1/anonymous-uploads/{upload_to_tira['dataset_id']}",
            files=files,
            headers=headers,
            verify=self.verify,
        )

        if resp.status_code not in {200, 202}:
            message = resp.content.decode()
            flush_stdout_and_stderr(tqdm_zip_file)
            try:
                message = json.loads(message)
                message = message["message"]
            except:
                pass
            message = f"Failed to upload to TIRA, got statuscode {resp.status_code}. Details: {message}"
            print(message)
            raise ValueError(message)

        resp = resp.json()
        flush_stdout_and_stderr(tqdm_zip_file)
        if verbose:
            print(
                "\t"
                + fmt_message(
                    f'Run uploaded to TIRA. Claim ownership via: {self.base_url}/claim-submission/{resp["uuid"]}',
                    _fmt.OK,
                )
            )
        else:
            print("\t" + fmt_message(f"The data is uploaded.", _fmt.OK))
        return resp

    def create_group(self, vm_id):
        if not vm_id or vm_id != vm_id.lower() or len(vm_id.split()) > 1:
            raise ValueError("The name of the group must be slugified: " + str(vm_id))

        if "tira" in vm_id:
            raise ValueError('The phrase "tira" should not be in the name of the group, got: ' + str(vm_id))

        return self.json_response("/tira-admin/create-group/" + vm_id)

    def register_group(
        self,
        vm_id,
        task_id,
        team_members="",
        name="",
        email="",
        affiliation="",
        country="",
        employment="",
        participates_for="",
        instructor_name="",
        instructor_email="",
        questions="",
    ):

        self.fail_if_api_key_is_invalid()
        user_id = self.json_response("/api/role")["context"]["user_id"]

        endpoint = f"/api/registration/add_registration/{vm_id}/{task_id}"
        body = {
            "group": vm_id,
            "team_members": team_members,
            "team": team_members,
            "registered_on_task": task_id,
            "username": user_id,
            "name": name,
            "email": email,
            "affiliation": affiliation,
            "country": country,
            "employment": employment,
            "participation": participates_for,
            "instructorName": instructor_name,
            "instructorEmail": instructor_email,
            "questions": questions,
        }

        return self.execute_post_return_json(endpoint, json_payload=body)

    def modify_task(self, task_id: str, to_rename: "Dict[str, Any]") -> None:
        task = self.metadata_for_task(task_id)["context"]["task"]
        fields_to_rename = {
            "name": "task_name",
            "description": "task_description",
            "website": "web",
            "help_text": "command_description",
            "help_command": "command_placeholder",
            "task_teams": "allowed_task_teams",
            "aggregated_results": "aggregated_results",
        }
        for k, v in fields_to_rename.items():
            task[k] = task[v]
            del task[v]

        if "aggregated_results" in to_rename:
            if len(to_rename["aggregated_results"]) == 0:
                raise ValueError("Empty aggregated results is not allowed.")

            for aggregated_result in to_rename["aggregated_results"]:
                with tempfile.TemporaryDirectory() as tmp:
                    json.dump(aggregated_result, open(f"{tmp}/aggregated-results.json", "w"))
                    c, msg = check_format(Path(tmp), "aggregated-results.json")
                    if c != _fmt.OK:
                        raise ValueError("Aggregated result is invalid: " + msg)
            task["aggregated_results"] = None

        for k, v in to_rename.items():
            assert k in task, k
            task[k] = v

        ret = self.execute_post_return_json("/tira-admin/edit-task/" + task_id, json_payload=task)
        if "status" not in ret or ret["status"] != 0:
            raise ValueError(f"Could not edit task: {ret}")

    def upload_run(
        self,
        file_path: Path,
        dataset_id: str,
        approach: str = None,
        task_id: str = None,
        vm_id: str = None,
        upload_id: str = None,
        allow_multiple_uploads=False,
    ) -> bool:
        """
        Returns true if the upload was successfull, false if not, or none if it was already uploaded.
        """
        logging.info(f"Submitting {upload_id} for Task {task_id}:{dataset_id} on VM {vm_id}")
        if approach:
            task_id, vm_id, display_name = approach.split("/")
            upload_id = self.get_upload_group_id(task_id, vm_id, display_name)

        previous_uploads = self.upload_submissions(task_id, vm_id, upload_id, dataset_id)
        if len(previous_uploads) > 0:
            logging.warn(
                f"Skip upload of file {file_path} for dataset {dataset_id} because there are already"
                f" {len(previous_uploads)} for this dataset. Pass allow_multiple_uploads=True to upload a new dataset"
                " or delete the uploads in the UI."
            )
            return None

        self.fail_if_api_key_is_invalid()

        if file_path is None or not file_path.is_file():
            logging.warn(f"The passed file {file_path} does not exist.")
            raise ValueError(f"The passed file {file_path} does not exist.")

        # TODO: check that task_id and vm_id don't contain illegal characters (e.g., '/')
        url = f"/task/{task_id}/vm/{vm_id}/upload/{dataset_id}/{upload_id}"
        logging.info(f"Submitting the runfile at {url}")
        response = self.execute_post_return_json(url, file_path=file_path)

        return (
            "status" in response
            and response["status"] == 0
            and "message" in response
            and response["message"] == "ok"
            and "new_run" in response
        )

    def get_csrf_token(self):
        self.fail_if_api_key_is_invalid()
        ret = self.json_response("/api/role")
        return ret["csrf"]

    def execute_post_return_json(
        self,
        endpoint: str,
        params: "Optional[Union[Dict, List[tuple], bytes]]" = None,
        file_path: "Path" = None,
        json_payload: "Any" = None,
    ) -> Dict:
        assert endpoint.startswith("/")
        csrf = self.get_csrf_token()

        headers = self.authentication_headers()
        headers["Accept"] = "application/json"
        headers["x-csrftoken"] = csrf
        headers["Cookie"] = f"csrftoken={csrf}"

        for _ in range(self.failsave_retries):
            try:
                files = None if not file_path else {"file": open(file_path, "rb")}

                resp = requests.post(
                    url=f"{self.base_url}{endpoint}",
                    files=files,
                    headers=headers,
                    params=params,
                    json=json_payload,
                    verify=self.verify,
                )
                if resp.status_code not in {200, 202}:
                    raise ValueError(f"Got statuscode {resp.status_code} for {endpoint}. Got {resp.content}")
                else:
                    break
            except Exception as e:
                sleep_time = randint(1, self.failsave_max_delay)
                resp_code = resp.status_code if "resp" in locals() else "unknown-response-code"
                logging.warning(
                    f"Error occured while fetching {endpoint}. Code: {resp_code}. I will sleep"
                    f" {sleep_time} seconds and continue.",
                    exc_info=e,
                )
                time.sleep(sleep_time)

        return resp.json()

    @lru_cache(maxsize=None)
    def archived_json_response(self, endpoint: str, force_reload: bool = False):
        out = Path(self.tira_cache_dir) / ".archived" / Path(endpoint[1:])
        if endpoint.endswith("/"):
            out = out / "index.json"

        if out.exists() and not force_reload:
            return json.load(open(out, "r"))

        out.parent.mkdir(exist_ok=True, parents=True)
        base_url = self.archive_base_url if not force_reload else self.base_url
        response = self.json_response(endpoint, base_url=base_url, failsave_retries=1)

        with open(out, "w") as f:
            f.write(json.dumps(response))

        return json.load(open(out, "r"))

    @lru_cache(maxsize=None)
    def json_response(
        self,
        endpoint: str,
        params: "Optional[Union[Dict, List[tuple], bytes]]" = None,
        base_url: "Optional[str]" = None,
        failsave_retries: "Optional[int]" = None,
    ) -> Dict:
        if failsave_retries is None:
            failsave_retries = self.failsave_retries
        assert endpoint.startswith("/")
        headers = self.authentication_headers()
        headers["Accept"] = "application/json"

        base_url = base_url if base_url else self.base_url

        for _ in range(failsave_retries):
            try:
                resp = requests.get(url=f"{base_url}{endpoint}", headers=headers, verify=self.verify, params=params)
                if resp.status_code not in {200, 202}:
                    raise ValueError(f"Got statuscode {resp.status_code} for {endpoint}. Got {resp}")
                else:
                    break
            except Exception as e:
                if "resp" not in vars() or resp.status_code in {403, 404}:
                    raise e

                sleep_time = randint(1, self.failsave_max_delay)
                response_code = "'unknown response code, maybe there was a timeout?'"
                try:
                    response_code = resp.status_code
                except Exception:
                    pass
                logging.warn(
                    f"Error occured while fetching {endpoint}. Code: {response_code}. I will sleep {sleep_time} seconds"
                    " and continue.",
                    exc_info=e,
                )

                if failsave_retries > 1:
                    time.sleep(sleep_time)

        return resp.json()

    def __listdir_failsave(self, path: str):
        try:
            return os.listdir(path)
        except Exception:
            return []

    def _well_known(self):
        pass

    def input_run_in_sandbox(self, approach: str):
        """
        Returns the directory with the outputs of an approach in mounted into the sandbox. returns None if not in the
        sandbox.
        """
        if "inputRun" not in os.environ:
            return None

        input_run = os.environ["inputRun"]
        input_run_mapping_file = Path(self.tira_cache_dir) / (
            hashlib.md5(input_run.encode("utf-8")).hexdigest()[:6] + "-input-run-mapping.json"
        )

        files_in_input_dir = self.__listdir_failsave(input_run)
        if "1" not in files_in_input_dir or "2" not in files_in_input_dir:
            return input_run

        input_run_mapping = {}
        if input_run_mapping_file.exists():
            input_run_mapping = json.load(open(input_run_mapping_file, "r"))

        if approach not in input_run_mapping:
            next_id = max(list(input_run_mapping.values()) + [0]) + 1
            input_run_mapping[approach] = next_id
            os.makedirs(self.tira_cache_dir, exist_ok=True)
            json.dump(input_run_mapping, open(input_run_mapping_file, "w+"))

        return input_run + "/" + str(input_run_mapping[approach])
