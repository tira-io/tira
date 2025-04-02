import json
import os
import shutil
import tempfile
import uuid
import zipfile
from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, overload

from tira.check_format import _fmt, check_format, log_message

if TYPE_CHECKING:
    import io
    from typing import Any, Dict, Optional, Union

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

    def docker_software() -> "Any":
        # .. todo:: typehint
        pass

    def run_was_already_executed_on_dataset(self, approach, dataset) -> bool:
        # .. todo:: typehint
        pass

    def get_run_output(self, approach, dataset, allow_without_evaluation=False) -> str:
        # .. todo:: typehint
        pass

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

    def evaluate(self, directory: Path, dataset_id: str):
        """Evaluate some predictions made for some dataset on your local machine.

        Args:
            directory (Path): The path to the directory that contains the predictions that you want to evaluate.
            dataset_id (str): The ID of the TIRA dataset on which the directory is to be evaluated.
        """
        from tira.io_utils import load_output_of_directory

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
            print_message(msg, result)
            raise ValueError(msg)
        print_message(f"The predictions in {directory} have the expected format.", _fmt.OK)

        print(dataset_handle)
        dataset_path = self.download_dataset(dataset_handle["default_task"], dataset_id, truth_dataset=True)

        print_message(f"The dataset {dataset_id} is available locally.", _fmt.OK)

        if not self.local_execution.docker_is_installed_failsave():
            msg = "Docker is not installed, I can not run the dockerized evaluator..."
            print_message(msg, _fmt.ERROR)
            raise ValueError(msg)

        print_message("Docker is installed. I can run the dockerized evaluator.", _fmt.OK)
        self.local_execution.ensure_image_available_locally(dataset_handle["evaluator"]["image"])

        print_message(f"The evaluator image {dataset_handle['evaluator']['image']} is available locally.", _fmt.OK)

        with tempfile.TemporaryDirectory() as tmp_dir:
            eval_config = {
                "evaluator_id": "1",
                "evaluator_git_runner_image": dataset_handle["evaluator"]["image"],
                "evaluator_git_runner_command": dataset_handle["evaluator"]["command"],
                "truth_directory": str(Path(dataset_path).absolute().resolve()),
            }
            self.local_execution.evaluate(
                Path(tmp_dir).absolute().resolve(),
                directory.absolute().resolve(),
                allow_network=False,
                evaluate=eval_config,
            )

            preds = None
            try:
                preds = json.dumps(load_output_of_directory(Path(tmp_dir), evaluation=True))
            except:
                msg = "The evaluator failed to produce a valid evaluation..."
                print(msg)
                raise ValueError(msg)

            print_message("The evaluator was successfull.", _fmt.OK)
            print("\n\nResult:\n\t" + preds)

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
    ):
        """Build a tira submission from a git repository.

        Args:
            path (Path): The path to the directory that contains the submission. The path points to the directory used as root for the docker build and must be in a git repository.
            task_id (str): The ID of the TIRA task to which the submissions should be made.
            dataset_id (str, optional): The ID of the TIRA dataset on which the submission is to be tested. If no dataset is passed, the submission will be tested on a small publicly available smoke test dataset for the task.
            user_id (str, optional): The ID of the TIRA team that makes the submission. Is only required if a user has multiple teams.
            docker_file (Path, optional): The Dockerfile to build the submission within the repository. Defaults to None to use path/Dockerfile.
        """

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
        submission_name = directory_in_path.replace("/", "-")
        docker_tag = submission_name + "-" + str(uuid.uuid4())[:5]

        if repo.is_dirty(untracked_files=True):
            if not dry_run:
                raise ValueError("The git repository is not clean.")
        else:
            print_message(f"The git repository {repo.working_tree_dir} is clean.", _fmt.OK)
        print("Build Docker image...")
        zipped_code = self._zip_tracked_files(repo, directory_in_path)

        self.local_execution.build_docker_image(path, docker_tag, docker_file)

        print_message(f"The code is embedded into the docker image {docker_tag}.", _fmt.OK)
        print("Test Docker image...")

        if command is None:
            command = self.local_execution.extract_entrypoint(docker_tag)

        with tempfile.TemporaryDirectory() as tmp_dir:
            self.local_execution.run(
                image=docker_tag,
                command=command,
                input_dir=dataset_path,
                output_dir=tmp_dir,
                allow_network=allow_network,
            )
            result, msg = check_format(Path(tmp_dir), dataset_handle["format"][0])
            if result != _fmt.OK:
                print(msg)
                raise ValueError(msg)
            print_message(f"The docker image produced valid outputs on the dataset {dataset_id}.", _fmt.OK)
            shutil.copy(zipped_code, Path(tmp_dir) / "source-code.zip")

            if not dry_run:
                print("Upload Code Submission image...")
                metadata_uuid = self.upload_run_anonymous(tmp_dir, dataset_id)["uuid"]

                print_message(f"The meta data is uploaded to TIRA.", _fmt.OK)

                print("Push Docker image to TIRA...")
                from tira.tira_run import push_image

                pushed_image = push_image(self, docker_tag, task_id, user_id)

                print_message(f"The Docker image is pushed to TIRA.", _fmt.OK)
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
