import json
import os
import shutil
import tempfile
import uuid
import zipfile
from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, overload

from tira.check_format import _fmt, check_format, lines_if_valid, log_message

if TYPE_CHECKING:
    import io
    from typing import Any, List, Optional, Union

    import pandas as pd

# .. todo:: this file needs further documentation


class TiraClient(ABC):
    def all_datasets(self) -> "pd.DataFrame":
        pass

    def all_softwares(self) -> "pd.DataFrame":
        pass

    def print_overview_of_all_software(self) -> None:
        pass

    def all_evaluators(self) -> "pd.DataFrame":
        pass

    def all_evaluated_appraoches(self) -> "pd.DataFrame":
        pass

    def docker_software(self) -> "Any":
        # .. todo:: typehint
        pass

    def run_was_already_executed_on_dataset(self, approach: str, dataset: str) -> bool:
        raise ValueError("ToDo: Implement")

    def get_run_output(self, approach: str, dataset: str, allow_without_evaluation: bool = False) -> Path:
        raise ValueError("ToDo: Implement")

    def claim_ownership(self, uuid: str, team: str, system: str, description: str, task_id: str) -> Dict:
        raise ValueError("ToDo: Implement")

    def get_dataset(self, dataset: str) -> dict:
        """Get the TIRA representation of an dataset identified by the passed dataset argument.

        Args:
            dataset (Union[str, IrDataset, PyTerrierDataset): The dataset that is either the string id of the dataset in TIRA, the string id of an ir_dataset, the string id of an PyTerrier dataset, or an instantiation of an ir_dataset or an PyTerrier dataset.
        Returns:
            dict: The TIRA representation of the dataset.
        """
        raise ValueError("ToDo: Implement")

    def download_dataset(
        self, task: str, dataset: str, truth_dataset: bool = False, allow_local_dataset: bool = False
    ) -> Path:
        """
        Download the dataset. Set truth_dataset to true to load the truth used for evaluations.
        """
        raise ValueError("ToDo: Implement")

    def json_response(
        self,
        endpoint: str,
        params: "Optional[Union[Dict, List[tuple], bytes]]" = None,
        base_url: "Optional[str]" = None,
        failsave_retries: "Optional[int]" = None,
    ) -> Dict:
        raise ValueError("ToDo: Implement")

    def api_key_is_valid(self) -> bool:
        try:
            role = self.json_response("/api/role")
        except:
            return False

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
            and "csrf" in role
            and role["csrf"]
            and 0 == role["status"]
            and "user_id" in role["context"]
            and role["context"]["user_id"]
            and "role" in role["context"]
            and role["context"]["role"]
            and "guest" != role["context"]["role"]
        )

    def fail_if_api_key_is_invalid(self) -> None:
        if not self.api_key_is_valid():
            role = self.json_response("/api/role")
            raise ValueError("It seems like the api key is invalid. Got: ", role)

    def get_run_execution_or_none(self, approach, dataset, previous_stage_run_id=None) -> "Optional[dict[str, str]]":
        # .. todo:: typehint
        pass

    def docker_registry(self):
        return "registry.webis.de"

    def modify_task(self, task_id: str, to_rename: "dict[str, Any]"):
        # .. todo:: typehint
        pass

    @overload
    def download_run(
        self,
        task,
        dataset,
        software,
        team=None,
        previous_stage=None,
        return_metadata: bool = False,
    ) -> "tuple[pd.DataFrame, str]":
        # .. todo:: typehint
        ...

    @overload
    def download_run(
        self,
        task,
        dataset,
        software,
        team=None,
        previous_stage=None,
        return_metadata: bool = False,
    ) -> "pd.DataFrame":
        # .. todo:: typehint
        ...

    def download_run(
        self,
        task,
        dataset,
        software,
        team=None,
        previous_stage=None,
        return_metadata: bool = False,
    ) -> "Union[pd.DataFrame, tuple[pd.DataFrame, str]]":
        # .. todo:: typehint
        pass

    def create_new_upload(self, task_id: str, vm_id: str) -> "Optional[str]":
        """
        Creates a new upload and returns the newly created id. Returns None on failure.
        """
        pass

    def submit_run(self, task_id: str, vm_id: str, dataset_id: str, upload_id: str, run: "io.IOBase") -> bool:
        """
        Submits the runfile located at `run` for the given task and vm for the given upload id. Returns true on success,
        false  otherwise.
        """
        pass

    def _git_repo(self, path: Path):
        import git

        try:
            # TODO: Replace with call to tirex_tracker.
            return git.Repo(path, search_parent_directories=True)
        except git.exc.InvalidGitRepositoryError as e:
            raise ValueError(f"No git repository found at {path}") from e

    def _zip_tracked_files(self, repo: "git.Repo", directory: str):
        """
        Creates a zip archive containing all tracked files in a given Git repository.

        :param repo: The Git repository.
        :param zip_filename: Name of the output zip file.
        """
        # TODO: Replace with call to tirex_tracker.
        tracked_files = [i.path for i in repo.commit().tree.traverse() if i.path.startswith(f"{directory}/")]
        zip_path = Path(tempfile.TemporaryDirectory().name) / "repo.zip"
        zip_path.parent.mkdir(exist_ok=True, parents=True)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in tracked_files:
                file_path = os.path.join(repo.working_tree_dir, file)
                zipf.write(file_path, arcname=file)
        return zip_path

    def __run_evaluation(
        self,
        image: str,
        command: str,
        predictions: Path,
        truths: Path,
        print_message: Callable,
        ret_dir: Optional[Path] = None,
    ) -> str:
        from tira.io_utils import load_output_of_directory
        from tira.third_party_integrations import temporary_directory

        if not self.local_execution.docker_is_installed_failsave():
            msg = "Docker is not installed, I can not run the dockerized evaluator..."
            log_message(msg, _fmt.ERROR)
            raise ValueError(msg)

        print_message("Docker is installed. I can run the dockerized evaluator.", _fmt.OK)
        self.local_execution.ensure_image_available_locally(image)

        print_message(f"The evaluator image {image} is available locally.", _fmt.OK)

        if ret_dir is None:
            ret_dir = temporary_directory()

        eval_config = {
            "evaluator_id": "1",
            "evaluator_git_runner_image": image,
            "evaluator_git_runner_command": command,
            "truth_directory": str(Path(truths).absolute().resolve()),
        }
        self.local_execution.evaluate(
            Path(ret_dir).absolute().resolve(),
            predictions.absolute().resolve(),
            allow_network=False,
            evaluate=eval_config,
        )

        try:
            return json.dumps(load_output_of_directory(Path(ret_dir), evaluation=True))
        except:
            msg = "The evaluator failed to produce a valid evaluation..."
            print(msg)
            raise ValueError(msg)

    def evaluate(self, directory: Path, dataset_id: str, results_dir: Optional[Path] = None) -> None:
        """Evaluate some predictions made for some dataset on your local machine.

        Args:
            directory (Path): The path to the directory that contains the predictions that you want to evaluate.
            dataset_id (str): The ID of the TIRA dataset on which the directory is to be evaluated.
        """
        all_messages = []

        def print_message(message, level):
            all_messages.append((message, level))
            os.system("cls" if os.name == "nt" else "clear")
            print(f"TIRA Evaluation on '{dataset_id}':")
            for m, l in all_messages:
                log_message(m, l)

        dataset_handle = self.get_dataset(dataset_id)
        if (
            not dataset_handle
            or "mirrors" not in dataset_handle
            or "inputs" not in dataset_handle["mirrors"]
            or "format" not in dataset_handle
            or len(dataset_handle["format"]) == 0
        ):
            raise ValueError("Dataset configuration is invalid: " + str(dataset_handle))

        if (
            "evaluator" not in dataset_handle
            or "image" not in dataset_handle["evaluator"]
            or "command" not in dataset_handle["evaluator"]
        ):
            raise ValueError("Dataset configuration has no evaluator configured: " + str(dataset_handle))

        if not directory or not directory.exists():
            print_message(f"The directory {directory} does not exist.", _fmt.ERROR)
            raise ValueError(f"The directory {directory} does not exist.")

        result, msg = check_format(directory, dataset_handle["format"][0])
        if result != _fmt.OK:
            log_message(msg, result)
            raise ValueError(msg)
        print_message(f"The predictions in {directory} have the expected format.", _fmt.OK)

        dataset_path = self.download_dataset(dataset_handle["default_task"], dataset_id, truth_dataset=True)
        print_message(f"The dataset {dataset_id} is available locally.", _fmt.OK)

        preds = self.__run_evaluation(
            dataset_handle["evaluator"]["image"],
            dataset_handle["evaluator"]["command"],
            directory,
            dataset_path,
            print_message,
            results_dir,
        )

        log_message("The evaluator was successfull.", _fmt.OK)
        print("\n\nResult:\n\t" + preds)

    def __extract_task_and_dataset_id(self, task, dataset):
        if dataset is None and task and len(task.split("/")) == 2:
            task, dataset = task.split("/")
        elif dataset is None:
            task, dataset = None, task

        return task, dataset

    def iter_run_output(self, approach, dataset, format):
        from tira.ir_datasets_util import translate_irds_id_to_tirex

        if dataset is None and os.path.exists(approach):
            output_dir = approach
        else:
            output_dir = self.get_run_output(approach, translate_irds_id_to_tirex(dataset))
        for i in lines_if_valid(Path(output_dir), format):
            yield i

    def iter_dataset(self, task, dataset, truth_dataset, format):
        local_dir = task
        task, dataset = self.__extract_task_and_dataset_id(task, dataset)

        if not self.dataset_exists_in_tira(dataset) and Path(local_dir).exists():
            dataset_dir = local_dir
        else:
            dataset_dir = self.download_dataset(task, dataset, truth_dataset)

        for i in lines_if_valid(Path(dataset_dir), format):
            yield i

    def clone_git_repository(self, repo_url: str):
        from git import Repo

        target_file = Path(self.tira_cache_dir) / "git-repositories" / (repo_url.split("/")[-1])
        if target_file.exists():
            return target_file

        target_file.parent.mkdir(exist_ok=True, parents=True)
        Repo.clone_from(repo_url, target_file)
        return target_file

    def build_docker_image_from_code(
        self, path: Path, print_message, dry_run: bool, docker_file: "Optional[Path]" = None
    ):
        repo = self._git_repo(path)

        try:
            remotes = {remote.name: remote.url for remote in repo.remotes}
        except:
            raise ValueError("No remotes found for the git repository.")

        if len(remotes) == 0:
            raise ValueError("No remotes found for the git repository.")

        try:
            commit = repo.commit().hexsha
        except:
            raise ValueError("No commits in the git repository")

        try:
            active_branch = repo.active_branch.name
        except:
            raise ValueError("No branch in the git repository")

        print_message(f"The code is in a git repository {repo.working_tree_dir}.", _fmt.OK)

        if docker_file is None:
            docker_file = path / "Dockerfile"

        docker_file = Path(docker_file)
        if not docker_file.exists():
            raise ValueError(f"No dockerfile {docker_file} exists.")

        directory_in_path = str(Path(path).absolute()).replace(str(Path(repo.working_tree_dir).absolute()) + "/", "")
        if Path(repo.working_tree_dir).name in directory_in_path:
            directory_in_path = Path(repo.working_tree_dir).name
        submission_name = (
            directory_in_path.replace("/", "-").lower().replace(" ", "-").replace("\n", "").replace("\r", "")
        )
        docker_tag = submission_name + "-" + str(uuid.uuid4())[:5]

        if repo.is_dirty(untracked_files=True):
            if not dry_run:
                log_message(
                    f"The git repository {repo.working_tree_dir} is not clean.\n\tPlease ensure that the repository is clean, i.g., git status reports that everything is committed and pushed.\n\n\tPlease pass --dry-run if you want to test without uploading",
                    _fmt.ERROR,
                )
                raise ValueError("The git repository is not clean.")
        else:
            print_message(f"The git repository {repo.working_tree_dir} is clean.", _fmt.OK)
        print("Build Docker image...")
        zipped_code = self._zip_tracked_files(repo, directory_in_path)

        self.local_execution.build_docker_image(path, docker_tag, docker_file)

        print_message(f"The code is embedded into the docker image {docker_tag}.", _fmt.OK)
        return docker_tag, zipped_code, remotes, commit, active_branch

    def submit_code(
        self,
        path: Path,
        task_id: str,
        command: "Optional[str]" = None,
        dataset_id: "Optional[str]" = None,
        user_id: "Optional[str]" = None,
        docker_file: "Optional[Path]" = None,
        dry_run: "Optional[bool]" = False,
        allow_network: "Optional[bool]" = False,
        mount_hf_model: "Optional[list[str]]" = None,
    ):
        """Build a tira submission from a git repository.

        Args:
            path (Path): The path to the directory that contains the submission. The path points to the directory used as root for the docker build and must be in a git repository.
            task_id (str): The ID of the TIRA task to which the submissions should be made.
            dataset_id (str, optional): The ID of the TIRA dataset on which the submission is to be tested. If no dataset is passed, the submission will be tested on a small publicly available smoke test dataset for the task.
            user_id (str, optional): The ID of the TIRA team that makes the submission. Is only required if a user has multiple teams.
            docker_file (Path, optional): The Dockerfile to build the submission within the repository. Defaults to None to use path/Dockerfile.
        """
        from tira.third_party_integrations import temporary_directory

        all_messages = []

        def print_message(message, level):
            all_messages.append((message, level))
            os.system("cls" if os.name == "nt" else "clear")
            print("TIRA Code Submission:")
            for m, l in all_messages:
                log_message(m, l)

        if not dry_run:
            print(f"Ensure that you are registed for task {task_id}.")
            from tira.tira_run import guess_vm_id_of_user

            user_id = guess_vm_id_of_user(task_id, self, user_id)
            assert user_id
            print_message(f"You are registered and will submit as team {user_id} to task {task_id}.", _fmt.OK)

        if dataset_id is None:
            for k, v in self.datasets(task_id).items():
                if (
                    "is_confidential" not in v
                    or v["is_confidential"]
                    or "is_deprecated" not in v
                    or v["is_deprecated"]
                    or "format" not in v
                    or len(v["format"]) == 0
                ):
                    continue
                candidate = self.get_dataset(f"{task_id}/{k}")
                if not candidate or "mirrors" not in candidate or "inputs" not in candidate["mirrors"]:
                    continue
                dataset_id = k

            if dataset_id is None:
                raise ValueError("foo")

        dataset_handle = self.get_dataset(f"{task_id}/{dataset_id}")
        if (
            not dataset_handle
            or "mirrors" not in dataset_handle
            or "inputs" not in dataset_handle["mirrors"]
            or "format" not in dataset_handle
            or len(dataset_handle["format"]) == 0
        ):
            raise ValueError("foo")

        dataset_path = self.download_dataset(task_id, dataset_id)
        print_message(f"The dataset {dataset_id} is available locally.", _fmt.OK)

        docker_tag, zipped_code, remotes, commit, active_branch = self.build_docker_image_from_code(
            path, print_message, dry_run, docker_file
        )
        print("Test Docker image...")

        hf_models = None
        if mount_hf_model:
            from tira.io_utils import huggingface_model_mounts

            hf_models = huggingface_model_mounts(mount_hf_model)
            hf_models = [k + ":" + v["bind"] + ":" + v["mode"] for k, v in hf_models.items()]
            print(f"The following models from huggingface are mounted: {hf_models}\n\n")

        if command is None:
            command = self.local_execution.extract_entrypoint(docker_tag)

        tmp_dir = temporary_directory()
        self.local_execution.run(
            image=docker_tag,
            command=command,
            input_dir=dataset_path,
            output_dir=tmp_dir,
            allow_network=allow_network,
            additional_volumes=hf_models,
        )

        format_configuration = (
            None if "format_configuration" not in dataset_handle else dataset_handle["format_configuration"]
        )
        result, msg = check_format(Path(tmp_dir), dataset_handle["format"], format_configuration)
        if result != _fmt.OK:
            print(msg)
            raise ValueError(msg)
        print_message(f"The docker image produced valid outputs on the dataset {dataset_id}.", _fmt.OK)
        shutil.copy(zipped_code, Path(tmp_dir) / "source-code.zip")

        if not dry_run:
            print("Upload Code Submission image...")
            metadata_uuid = self.upload_run_anonymous(tmp_dir, dataset_id)["uuid"]

            print_message("The meta data is uploaded to TIRA.", _fmt.OK)

            print("Push Docker image to TIRA...")
            from tira.tira_run import push_image

            pushed_image = push_image(self, docker_tag, task_id, user_id)

            print_message("The Docker image is pushed to TIRA.", _fmt.OK)
            print("Configure code submission in TIRA...")
            upload = self.add_docker_software(
                pushed_image,
                command,
                user_id,
                task_id,
                None,
                dict(os.environ),
                source_code_remotes=remotes,
                source_code_commit=commit,
                source_code_active_branch=active_branch,
                try_run_metadata_uuid=metadata_uuid,
                mount_hf_model=mount_hf_model,
            )
            print_message(f"The code submission is uploaded to TIRA.", _fmt.OK)
            print("\nResult:")
            log_message(
                f"Your code submission is available in TIRA as {upload['display_name']}.",
                _fmt.OK,
            )

        return {
            "code": zipped_code,
            "remotes": remotes,
            "commit": commit,
            "active_branch": active_branch,
            "image": docker_tag,
        }

    def submit_dataset(
        self,
        path: Path,
        task: str,
        split: str,
        dry_run: bool,
        system_inputs: str = "inputs",
        truths: str = "truths",
        skip_baseline: bool = False,
    ):
        from shutil import copy

        from tira.io_utils import TqdmUploadFile, verify_tira_installation, zip_dir
        from tira.third_party_integrations import temporary_directory

        all_messages = []

        def print_message(message: str, level: _fmt) -> None:
            all_messages.append((message, level))
            os.system("cls" if os.name == "nt" else "clear")
            print("TIRA Dataset Submission:")
            for m, l in all_messages:
                log_message(m, l)

        if not dry_run:
            result = verify_tira_installation()
            if result != _fmt.OK:
                msg = "Your tira installation is not valid. Please run: tira-cli verify-installation"
                print_message(msg, _fmt.ERROR)
                return None

        if path is None or not path.exists() or not path.is_dir():
            msg = f"The path {path} does not exist. I can not continue"
            log_message(msg, _fmt.ERROR)
            return None

        print_message("Your tira installation is valid.", _fmt.OK)

        try:
            from datasets import load_dataset, load_dataset_builder
        except ImportError as e:
            msg = "I could not import the datasets library to load the dataset. Please install the datasets library (e.g., via pip3 install datasets)."
            log_message(msg, _fmt.ERROR)
            return None

        try:
            from huggingface_hub import DatasetCard
        except ImportError as e:
            msg = "I could not import the huggingface_hub library to load the DatasetCard. Please install the huggingface_hub library (e.g., via pip3 install huggingface_hub)."
            log_message(msg, _fmt.ERROR)
            return None

        if str(path).strip() in (".", ".."):
            print_message(
                f"Please do not pass '.' or '..' as argument for --path as the datasets library uses the name of the directory.",
                _fmt.ERROR,
            )
            return None

        if not (path / "README.md").is_file():
            print_message(
                f"I expect a huggingface dataset configuration in a file {path / 'README.md'}.",
                _fmt.ERROR,
            )
            return None

        tira_configs = DatasetCard.load(str(path / "README.md")).data["tira_configs"]
        resolve_inputs_to = tira_configs.get("resolve_inputs_to", None)
        input_format = tira_configs["input_format"]["name"]
        input_config = tira_configs["input_format"].get("config", {})
        git_url, subdir = tira_configs["baseline"]["link"].replace("/tree/master/", "/tree/main/").split("/tree/main/")
        baseline_command = tira_configs["baseline"]["command"]
        baseline_format = tira_configs["baseline"]["format"]["name"]
        baseline_config = tira_configs["baseline"]["format"].get("config", {})
        if "measures" in tira_configs["evaluator"]:
            eval_image, eval_command, eval_measures = None, None, tira_configs["evaluator"]["measures"]
        else:
            eval_image = tira_configs["evaluator"]["image"]
            eval_command = tira_configs["evaluator"]["command"]
            eval_measures = None
        resolve_truths_to = tira_configs.get("resolve_truths_to", None)

        print_message(f"The configuration of the dataset {path} is valid.", _fmt.OK)

        truth_format = tira_configs["truth_format"]["name"]
        truth_config = tira_configs["truth_format"].get("config", {})

        baseline_format = baseline_format if isinstance(baseline_format, List) else [baseline_format]
        truth_format = truth_format if isinstance(truth_format, List) else [truth_format]

        dataset_system_inputs = load_dataset_builder(str(path), system_inputs)
        dataset_truths = load_dataset_builder(str(path), truths)

        inputs_dir = temporary_directory()
        truth_dir = temporary_directory()

        if split not in dataset_system_inputs.config.data_files:
            msg = (
                f"Split {split} is not available. Possible are: {list(dataset_system_inputs.config.data_files.keys())}"
            )
            log_message(msg, _fmt.ERROR)
            return None

        for data_file in dataset_system_inputs.config.data_files[split]:
            relative_data_file = Path(data_file).relative_to(
                Path(dataset_system_inputs.base_path).absolute() / resolve_inputs_to
            )
            target_file = inputs_dir / relative_data_file
            target_file.parent.mkdir(exist_ok=True, parents=True)
            copy(data_file, target_file)

        for data_file in dataset_truths.config.data_files[split]:
            relative_data_file = Path(data_file).relative_to(
                Path(dataset_truths.base_path).absolute() / resolve_truths_to
            )
            target_file = truth_dir / relative_data_file
            target_file.parent.mkdir(exist_ok=True, parents=True)
            copy(data_file, target_file)

        l, m = check_format(inputs_dir, input_format, input_config)
        if l != _fmt.OK:
            log_message(m, l)
            return None

        print_message("The system inputs are valid.", _fmt.OK)

        l, m = check_format(truth_dir, truth_format, truth_config)
        if l != _fmt.OK:
            log_message(m, l)
            return None

        print_message("The truth data is valid.", _fmt.OK)

        if not skip_baseline:
            git_repo_local = self.clone_git_repository(git_url)
            print_message(f"Repository for the baseline is cloned from {git_url}.", _fmt.OK)

            docker_tag, _, _, _, _ = self.build_docker_image_from_code(
                git_repo_local / Path(subdir), log_message, False
            )

            print_message(f"The baseline {subdir} is embedded in a Docker image.", _fmt.OK)

            if baseline_command is None:
                baseline_command = self.local_execution.extract_entrypoint(docker_tag)

            baseline_output = temporary_directory()
            self.local_execution.run(
                image=docker_tag, command=baseline_command, input_dir=inputs_dir, output_dir=baseline_output
            )

            l, m = check_format(baseline_output, baseline_format, baseline_config)
            if l != _fmt.OK:
                log_message(f"The outputs of the baseline are at {baseline_output} and not valid: {m}", l)
                return None

            if eval_image is not None and eval_command is not None:
                print_message(f"The baseline produced valid outputs at {baseline_output}.", _fmt.OK)
                preds = self.__run_evaluation(eval_image, eval_command, baseline_output, truth_dir, log_message)

                print_message(f"The evaluation of the baseline produced valid outputs: {preds}.", _fmt.OK)
            else:
                from tira.evaluators import evaluate

                eval_config: Dict = {
                    "measures": eval_measures,
                    "run_format": baseline_format,
                    "truth_format": truth_format,
                }
                preds = evaluate(
                    baseline_output,
                    truth_dir,
                    eval_config,
                )
                print_message(f"The evaluation of the baseline produced valid outputs: {preds}.", _fmt.OK)

        ret = {}

        ret["inputs_dir"] = inputs_dir
        ret["truths_dir"] = truth_dir
        ret["inputs_zip"] = zip_dir(inputs_dir)
        ret["truths_zip"] = zip_dir(truth_dir)

        if not dry_run:
            headers = self.authentication_headers()
            headers["Accept"] = "application/json"
            headers["Content-Type"] = "application/json"
            self.fail_if_api_key_is_invalid()

            csrf_token = self.get_csrf_token()
            headers["Cookie"] = f"csrftoken={csrf_token}" + (
                "" if "Cookie" not in headers else "; " + headers["Cookie"]
            )
            headers["x-csrftoken"] = csrf_token
            dataset_name = path.name
            dataset_id = dataset_name.lower().replace("/", "-").replace(" ", "-").replace("_", "-")
            url = f"{self.base_url}/tira-admin/add-dataset/{task}"
            content = {
                "csrfmiddlewaretoken": csrf_token,
                "dataset_id": dataset_id,
                "name": dataset_name,
                "task": task,
                "type": "training" if ("train" in split.lower()) else "test",
                "upload_name": "predictions.jsonl",
                "is_confidential": True,
                "irds_docker_image": "",
                "irds_import_command": "",
                "irds_import_truth_command": "",
                "git_runner_image": eval_image if eval_image else "ubuntu:18.04",
                "git_runner_command": eval_command if eval_command else "echo 'this is no real evaluator'",
                "is_git_runner": True,
                "use_existing_repository": False,
                "working_directory": "obsolete",
                "command": "obsolete",
                "publish": False,
                "evaluator_command": "obsolete",
                "evaluator_image": "obsolete",
                "evaluator_working_directory": "obsolete",
                "description": "todo",
                "chatnoir_id": "",
                "ir_datasets_id": "",
                "format": baseline_format,
                "format_configuration": json.dumps(baseline_config),
                "truth_format": truth_format,
                "truth_format_configuration": json.dumps(truth_config),
            }

            if eval_measures is not None:
                content["trusted_measures"] = eval_measures

            import requests

            resp = requests.post(url, headers=headers, json=content, verify=self.verify)
            resp_content = resp.content.decode("utf8")
            try:
                dataset_id = json.loads(resp_content)["context"]["dataset_id"]
            except:
                print(resp_content)
                raise ValueError(f"Failure. Got response {resp.status_code} from server:\n\n{resp_content}")
            print_message(f"Configuration for dataset {dataset_id} is uploaded to TIRA.", _fmt.OK)

            def post_data(type: str) -> None:
                tqdm_zip_file = TqdmUploadFile(ret[f"{type}s_zip"], f"Upload {type}s to TIRA")

                headers = self.authentication_headers()
                headers["Accept"] = "application/json"
                headers["Cookie"] = f"csrftoken={csrf_token}" + (
                    "" if "Cookie" not in headers else "; " + headers["Cookie"]
                )
                headers["x-csrftoken"] = csrf_token
                files = {"file": (os.path.basename(ret[f"{type}s_zip"]), tqdm_zip_file)}

                resp = requests.post(
                    url=f"{self.base_url}/tira-admin/upload-dataset/{task}/{dataset_id}/{type}",
                    files=files,
                    headers=headers,
                    verify=self.verify,
                )

                resp_content = resp.content.decode("utf8")
                try:
                    resp_parsed = json.loads(resp_content)
                except:
                    print(resp_content)
                    raise ValueError(f"Failure. Got response {resp.status_code} from server:\n\n{resp_content}")
                if "status" not in resp_parsed or "message" not in resp_parsed or resp_parsed["status"] != 0:
                    log_message(f"Could not upload system {type}s: {resp_content}", _fmt.ERROR)
                    return

                print_message(f"{type}s are uploaded to TIRA: {resp_parsed['message']}", _fmt.OK)

            post_data("input")
            post_data("truth")

        return ret

    def __extract_dataset_identifier(self, dataset: any):
        """Extract the dataset identifier from a passed object.

        Args:
            dataset (any): Some representation of dataset.

        Returns:
            Optional[dict]: The dataset identifier if available.
        """
        if hasattr(dataset, "irds_ref"):
            return self.__extract_dataset_identifier(dataset.irds_ref())
        if hasattr(dataset, "dataset_id"):
            return dataset.dataset_id()
        return dataset

    def __matching_dataset(self, datasets, dataset_identifier) -> "Optional[dict]":
        """Find the dataset identified by the passed dataset_identifier in all passed datasets.

        Args:
            datasets (List[dict]): TIRA representations of datasets.
            dataset_identifier (_type_): identifier of the dataset to be found.

        Returns:
            Optional[dict]: The TIRA representation of the dataset if found in the datasets.
        """
        datasets = [i for i in datasets if "id" in i and len(i["id"]) > 2]

        for dataset in datasets:
            if dataset_identifier and dataset["id"] == dataset_identifier:
                return dataset

        if len(dataset_identifier.split("/")) == 2:
            task_identifier, dataset_in_task = dataset_identifier.split("/")

            for dataset in datasets:
                if "default_task" not in dataset or not dataset["default_task"]:
                    continue

                if not task_identifier or not dataset_in_task:
                    continue

                if task_identifier == dataset["default_task"] and dataset_in_task == dataset["id"]:
                    return dataset

                if task_identifier == dataset["default_task"] and dataset_in_task == dataset["display_name"]:
                    return dataset

        for dataset in datasets:
            if "ir_datasets_id" not in dataset or not dataset["ir_datasets_id"] or len(dataset["ir_datasets_id"]) < 3:
                continue

            if dataset_identifier and dataset_identifier == dataset["ir_datasets_id"]:
                return dataset

        matches = []
        for dataset in datasets:
            if "default_task" not in dataset or not dataset["default_task"]:
                continue

            if dataset_identifier and dataset_identifier == dataset["display_name"]:
                matches.append(dataset)

        if len(matches) == 1:
            return matches[0]
