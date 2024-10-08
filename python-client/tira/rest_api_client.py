import hashlib
import io
import json
import logging
import os
import time
import zipfile
from functools import lru_cache
from glob import glob
from pathlib import Path
from random import randint
from typing import Dict, List, Optional, Union

import pandas as pd
import requests
from tqdm import tqdm

from tira.local_execution_integration import LocalExecutionIntegration
from tira.pandas_integration import PandasIntegration
from tira.profiling_integration import ProfilingIntegration
from tira.pyterrier_integration import PyTerrierAnceIntegration, PyTerrierIntegration, PyTerrierSpladeIntegration
from tira.tira_redirects import (
    RESOURCE_REDIRECTS,
    TASKS_WITH_REDIRECT_MERGING,
    dataset_ir_redirects,
    mirror_url,
    redirects,
)

from .tira_client import TiraClient


class Client(TiraClient):
    base_url: str

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: str = None,
        failsave_retries: int = 5,
        failsave_max_delay: int = 15,
        api_user_name: Optional[str] = None,
    ):
        self.base_url = base_url or "https://www.tira.io"
        self.tira_cache_dir = os.environ.get("TIRA_CACHE_DIR", os.path.expanduser("~") + "/.tira")
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
        self.pd = PandasIntegration(self)
        self.pt = PyTerrierIntegration(self)
        self.profiling = ProfilingIntegration(self)
        self.pt_ance = PyTerrierAnceIntegration(self)
        self.pt_splade = PyTerrierSpladeIntegration(self)
        self.local_execution = LocalExecutionIntegration(self)

        self.failsave_retries = failsave_retries
        self.failsave_max_delay = failsave_max_delay

    def load_settings(self):
        try:
            ret = json.load(open(self.tira_cache_dir + "/.tira-settings.json", "r"))
            if "api_key" not in ret:
                ret["api_key"] = "no-api-key"
            if "api_user_name" not in ret:
                ret["api_user_name"] = "no-api-key-user"
            return ret
        except Exception:
            logging.info(f"No settings given in {self.tira_cache_dir}/.tira-settings.json. I will use defaults.")
            return {"api_key": "no-api-key", "api_user_name": "no-api-key-user"}

    def update_settings(self, k, v):
        settings = self.load_settings()
        settings[k] = v
        os.makedirs(self.tira_cache_dir, exist_ok=True)
        json.dump(settings, open(Path(self.tira_cache_dir) / ".tira-settings.json", "w+"))

        if k == "api_key":
            self.api_key = settings["api_key"]

    def api_key_is_valid(self):
        role = self.json_response("/api/role")

        if (
            (self.api_user_name is None or self.api_user_name == "no-api-key-user")
            and role
            and "context" in role
            and "user_id" in role["context"]
            and role["context"]["user_id"]
        ):
            self.api_user_name = role["context"]["user_id"]

        return (
            role
            and "status" in role
            and "role" in role
            and 0 == role["status"]
            and "user_id" in role["context"]
            and role["context"]["user_id"]
            and "role" in role["context"]
            and role["context"]["role"]
            and "guest" != role["context"]["role"]
        )

    def fail_if_api_key_is_invalid(self):
        if not self.api_key_is_valid():
            role = self.json_response("/api/role")
            raise ValueError("It seems like the api key is invalid. Got: ", role)

    def datasets(self, task):
        return json.loads(self.json_response(f"/api/datasets_by_task/{task}")["context"]["datasets"])

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

    def metadata_for_task(self, task_name, team_name=None):
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
    ):
        headers = {
            "Api-Key": self.api_key,
            "Api-Username": self.api_user_name,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
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

        ret = requests.post(url, headers=headers, json=content)
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

    def get_run_output(self, approach, dataset, allow_without_evaluation=False):
        """
        Downloads the run (or uses the cached version) of the specified approach on the specified dataset.
        Returns the directory containing the outputs of the run.
        """
        mounted_output_in_sandbox = self.input_run_in_sandbox(approach)
        if mounted_output_in_sandbox:
            return mounted_output_in_sandbox

        task, team, software = approach.split("/")
        if "/" in dataset:
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

    def get_run_execution_or_none(self, approach, dataset, previous_stage_run_id=None):
        task, team, software = approach.split("/")
        redirect = redirects(approach, dataset)

        if redirect is not None and "run_id" in redirect and redirect["run_id"] is not None:
            return {"task": task, "dataset": dataset, "team": team, "run_id": redirect["run_id"]}

        public_runs = self.public_runs(task, dataset, team, software)
        if public_runs:
            return {"task": task, "dataset": dataset, "team": team, "run_id": public_runs["runs"][0]}

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

        if "/" in dataset:
            dataset = dataset.split("/")[-1]
        ret = self.get_run_execution_or_none(f"{task}/{team}/{software}", dataset, previous_stage)
        if not ret:
            raise ValueError(
                f'I could not find a run for the filter criteria task="{task}", dataset="{dataset}",'
                f' software="{software}", team={team}, previous_stage={previous_stage}'
            )
        run_id = ret["run_id"]

        ret = self.download_zip_to_cache_directory(**ret)
        ret = pd.read_csv(
            ret + "/run.txt",
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

    def download_dataset(self, task, dataset, truth_dataset=False):
        """
        Download the dataset. Set truth_dataset to true to load the truth used for evaluations.
        """
        if "TIRA_INPUT_DATASET" in os.environ:
            return os.environ["TIRA_INPUT_DATASET"]
        if "/" in dataset:
            dataset = dataset.split("/")[-1]

        dataset = dataset_ir_redirects(dataset)

        target_dir = f"{self.tira_cache_dir}/extracted_datasets/{task}/{dataset}/"
        suffix = "input-data" if not truth_dataset else "truth-data"
        if os.path.isdir(target_dir + suffix):
            return target_dir + suffix
        data_type = "training" if dataset.endswith("-training") else "test"
        self.download_and_extract_zip(
            f'{self.base_url}/data-download/{data_type}/input-{("" if not truth_dataset else "truth")}/{dataset}.zip',
            target_dir,
        )

        os.rename(target_dir + f"/{dataset}", target_dir + suffix)

        return target_dir + suffix

    def download_zip_to_cache_directory(self, task, dataset, team, run_id):
        target_dir = f"{self.tira_cache_dir}/extracted_runs/{task}/{dataset}/{team}"

        if os.path.isdir(target_dir + f"/{run_id}"):
            return target_dir + f"/{run_id}/output"

        potential_local_matches = glob(f"{self.tira_cache_dir}/extracted_runs/{task}/{dataset}/*/{run_id}/output")
        if task in TASKS_WITH_REDIRECT_MERGING and len(potential_local_matches) == 1:
            return potential_local_matches[0]

        self.download_and_extract_zip(
            f"{self.base_url}/task/{task}/user/{team}/dataset/{dataset}/download/{run_id}.zip", target_dir
        )

        return target_dir + f"/{run_id}/output"

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
            logging.info(f"Publish run: {evaluation_run_id}.")
            ret = self.json_response(f"/publish/{team}/{dataset}/{evaluation_run_id}/true")

            if ("status" not in ret) or ("0" != ret["status"]) or ("published" not in ret) or (not ret["published"]):
                raise ValueError(f"Adding the run to the leaderboard failed. Got {ret}")

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

    def download_and_extract_zip(self, url, target_dir, extract=True):
        url = redirects(url=url)["urls"][0]
        if url.split("://")[1].startswith("files.webis.de"):
            print(f"Download from the Incubator: {url}")
            print("\tThis is only used for last spot checks before archival to Zenodo.")

        if url.split("://")[1].startswith("zenodo.org"):
            print(f"Download from Zenodo: {url}")

        for _ in range(self.failsave_retries):
            status_code = None
            try:
                headers = {"Api-Key": self.api_key, "Api-Username": self.api_user_name}
                if self.api_key == "no-api-key":
                    del headers["Api-Key"]
                if self.api_user_name == "no-api-key-user":
                    del headers["Api-Username"]

                r = requests.get(url, headers=headers, stream=True)
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
            except Exception:
                sleep_time = randint(1, self.failsave_max_delay)
                print(f"Code: {status_code}")
                print(f"Error occured while fetching {url}. I will sleep {sleep_time} seconds and continue.")
                url = mirror_url(url)
                time.sleep(sleep_time)

    def login(self, token):
        self.api_key = token

        if not self.api_key_is_valid():
            print("The api key {token} is not valid")
            raise ValueError(f"The api key {token} is invalid.")

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

    def get_upload_group_id(self, task_id: str, vm_id: str, display_name: str) -> int:
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

        logging.error(
            f"Could not find upload with display_name {display_name} for task {task_id} of user {vm_id}. Got:",
            ret["context"]["all_uploadgroups"],
        )
        raise ValueError(
            "Could not find upload with display_name {display_name} for task {task_id} of user {vm_id}. Got:",
            ret["context"]["all_uploadgroups"],
        )

    def create_upload_group(self, task_id: str, vm_id: str, display_name: str) -> Optional[str]:
        # TODO: check that task_id and vm_id don't contain illegal characters (e.g., '/')
        # TODO: Make this idempotent: reuse existing upload group if it already exists.
        url = f"{self.base_url}/task/{task_id}/vm/{vm_id}/add_software/upload"
        logging.debug(f"Creating a new upload at {url}")
        ret = self.json_response(url)

        logging.debug(f"Created new upload with id {ret['upload']}")
        return ret["upload"]

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
        ret = requests.get(f"{self.base_url}/", headers={"Api-Key": self.api_key})
        return ret.content.decode("utf-8").split('name="csrfmiddlewaretoken" value="')[1].split('"')[0]

    def execute_post_return_json(
        self, endpoint: str, params: Optional[Union[Dict, List[tuple], bytes]] = None, file_path: Path = None
    ) -> Dict:
        assert endpoint.startswith("/")
        headers = {
            "Api-Key": self.api_key,
            "Api-Username": self.api_user_name,
            "Accept": "application/json",
        }
        for _ in range(self.failsave_retries):
            try:
                files = {"file": open(file_path, "rb")}

                resp = requests.post(url=f"{self.base_url}{endpoint}", files=files, headers=headers, params=params)
                if resp.status_code not in {200, 202}:
                    raise ValueError(f"Got statuscode {resp.status_code} for {endpoint}. Got {resp.content}")
                else:
                    break
            except Exception as e:
                sleep_time = randint(1, self.failsave_max_delay)
                logging.warn(
                    f"Error occured while fetching {endpoint}. Code: {resp.status_code}. I will sleep"
                    f" {sleep_time} seconds and continue.",
                    exc_info=e,
                )
                time.sleep(sleep_time)

        return resp.json()

    @lru_cache(maxsize=None)
    def json_response(self, endpoint: str, params: Optional[Union[Dict, List[tuple], bytes]] = None):
        assert endpoint.startswith("/")
        headers = {"Accept": "application/json"}

        if self.api_key != "no-api-key":
            headers["Api-Key"] = self.api_key
        if self.api_user_name != "no-api-key-user":
            headers["Api-Username"] = self.api_user_name

        for _ in range(self.failsave_retries):
            try:
                resp = requests.get(url=f"{self.base_url}{endpoint}", headers=headers, params=params)
                if resp.status_code not in {200, 202}:
                    raise ValueError(f"Got statuscode {resp.status_code} for {endpoint}. Got {resp}")
                else:
                    break
            except Exception as e:
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
                time.sleep(sleep_time)

        return resp.json()

    def __listdir_failsave(self, path: str):
        try:
            return os.listdir(path)
        except Exception:
            return []

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
