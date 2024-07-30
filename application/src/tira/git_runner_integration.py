import json
import logging
import os
import shutil
import stat
import string
import tempfile
from copy import deepcopy
from datetime import datetime as dt
from glob import glob
from itertools import chain
from pathlib import Path

import gitlab
import markdown
import requests
from django.conf import settings
from django.template.loader import render_to_string
from git import Repo
from github import Github
from slugify import slugify
from tqdm import tqdm

from tira.grpc_client import new_transaction
from tira.model import EvaluationLog, TransactionLog

logger = logging.getLogger("tira")


def normalize_file(file_content, tira_user_name, task_id):
    default_datasets = {
        "webpage-classification": "webpage-classification/tiny-sample-20231023-training",
        "ir-lab-jena-leipzig-wise-2023": "workshop-on-open-web-search/retrieval-20231027-training",
        "ir-lab-jena-leipzig-sose-2023": "workshop-on-open-web-search/retrieval-20231027-training",
        "workshop-on-open-web-search": "workshop-on-open-web-search/retrieval-20231027-training",
        "ir-benchmarks": "workshop-on-open-web-search/retrieval-20231027-training",
    }

    return (
        file_content.replace("TIRA_USER_FOR_AUTOMATIC_REPLACEMENT", tira_user_name)
        .replace("TIRA_TASK_ID_FOR_AUTOMATIC_REPLACEMENT", task_id)
        .replace("TIRA_DATASET_FOR_AUTOMATIC_REPLACEMENT", default_datasets.get(task_id, "<TODO-ADD-DATASET>"))
    )


def convert_size(size_bytes):
    import math

    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    return f"{s} {size_name[i]}"


def write_to_file(file_name, content):
    open(file_name, "w").write(content)


class GitRunner:
    def create_task_repository(self, task_id):
        """
        Create the repository with the name "task_id" in the organization.
        An organization has task repositories (execute and evaluate submissions)
        and multiple user repositories (hosts docker images).
        Does nothing, if the repository already exists.

        Parameters
        ----------
        task_id: str
        Name of the task repository
        """
        logger.info(f"Creating task repository for task {task_id} ...")
        repo = self.existing_repository(task_id)
        if repo:
            return int(repo.id)

        project = self._create_task_repository_on_gitHoster(task_id)

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Repo.init(tmp_dir)
            write_to_file(str(tmp_dir) + "/" + self.template_ci_file_name(), self.template_ci())
            write_to_file(str(tmp_dir) + "/README.md", self.template_readme(task_id))
            write_to_file(str(tmp_dir) + "/tira", self.template_tira_cmd_script(project))
            os.chmod(str(tmp_dir) + "/tira", os.stat(str(tmp_dir) + "/tira").st_mode | stat.S_IEXEC)

            repo.create_remote("origin", self.repo_url(project.id))
            self.ensure_branch_is_main(repo)
            repo.index.add(["README.md", self.template_ci_file_name(), "tira"])
            repo.index.commit("Initial commit")
            repo.remote().push(self.user_repository_branch, o="ci.skip")

        logger.info(f"Created task repository for task {task_id} with new id {project.id}")
        return project.id

    def template_ci_file_name(self):
        raise ValueError("ToDo: Implement.")

    def _create_task_repository_on_gitHoster(self, task_id):
        raise ValueError("ToDo: Implement.")

    def repo_url(self, repo_id):
        raise ValueError("ToDo: Implement.")

    def ensure_branch_is_main(self, repo):
        try:
            # for some git versions we need to manually switch, may fail if the branch is already correct
            repo.git.checkout("-b", self.user_repository_branch)
        except Exception:
            pass

    def clone_repository_and_create_new_branch(self, repo_url, branch_name, directory):
        repo = Repo.clone_from(repo_url, directory, branch="main")
        repo.head.reference = repo.create_head(branch_name)

        return repo

    def dict_to_key_value_file(self, d):
        return "\n".join([(k + "=" + str(v)).strip() for (k, v) in d.items()])

    def write_metadata_for_ci_job_to_repository(
        self,
        tmp_dir,
        task_id,
        transaction_id,
        dataset_id,
        vm_id,
        run_id,
        identifier,
        git_runner_image,
        git_runner_command,
        evaluator_id,
        user_image_to_execute,
        user_command_to_execute,
        tira_software_id,
        resources,
        input_run,
        mount_hf_model,
        workdir_in_user_image,
    ):
        job_dir = Path(tmp_dir) / dataset_id / vm_id / run_id
        job_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            # The pipeline executed first a pseudo software so the following three values are
            # only dummy values so that the software runs successful.
            "TIRA_IMAGE_TO_EXECUTE": user_image_to_execute,
            "TIRA_VM_ID": vm_id,
            "TIRA_COMMAND_TO_EXECUTE": user_command_to_execute,
            "TIRA_SOFTWARE_ID": tira_software_id,
            "TIRA_DATASET_ID": dataset_id,
            "TIRA_RUN_ID": run_id,
            "TIRA_CPU_COUNT": str(settings.GIT_CI_AVAILABLE_RESOURCES[resources]["cores"]),
            "TIRA_MEMORY_IN_GIBIBYTE": str(settings.GIT_CI_AVAILABLE_RESOURCES[resources]["ram"]),
            "TIRA_GPU": str(settings.GIT_CI_AVAILABLE_RESOURCES[resources]["gpu"]),
            "TIRA_DATA": str(settings.GIT_CI_AVAILABLE_RESOURCES[resources]["data"]),
            "TIRA_DATASET_TYPE": "training" if "training" in dataset_id else "test",
            # The actual important stuff for the evaluator:
            "TIRA_TASK_ID": task_id,
            "TIRA_EVALUATOR_TRANSACTION_ID": transaction_id,
            "TIRA_GIT_ID": identifier,
            "TIRA_EVALUATION_IMAGE_TO_EXECUTE": git_runner_image,
            "TIRA_EVALUATION_COMMAND_TO_EXECUTE": git_runner_command,
            "TIRA_EVALUATION_SOFTWARE_ID": evaluator_id,
        }

        if mount_hf_model and isinstance(mount_hf_model, str) and len(mount_hf_model.strip()) > 0:
            metadata["TIRA_MOUNT_HF_MODEL"] = mount_hf_model.strip()

        if workdir_in_user_image and isinstance(workdir_in_user_image, str) and len(workdir_in_user_image.strip()) > 0:
            metadata["TIRA_WORKDIR"] = workdir_in_user_image.strip()

        if input_run and not isinstance(input_run, list):
            metadata["TIRA_INPUT_RUN_DATASET_ID"] = input_run["dataset_id"]
            metadata["TIRA_INPUT_RUN_VM_ID"] = input_run["vm_id"]
            metadata["TIRA_INPUT_RUN_RUN_ID"] = input_run["run_id"]
            if input_run.get("replace_original_dataset", False):
                metadata["TIRA_INPUT_RUN_REPLACES_ORIGINAL_DATASET"] = "true"
        elif input_run and isinstance(input_run, list) and len(input_run) > 0:
            metadata["TIRA_INPUT_RUN_DATASET_IDS"] = json.dumps([i["dataset_id"] for i in input_run])
            metadata["TIRA_INPUT_RUN_VM_IDS"] = json.dumps([i["vm_id"] for i in input_run])
            metadata["TIRA_INPUT_RUN_RUN_IDS"] = json.dumps([i["run_id"] for i in input_run])

        open(job_dir / "job-to-execute.txt", "w").write(self.dict_to_key_value_file(metadata))

    def create_user_repository(self, user_name):
        """
        Create the repository for user with the name "user_name" in the organization.
        An organization has task repositories (execute and evaluate submissions)
        and multiple user repositories (hosts docker images).
        Creates an authentication token, that allows the user to upload images to this repository.
        Does nothing, if the repository already exists.

        Parameters
        ----------
        user_name: str
        Name of the user.  The created repository has the name tira-user-${user_name}
        """
        repo = "tira-user-" + user_name
        existing_repo = self.existing_repository(repo)
        if existing_repo:
            return existing_repo.id

        project = self._create_task_repository_on_gitHoster(repo)

        token = self._create_access_token_gitHoster(project, repo)

        self.initialize_user_repository(project.id, repo, token.token)

        return project.id

    def initialize_user_repository(self, git_repository_id, repo_name, token):
        project_readme = render_to_string(
            "tira/git_user_repository_readme.md",
            context={
                "user_name": repo_name.replace("tira-user-", ""),
                "repo_name": repo_name,
                "token": token,
                "image_prefix": self.image_registry_prefix + "/" + repo_name + "/",
            },
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Repo.init(tmp_dir)
            write_to_file(str(tmp_dir) + "/README.md", project_readme)

            repo.create_remote("origin", self.repo_url(git_repository_id))
            self.ensure_branch_is_main(repo)
            repo.index.add(["README.md"])
            repo.index.commit("Initial commit")
            repo.remote().push(self.user_repository_branch)

    def docker_images_in_user_repository(self, user_name, cache=None, force_cache_refresh=False):
        """TODO  Dane
        List all docker images uploaded by the user with the name "user_name" to his user repository

        Parameters
        ----------
        user_name: str
        Name of the user.

        Return
        ----------
        images: Iterable[str]
        The images uploaded by the user.
        """
        cache_key = "docker-images-in-user-repository-tira-user-" + user_name
        if cache:
            ret = cache.get(cache_key)
            if ret is not None and not force_cache_refresh:
                return ret

        ret = []
        repo = self.existing_repository("tira-user-" + user_name)
        if not repo:
            self.create_user_repository(user_name)
            return ret

        covered_images = set()
        for registry_repository in repo.repositories.list():
            for registry in registry_repository.manager.list():
                for image in registry.tags.list(get_all=True):
                    if image.location in covered_images:
                        continue
                    covered_images.add(image.location)
                    image_manifest = self.get_manifest_of_docker_image_image_repository(
                        image.location.split(":")[0], image.location.split(":")[1], cache, force_cache_refresh
                    )

                    ret += [
                        {
                            "image": image.location,
                            "architecture": image_manifest["architecture"],
                            "created": image_manifest["created"].split(".")[0],
                            "size": image_manifest["size"],
                            "raw_size": image_manifest["raw_size"],
                            "digest": image_manifest["digest"],
                        }
                    ]

        ret = sorted(list(ret), key=lambda i: i["image"])

        if cache:
            logger.info(f"Cache refreshed for key {cache_key} ...")
            cache.set(cache_key, ret)

        return ret

    def help_on_uploading_docker_image(self, user_name, cache=None, force_cache_refresh=False):
        """TODO
        Each user repository has a readme.md , that contains instructions on
        how to upload images to the repository.
        This method extracts those instructions from the readme and returns them.

        Parameters
        ----------
        user_name: str
        Name of the user.

        Return
        ----------
        help: [str]
        The personalized instructions on how to upload images
        to be shown in the webinterface.
        """
        cache_key = "help-on-uploading-docker-image-tira-user-" + user_name
        if cache:
            ret = cache.get(cache_key)
            if ret is not None and not force_cache_refresh:
                return ret

        repo = self.existing_repository("tira-user-" + user_name)
        if not repo:
            self.create_user_repository(user_name)
            return self.help_on_uploading_docker_image(user_name, cache)

        # Hacky at the moment
        ret = repo.files.get("README.md", ref="main").decode().decode("UTF-8").split("## Create an docker image")[1]
        ret = "## Create an docker image\n\n" + ret

        ret = markdown.markdown(ret)

        if cache:
            logger.info(f"Cache refreshed for key {cache_key} ...")
            cache.set(cache_key, ret)

        return ret

    def add_new_tag_to_docker_image_repository(self, repository_name, existing_tag, new_tag):
        """TODO Niklas
        The repository with the name "repository_name" contains an docker image
        with the tag "existing_tag".
        This method adds the tag "new_tag" to the image with the tag "existing_tag".

        Parameters
        ----------
        repository_name: str
        Name of the repository with an docker image with the tag "existing_tag".

        existing_tag: str
        Tag of the docker image.

        new_tag: str
        The to be added tag of the docker image.
        """
        raise ValueError("ToDo: Implement.")

    def extract_configuration_of_finished_job(self, git_repository_id, dataset_id, vm_id, run_id):
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.clone_repository_and_create_new_branch(self.repo_url(git_repository_id), "dummy-br", tmp_dir)
            f = glob(tmp_dir + "/" + dataset_id + "/" + vm_id + "/" + run_id + "/job-executed-on-*.txt")

            if len(f) != 1:
                return None

            return open(f[0]).read()

    def all_user_repositories(self):
        """
        Lists all user repositories in the organization.

        Return
        ----------
        user_repositories: Iterable[str]
        List of all user repositories in the organization.
        """
        raise ValueError("ToDo: Implement.")

    def run_and_evaluate_user_software(
        self,
        task_id,
        dataset_id,
        user_name,
        run_id,
        user_software_id,
        user_docker_image,
        user_command,
        git_repository_id,
        evaluator_id,
        evaluator_software_id,
        evaluator_docker_image,
        evaluator_command,
    ):
        """TODO
        Execute the specified software (docker image and a command)
        on a dataset and evaluate the output.

        Erzeugt neue Datei und commited diese als Trigger für Workflow/CI.

        Parameters
        ----------
        task_id: str
        Name of the task repository.

        dataset_id: str
        Dataset on which the software is to be executed.

        user_name: str
        Name of the user. The repository of the user has the name tira-user-${user_name}.

        run_id: str
        Identifier of the resulting run.

        user_software_id: str
        ID of the to be executed software.
        (identifies docker images and command)

        user_docker_image: str
        The to be execued docker image.

        user_command: str
        The to be executed command in "user_docker_image".

        git_repository_id: str
        Identifier of the task repository
        (gitlab: int; github: ???)

        evaluator_id: str
        Identifier of the resulting evaluation.

        evaluator_software_id: str
        ID of the to be executed evaluation software.
        (identifies the evaluation docker images and evaluation command)


        evaluator_docker_image: str
        The to be execued docker image used for evaluation.

        evaluator_command: str
        The to be executed evaluation command in "evaluation_docker_image".

        Return
        ----------
        transaction_id: str
        ID of the running transaction.
        """
        raise ValueError("ToDo: Implement.")

    def stop_job_and_clean_up(self, git_repository_id, user_name, run_id):
        """
        All runs that are currently running, pending, or failed
        life in a dedicated branch.
        Every successfully (without errors/failures and with evaluation)
        executed software is merged into the main branch.
        This method stops a potentially running pipeline identified by the run_id
        of the user "user_id" and deletes the branch.

        Parameters
        ----------
        git_repository_id: str
        Identifier of the task repository.
        (gitlab: int; github: int)

        user_name: str
        Name of the user. The repository of the user has the name "tira-user-${user_name}".

        run_id: str
        Identifier of the to be stopped run.

        Return
        ----------
        -
        """
        raise ValueError("ToDo: Implement.")

    def yield_all_running_pipelines(self, git_repository_id):
        """TODO
        Yield all pipelines/workflows that are currently running, pending, or failed.


        Parameters
        ----------
        git_repository_id: str
        Identifier of the task repository.
        (gitlab: int; github: int)

        Return
        ----------
        jobs: Iteratable[dict]
        all pipelines/workflows that are currently running, pending, or failed.
        Each entry has the following fields:
            'run_id',
            'execution',
            'stdOutput',
            'started_at',
            'pipeline_name',
            'job_config',
            'pipeline'
        """
        raise ValueError("ToDo: Implement.")

    def archive_software(self, working_directory, software_definition, download_images, persist_images, upload_images):
        from tira.util import docker_image_details, run_cmd

        image = (
            software_definition["TIRA_EVALUATION_IMAGE_TO_EXECUTE"]
            if "TIRA_EVALUATION_IMAGE_TO_EXECUTE" in software_definition
            else software_definition["TIRA_IMAGE_TO_EXECUTE"]
        )
        dockerhub_image = (
            software_definition["TIRA_IMAGE_TO_EXECUTE_IN_DOCKERHUB"]
            if "TIRA_IMAGE_TO_EXECUTE_IN_DOCKERHUB" in software_definition
            else None
        )

        if download_images:
            print(f"Run docker pull {image}.")
            run_cmd(["podman", "pull", image])

        description = docker_image_details(image)

        Path(working_directory + "/docker-softwares").mkdir(parents=True, exist_ok=True)
        image_name = working_directory + "/docker-softwares/" + description["image_id"] + ".tar"

        if persist_images and not os.path.isfile(image_name):
            print(f"Run image save {image} -o {image_name}.")
            run_cmd(["podman", "image", "save", image, "-o", image_name])

        if upload_images and dockerhub_image:
            run_cmd(["podman", "tag", image, dockerhub_image])
            print(f"Run image push {dockerhub_image}.")
            run_cmd(["podman", "push", dockerhub_image])

        description["local_image"] = image_name
        software_definition["image_details"] = description

        return software_definition

    def archive_all_softwares(self, working_directory, download_images=True, persist_images=True, upload_images=True):
        existing_software = [json.loads(i) for i in open(working_directory + "/.tira/submitted-software.jsonl", "r")]
        existing_evaluators = [json.loads(i) for i in open(working_directory + "/.tira/evaluators.jsonl", "r")]

        software, evaluators = [], []

        for s in tqdm(existing_software, "Software"):
            software += [
                json.dumps(self.archive_software(working_directory, s, download_images, persist_images, upload_images))
            ]

        for e in tqdm(existing_evaluators, "Evaluators"):
            evaluators += [
                json.dumps(self.archive_software(working_directory, e, download_images, persist_images, upload_images))
            ]

        open((Path(working_directory) / ".tira" / "submitted-software.jsonl").absolute(), "w").write(
            "\n".join(software)
        )
        open((Path(working_directory) / ".tira" / "evaluators.jsonl").absolute(), "w").write("\n".join(evaluators))

    def archive_repository(
        self,
        repo_name,
        working_directory,
        copy_runs=True,
        download_images=True,
        persist_images=True,
        upload_images=True,
        persist_datasets=True,
    ):
        from django.template.loader import render_to_string

        from tira.tira_model import get_dataset, get_docker_software, get_docker_softwares_with_runs

        softwares = set()
        evaluations = set()
        datasets = {}

        if not os.path.isdir(working_directory + "/.git"):
            repo = self.existing_repository(repo_name)
            print(f"Clone repository {repo.name}. Working in {working_directory}")
            repo = Repo.clone_from(self.repo_url(repo.id), working_directory, branch="main")
        else:
            print(f"Use existing repo in {working_directory}.")
            self.archive_all_softwares(working_directory, download_images, persist_images, upload_images)
            return

        Path(working_directory + "/docker-softwares").mkdir(parents=True, exist_ok=True)

        print("Exporting docker images...")
        downloaded_images = set()
        for job_file in tqdm(
            sorted(list(glob(working_directory + "/*/*/*/job-executed-on*.txt"))), "Export Docker Images"
        ):
            job = [i.split("=", 1) for i in open(job_file, "r")]
            job = {k.strip(): v.strip() for k, v in job}
            image = job["TIRA_IMAGE_TO_EXECUTE"].strip()

            if self.image_registry_prefix.lower() not in image.lower():
                continue

            datasets[job["TIRA_DATASET_ID"]] = get_dataset(job["TIRA_DATASET_ID"])

            try:
                software_metadata = get_docker_software(int(job["TIRA_SOFTWARE_ID"].replace("docker-software-", "")))
                if copy_runs:
                    runs = get_docker_softwares_with_runs(job["TIRA_TASK_ID"], job["TIRA_VM_ID"])
            except Exception:
                continue

            if copy_runs:

                runs = [
                    i
                    for i in runs
                    if int(i["docker_software_id"]) == (int(job["TIRA_SOFTWARE_ID"].replace("docker-software-", "")))
                ]
                runs = list(chain(*[i["runs"] for i in runs]))
                runs = [
                    i for i in runs if (i["input_run_id"] == job["TIRA_RUN_ID"] or i["run_id"] == job["TIRA_RUN_ID"])
                ]

                for run in runs:
                    result_out_dir = Path(job_file.split("/job-executed-on")[0]) / (
                        "evaluation" if run["is_evaluation"] else "run"
                    )
                    result_out_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(
                        Path(settings.TIRA_ROOT)
                        / "data"
                        / "runs"
                        / job["TIRA_DATASET_ID"]
                        / job["TIRA_VM_ID"]
                        / run["run_id"],
                        result_out_dir / run["run_id"],
                    )

            image_name = (slugify(image) + ".tar").replace("/", "-")

            dockerhub_image = (
                f'docker.io/webis/{job["TIRA_TASK_ID"]}-submissions:'
                + (image_name.split("-tira-user-")[1]).replace(".tar", "").strip()
            )

            downloaded_images.add(image)
            softwares.add(
                json.dumps(
                    {
                        "TIRA_IMAGE_TO_EXECUTE": image,
                        "TIRA_IMAGE_TO_EXECUTE_IN_DOCKERHUB": dockerhub_image,
                        "TIRA_VM_ID": job["TIRA_VM_ID"],
                        "TIRA_COMMAND_TO_EXECUTE": job["TIRA_COMMAND_TO_EXECUTE"],
                        "TIRA_TASK_ID": job["TIRA_TASK_ID"],
                        "TIRA_SOFTWARE_ID": job["TIRA_SOFTWARE_ID"],
                        "TIRA_SOFTWARE_NAME": software_metadata["display_name"],
                        "TIRA_IDS_OF_PREVIOUS_STAGES": (
                            []
                            if "input_docker_software_id" not in software_metadata
                            or not software_metadata["input_docker_software_id"]
                            else [software_metadata["input_docker_software_id"]]
                        ),
                    }
                )
            )

            evaluations.add(
                json.dumps(
                    {
                        "TIRA_DATASET_ID": job["TIRA_DATASET_ID"].strip(),
                        "TIRA_EVALUATION_IMAGE_TO_EXECUTE": job["TIRA_EVALUATION_IMAGE_TO_EXECUTE"].strip(),
                        "TIRA_EVALUATION_COMMAND_TO_EXECUTE": job["TIRA_EVALUATION_COMMAND_TO_EXECUTE"].strip(),
                    }
                )
            )

        (Path(working_directory) / ".tira").mkdir(parents=True, exist_ok=True)
        open((Path(working_directory) / ".tira" / "submitted-software.jsonl").absolute(), "w").write(
            "\n".join(softwares)
        )
        open((Path(working_directory) / ".tira" / "evaluators.jsonl").absolute(), "w").write("\n".join(evaluations))
        open((Path(working_directory) / "tira.py").absolute(), "w").write(
            render_to_string("tira/tira_git_cmd.py", context={})
        )
        open((Path(working_directory) / "requirements.txt").absolute(), "w").write("docker==5.0.3\npandas\njupyterlab")
        open((Path(working_directory) / "Makefile").absolute(), "w").write(
            render_to_string("tira/tira_git_makefile", context={})
        )
        open((Path(working_directory) / "Tutorial.ipynb").absolute(), "w").write(
            render_to_string("tira/tira_git_tutorial.ipynb", context={})
        )
        # open((Path(working_directory) / 'README.md').absolute(), 'a+').write(render_to_string('tira/tira_git_cmd.py', context={}))

        if persist_datasets:
            logger.info("Archive datasets")
            for dataset_name, dataset_definition in tqdm(datasets.items(), "Archive Datasets"):
                if "is_confidential" in dataset_definition and not dataset_definition["is_confidential"]:
                    for i in ["training-datasets", "training-datasets-truth"]:
                        shutil.copytree(
                            Path(settings.TIRA_ROOT) / "data" / "datasets" / i / job["TIRA_TASK_ID"] / dataset_name,
                            Path(working_directory) / dataset_name / i,
                        )

        self.archive_all_softwares(working_directory, download_images, persist_images, upload_images)
        # logger.info(f'Archive repository into {repo_name}.zip')
        # shutil.make_archive(repo_name, 'zip', working_directory)
        logger.info(f"The repository is archived into {working_directory}")


class GitLabRunner(GitRunner):

    def __init__(
        self,
        private_token,
        host,
        user_name,
        user_password,
        gitlab_repository_namespace_id,
        image_registry_prefix,
        user_repository_branch,
    ):
        self.git_token = private_token
        self.user_name = user_name
        self.host = host
        self.user_password = user_password
        self.namespace_id = int(gitlab_repository_namespace_id)
        self.image_registry_prefix = image_registry_prefix
        self.user_repository_branch = user_repository_branch
        self.gitHoster_client = gitlab.Gitlab("https://" + host, private_token=self.git_token)
        # self.gitHoster_client = gitlab.Gitlab('https://' + host, private_token=json.load(open('/home/maik/.tira/.tira-settings.json'))['access_token'])

    def template_ci(self):
        """
        returns the CI-Pipeline template file as string
        """
        return render_to_string("tira/git_task_repository_gitlab_ci.yml", context={})

    def template_ci_file_name(self):
        return ".gitlab-ci.yml"

    def template_readme(self, task_id):
        """
        returns the readme template file for Gitlab as string
        """
        return render_to_string("tira/git_task_repository_readme.md", context={"task_name": task_id})

    def template_tira_cmd_script(self, project):
        return render_to_string("tira/tira_git_cmd.sh", context={"project_id": project.id, "ci_server_host": self.host})

    def repo_url(self, git_repository_id):
        project = self.gitHoster_client.projects.get(git_repository_id)

        return project.http_url_to_repo.replace(self.host, self.user_name + ":" + self.git_token + "@" + self.host)

    def get_manifest_of_docker_image_image_repository(self, repository_name, tag, cache, force_cache_refresh):
        """
        Background for the implementation:
        https://dille.name/blog/2018/09/20/how-to-tag-docker-images-without-pulling-them/
        https://gitlab.com/gitlab-org/gitlab/-/issues/23156
        """
        registry_host = self.image_registry_prefix.split("/")[0]
        repository_name = repository_name.split(registry_host + "/")[-1]

        cache_key = f"docker-manifest-for-repo-{repository_name}-{tag}"
        if cache:
            ret = cache.get(cache_key)
            if ret is not None:
                return ret

        try:
            token = requests.get(
                f"https://{self.host}:{self.git_token}@git.webis.de/jwt/auth?client_id=docker&offline_token=true&service=container_registry&scope=repository:{repository_name}:push,pull,blob,upload"
            )

            if not token.ok:
                raise ValueError(token.content.decode("UTF-8"))

            token = json.loads(token.content.decode("UTF-8"))["token"]
            headers = {
                "Accept": "application/vnd.docker.distribution.manifest.v2+json",
                "Content-Type": "application/vnd.docker.distribution.manifest.v2+json",
                "Authorization": "Bearer " + token,
            }
            manifest = requests.get(f"https://{registry_host}/v2/{repository_name}/manifests/{tag}", headers=headers)

            if not manifest.ok:
                raise ValueError("-->" + manifest.content.decode("UTF-8"))

            image_metadata = json.loads(manifest.content.decode("UTF-8"))
            raw_size = image_metadata["config"]["size"] + sum([i["size"] for i in image_metadata["layers"]])
            size = convert_size(raw_size)

            image_config = requests.get(
                f'https://{registry_host}/v2/{repository_name}/blobs/{image_metadata["config"]["digest"]}',
                headers=headers,
            )

            if not image_config.ok:
                raise ValueError("-->" + image_config.content.decode("UTF-8"))

            image_config = json.loads(image_config.content.decode("UTF-8"))

            ret = {
                "architecture": image_config["architecture"],
                "created": image_config["created"],
                "size": size,
                "raw_size": raw_size,
                "digest": image_metadata["config"]["digest"].split(":")[-1][:12],
            }
        except Exception as e:
            logger.warn("Exception during loading of metadata for docker image", e)
            ret = {
                "architecture": "Loading...",
                "created": "Loading...",
                "size": "Loading...",
                "digest": "Loading...",
                "raw_size": "Loading...",
            }

        if cache:
            logger.info(f"Cache refreshed for key {cache_key} ...")
            cache.set(cache_key, ret)

        return ret

    def run_evaluate_with_git_workflow(
        self, task_id, dataset_id, vm_id, run_id, git_runner_image, git_runner_command, git_repository_id, evaluator_id
    ):
        msg = f"start run_eval with git: {task_id} - {dataset_id} - {vm_id} - {run_id}"
        logger.info(msg)
        transaction_id = self.start_git_workflow(
            task_id,
            dataset_id,
            vm_id,
            run_id,
            git_runner_image,
            git_runner_command,
            git_repository_id,
            evaluator_id,
            "ubuntu:18.04",
            "echo 'No software to execute. Only evaluation'",
            "-1",
            list(settings.GIT_CI_AVAILABLE_RESOURCES.keys())[0],
            None,
            None,
            None,
        )

        t = TransactionLog.objects.get(transaction_id=transaction_id)
        _ = EvaluationLog.objects.update_or_create(vm_id=vm_id, run_id=run_id, running_on=vm_id, transaction=t)

        return transaction_id

    def run_docker_software_with_git_workflow(
        self,
        task_id,
        dataset_id,
        vm_id,
        run_id,
        git_runner_image,
        git_runner_command,
        git_repository_id,
        evaluator_id,
        user_image_to_execute,
        user_command_to_execute,
        tira_software_id,
        resources,
        input_run,
        mount_hf_model,
        workdir_in_user_image,
    ):
        msg = f"start run_docker_image with git: {task_id} - {dataset_id} - {vm_id} - {run_id}"
        logger.info(msg)
        transaction_id = self.start_git_workflow(
            task_id,
            dataset_id,
            vm_id,
            run_id,
            git_runner_image,
            git_runner_command,
            git_repository_id,
            evaluator_id,
            user_image_to_execute,
            user_command_to_execute,
            tira_software_id,
            resources,
            input_run,
            mount_hf_model,
            workdir_in_user_image,
        )

        # TODO: add transaction to log

        return transaction_id

    def start_git_workflow(
        self,
        task_id,
        dataset_id,
        vm_id,
        run_id,
        git_runner_image,
        git_runner_command,
        git_repository_id,
        evaluator_id,
        user_image_to_execute,
        user_command_to_execute,
        tira_software_id,
        resources,
        input_run,
        mount_hf_model,
        workdir_in_user_image,
    ):
        msg = f"start git-workflow with git: {task_id} - {dataset_id} - {vm_id} - {run_id}"
        transaction_id = new_transaction(msg, in_grpc=False)
        logger.info(msg)

        identifier = f"eval---{dataset_id}---{vm_id}---{run_id}---started-{str(dt.now().strftime('%Y-%m-%d-%H-%M-%S'))}"

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = self.clone_repository_and_create_new_branch(self.repo_url(git_repository_id), identifier, tmp_dir)

            self.write_metadata_for_ci_job_to_repository(
                tmp_dir,
                task_id,
                transaction_id,
                dataset_id,
                vm_id,
                run_id,
                identifier,
                git_runner_image,
                git_runner_command,
                evaluator_id,
                user_image_to_execute,
                user_command_to_execute,
                tira_software_id,
                resources,
                input_run,
                mount_hf_model,
                workdir_in_user_image,
            )

            self.commit_and_push(repo, dataset_id, vm_id, run_id, identifier, git_repository_id, resources)

            t = TransactionLog.objects.get(transaction_id=transaction_id)
            _ = EvaluationLog.objects.update_or_create(vm_id=vm_id, run_id=run_id, running_on=vm_id, transaction=t)

        return transaction_id

    def commit_and_push(self, repo, dataset_id, vm_id, run_id, identifier, git_repository_id, resources):
        repo.index.add([str(Path(dataset_id) / vm_id / run_id / "job-to-execute.txt")])
        repo.index.commit("Evaluate software: " + identifier)
        gpu_resources = str(settings.GIT_CI_AVAILABLE_RESOURCES[resources]["gpu"]).strip()
        data_resources = str(settings.GIT_CI_AVAILABLE_RESOURCES[resources]["data"]).strip()

        if gpu_resources == "0" and data_resources == "no":
            repo.remote().push(identifier)
        else:
            repo.remote().push(identifier, **{"o": "ci.skip"})

            gl_project = self.gitHoster_client.projects.get(int(git_repository_id))
            gl_project.pipelines.create(
                {
                    "ref": identifier,
                    "variables": [
                        {"key": "TIRA_GPU", "value": gpu_resources},
                        {"key": "TIRA_DATA", "value": data_resources},
                    ],
                }
            )

    def add_new_tag_to_docker_image_repository(self, repository_name, old_tag, new_tag):
        """
        Background for the implementation:
        https://dille.name/blog/2018/09/20/how-to-tag-docker-images-without-pulling-them/
        https://gitlab.com/gitlab-org/gitlab/-/issues/23156
        """
        original_repository_name = repository_name
        registry_host = self.image_registry_prefix.split("/")[0]
        repository_name = repository_name.split(registry_host + "/")[-1]

        token = requests.get(
            f"https://{self.host}:{self.git_token}@git.webis.de/jwt/auth?client_id=docker&offline_token=true&service=container_registry&scope=repository:{repository_name}:push,pull"
        )

        if not token.ok:
            raise ValueError(token.content.decode("UTF-8"))

        token = json.loads(token.content.decode("UTF-8"))["token"]
        headers = {
            "Accept": "application/vnd.docker.distribution.manifest.v2+json",
            "Content-Type": "application/vnd.docker.distribution.manifest.v2+json",
            "Authorization": "Bearer " + token,
        }

        manifest = requests.get(f"https://{registry_host}/v2/{repository_name}/manifests/{old_tag}", headers=headers)

        if not manifest.ok:
            raise ValueError("-->" + manifest.content.decode("UTF-8"))
        manifest = manifest.content.decode("UTF-8")

        manifest = requests.put(
            f"https://{registry_host}/v2/{repository_name}/manifests/{new_tag}", headers=headers, data=manifest
        )

        if not manifest.ok:
            raise ValueError(manifest.content.decode("UTF-8"))

        return original_repository_name + ":" + new_tag

    def all_user_repositories(self):
        """
        Lists all user repositories in the organization.

        Return
        ----------
        user_repositories: Iterable[str]
        List of all user repositories in the organization.
        """

        ret = []
        for potential_existing_projects in self.gitHoster_client.projects.list(search="tira-user-", get_all=True):
            if (
                "tira-user-" in potential_existing_projects.name
                and int(potential_existing_projects.namespace["id"]) == self.namespace_id
            ):
                ret += [potential_existing_projects.name]
        return set(ret)

    def existing_repository(self, repo):
        for potential_existing_projects in self.gitHoster_client.projects.list(search=repo):
            if (
                potential_existing_projects.name == repo
                and int(potential_existing_projects.namespace["id"]) == self.namespace_id
            ):
                return potential_existing_projects

    def clean_task_repository(self, task_id):
        project = self.existing_repository(task_id)
        for pipeline in project.pipelines.list(get_all=True):
            print("Delete Pipeline: " + str(pipeline.id))
            if pipeline.status not in {"skipped", "canceled", "failed", "success"}:
                print("Skip running pipeline " + str(pipeline.id))
                continue
            pipeline.delete()

    def _create_task_repository_on_gitHoster(self, task_id):
        project = self.existing_repository(task_id)
        if project:
            print(f'Repository found "{task_id}".')
            return project

        project = self.gitHoster_client.projects.create(
            {"name": task_id, "namespace_id": str(self.namespace_id), "default_branch": self.user_repository_branch}
        )
        return project

    def _create_access_token_gitHoster(self, project, repo):
        return project.access_tokens.create(
            {
                "name": repo,
                "scopes": ["read_registry", "write_registry"],
                "access_level": 30,
                "expires_at": "2024-10-08",
            }
        )

    def stop_job_and_clean_up(self, git_repository_id, user_name, run_id, cache=None):
        """
        All runs that are currently running, pending, or failed
        life in a dedicated branch.
        Every successfully (without errors/failures and with evaluation)
        executed software is merged into the main branch.
        This method stops a potentially running pipeline identified by the run_id
        of the user "user_id" and deletes the branch.

        Parameters
        ----------
        git_repository_id: str
        Identifier of the task repository.
        (gitlab: int; github: int)

        user_name: str
        Name of the user. The repository of the user has the name "tira-user-${user_name}".

        run_id: str
        Identifier of the to be stopped run.

        Return
        ----------
        -
        """
        gl = self.gitHoster_client
        gl_project = gl.projects.get(int(git_repository_id))

        for pipeline in self.yield_all_running_pipelines(git_repository_id, user_name, cache, True):
            if run_id == pipeline["run_id"]:
                branch = pipeline["branch"] if "branch" in pipeline else pipeline["pipeline"].ref
                if ("---" + user_name + "---") not in branch:
                    continue
                if ("---" + run_id + "---") not in branch:
                    continue

                if "pipeline" in pipeline:
                    pipeline["pipeline"].cancel()
                gl_project.branches.delete(branch)

    def yield_all_running_pipelines(self, git_repository_id, user_id, cache=None, force_cache_refresh=False):
        for pipeline in self.all_running_pipelines_for_repository(git_repository_id, cache, force_cache_refresh):
            pipeline = deepcopy(pipeline)

            if ("---" + user_id + "---") not in pipeline["pipeline_name"]:
                continue

            if ("-training---" + user_id + "---") not in pipeline["pipeline_name"]:
                pipeline["stdOutput"] = "Output for runs on the test-data is hidden."

            yield pipeline

    def all_running_pipelines_for_repository(self, git_repository_id, cache=None, force_cache_refresh=False):
        cache_key = "all-running-pipelines-repo-" + str(git_repository_id)
        if cache:
            try:
                ret = cache.get(cache_key)
                if ret is not None and not force_cache_refresh:
                    logger.debug("get ret from cache", ret)
                    return ret
            except Exception:
                logger.exception(f"Could not find cache module {cache_key}.")

        ret = []
        gl = self.gitHoster_client
        gl_project = gl.projects.get(int(git_repository_id))
        already_covered_run_ids = set()
        for status in ["scheduled", "running", "pending", "created", "waiting_for_resource", "preparing"]:
            for pipeline in gl_project.pipelines.list(status=status):
                user_software_job = None
                evaluation_job = None
                for job in pipeline.jobs.list():
                    if "run-user-software" == job.name:
                        user_software_job = job
                    if "evaluate-software-result" == job.name:
                        evaluation_job = job
                        logger.debug(f"TODO: pass evaluation jobs in different structure to UI: {evaluation_job}")

                p = (pipeline.ref + "---started-").split("---started-")[0]

                execution = {"scheduling": "running", "execution": "pending", "evaluation": "pending"}
                if user_software_job.status == "running":
                    execution = {"scheduling": "done", "execution": "running", "evaluation": "pending"}
                elif user_software_job.status != "created":
                    execution = {"scheduling": "done", "execution": "done", "evaluation": "running"}

                stdout = "Output for runs on the test-data is hidden."
                if "-training---" in p:
                    try:
                        stdout = ""
                        user_software_job = gl_project.jobs.get(user_software_job.id)
                        stdout = self.clean_job_output(user_software_job.trace().decode("UTF-8"))
                    except Exception:
                        # Job is not started or similar
                        pass

                run_id = p.split("---")[-1]

                already_covered_run_ids.add(run_id)
                job_config = self.extract_job_configuration(gl_project, pipeline.ref)
                if job_config:
                    ret += [
                        {
                            "run_id": run_id,
                            "execution": execution,
                            "stdOutput": stdout,
                            "started_at": p.split("---")[-1],
                            "pipeline_name": p,
                            "job_config": job_config,
                            "pipeline": pipeline,
                        }
                    ]

        ret += self.__all_failed_pipelines_for_repository(gl_project, already_covered_run_ids)

        if cache:
            logger.info(f"Cache refreshed for key {cache_key} ...")
            cache.set(cache_key, ret)

        return ret

    def clean_job_output(self, ret):
        ret = "".join(filter(lambda x: x in string.printable, ret.strip()))
        if '$ eval "${TIRA_COMMAND_TO_EXECUTE}"[0;m' in ret:
            return self.clean_job_suffix(ret.split('$ eval "${TIRA_COMMAND_TO_EXECUTE}"[0;m')[1])
        elif '$ eval "${TIRA_EVALUATION_COMMAND_TO_EXECUTE}"[0;m' in ret:
            return self.clean_job_suffix(ret.split('$ eval "${TIRA_EVALUATION_COMMAND_TO_EXECUTE}"[0;m')[1])
        else:
            # Job not jet started.
            return ""

    def clean_job_suffix(self, ret):
        if "[32;1m$ env|grep 'TIRA' > task.env" in ret:
            ret = ret.split("[32;1m$ env|grep 'TIRA' > task.env")[0]
        if "section_end:" in ret:
            ret = ret.split("section_end:")[0]

        return ret.strip()

    def extract_job_configuration(self, gl_project, branch):
        ret = {}

        if not branch or branch.strip().lower() == "main":
            return None

        try:
            for commit in gl_project.commits.list(ref_name=branch, page=0, per_page=3):
                if len(ret) > 0:
                    break

                if branch in commit.title and "Merge" not in commit.title:
                    for diff_entry in commit.diff():
                        if len(ret) > 0:
                            break

                        if diff_entry["old_path"] == diff_entry["new_path"] and diff_entry["new_path"].endswith(
                            "/job-to-execute.txt"
                        ):
                            diff_entry = diff_entry["diff"].replace("\n+", "\n").split("\n")
                            ret = {
                                i.split("=")[0].strip(): i.split("=")[1].strip()
                                for i in diff_entry
                                if len(i.split("=")) == 2
                            }
        except Exception as e:
            logger.warn(f'Could not extract job configuration on "{branch}".', e)
            pass

        if (
            "TIRA_COMMAND_TO_EXECUTE" in ret
            and "'No software to execute. Only evaluation'" in ret["TIRA_COMMAND_TO_EXECUTE"]
            and ("TIRA_SOFTWARE_ID" not in ret or "-1" == ret["TIRA_SOFTWARE_ID"])
        ):
            software_from_db = {"display_name": "Evaluate Run", "image": "evaluator", "command": "evaluator"}
        else:
            try:
                from tira.tira_model import model

                software_from_db = model.get_docker_software(int(ret["TIRA_SOFTWARE_ID"].split("docker-software-")[-1]))
            except Exception as e:
                logger.warn(f'Could not extract the software from the database for "{json.dumps(ret)}": {str(e)}')
                software_from_db = {}

        return {
            "software_name": software_from_db.get("display_name", "Loading..."),
            "image": software_from_db.get("user_image_name", "Loading..."),
            "command": software_from_db.get("command", "Loading..."),
            "cores": str(ret.get("TIRA_CPU_COUNT", "Loading...")) + " CPU Cores",
            "ram": str(ret.get("TIRA_MEMORY_IN_GIBIBYTE", "Loading...")) + "GB of RAM",
            "gpu": str(ret.get("TIRA_GPU", "Loading...")) + " GPUs",
            "data": str(ret.get("TIRA_DATA", "Loading...")) + " Mounts",
            "dataset_type": ret.get("TIRA_DATASET_TYPE", "Loading..."),
            "dataset": ret.get("TIRA_DATASET_ID", "Loading..."),
            "software_id": ret.get("TIRA_SOFTWARE_ID", "Loading..."),
            "task_id": ret.get("TIRA_TASK_ID", "Loading..."),
        }

    def __all_failed_pipelines_for_repository(self, gl_project, already_covered_run_ids):
        ret = []

        for branch in gl_project.branches.list():
            branch = branch.name
            p = (branch + "---started-").split("---started-")[0]
            run_id = p.split("---")[-1]

            if run_id in already_covered_run_ids:
                continue

            job_config = self.extract_job_configuration(gl_project, branch)
            if not job_config:
                continue

            ret += [
                {
                    "run_id": run_id,
                    "execution": {"scheduling": "failed", "execution": "failed", "evaluation": "failed"},
                    "pipeline_name": p,
                    "stdOutput": (
                        "Job did not run. (Maybe it is still submitted to the cluster or failed to start. It might take"
                        " up to 5 minutes to submit a Job to the cluster.)"
                    ),
                    "started_at": p.split("---")[-1],
                    "branch": branch,
                    "job_config": job_config,
                }
            ]

        return ret


class GithubRunner(GitRunner):

    def __init__(self, github_token):
        self.git_token = github_token
        self.gitHoster_client = Github(self.git_token)

    def _convert_repository_id_to_repository_name(self, repository_id):
        for repo in self.gitHoster_client.get_user().get_repos():
            if repo.id == repository_id:
                return repo.name

    def template_ci(self):
        """
        returns the Workflow template file as string
        """
        # TODO: create workflow template file at tira/application/src/tira/templates/tira/git_task_repository_github_workflow.yml
        return render_to_string("tira/git_task_repository_github_workflow.yml", context={})

    def template_readme(self, task_id):
        """
        returns the readme template file for Github as string
        """
        # TODO: create readme template file for Github at tira/application/src/tira/templates/tira/git_task_repository_github_workflow.yml
        return render_to_string("tira/git_task_repository_github_readme.md", context={"task_name": task_id})

    def template_tira_cmd_script(self, project_id):
        return render_to_string(
            "tira/tira_git_cmd.sh", context={"project_id": project_id, "ci_server_host": "https://github.com"}
        )

    def add_new_tag_to_docker_image_repository(self, repository_name, old_tag, new_tag):
        for repo in self.gitHoster_client.get_user().get_repos():
            if repo.name == repository_name:
                tags = repo.tags
                if new_tag not in tags:
                    repo.create_tag(new_tag)
                    repo.git.push(tags=True)  # Brauchen wir das?
                else:
                    logger.info(f"Tag: {new_tag} already exists with the same name")

    def all_user_repositories(self):
        """
        Lists all user repositories in the organization "user_name".

        Return
        ----------
        user_repositories: Iterable[str]
        List of all user repositories in the organization.
        """

        ret = []
        for repo in self.gitHoster_client.get_user().get_repos():
            ret.append(repo.name)

        return set(ret)

    def stop_job_and_clean_up(self, git_repository_id, user_name, run_id):
        """
        All runs that are currently running, pending, or failed
        life in a dedicated branch.
        Every successfully (without errors/failures and with evaluation)
        executed software is merged into the main branch.
        This method stops a potentially running pipeline identified by the run_id
        of the user "user_id" and deletes the branch.

        Parameters
        ----------
        git_repository_id: str
        Identifier of the task repository.
        (gitlab: int; github: int)

        user_name: str
        Name of the user. The repository of the user has the name "tira-user-${user_name}".

        run_id: str
        Identifier of the to be stopped run.

        Return
        ----------
        -
        """
        repository_name = self._convert_repository_id_to_repository_name(git_repository_id)

        # cancel worflow run
        run = self.gitHoster_client.get_user().get_repo(repository_name).get_workflow_run(run_id)
        run.cancel()

        # delete branch
        branch_name = run.head_branch
        self.gitHoster_client.get_user().get_repo(repository_name).get_git_ref(f"heads/{branch_name}").delete

    def _create_task_repository_on_gitHoster(self, task_id):
        # create new repository and rename the default branch
        project = self.gitHoster_client.get_user().create_repo(name=task_id)
        for branch in project.get_branches():
            project.rename_branch(branch=branch, new_name=self.user_repository_branch)
        return project

    def _create_access_token_gitHoster(self, project, repo):
        raise ValueError("ToDo: Implement this.")

    def yield_all_running_pipelines(self, git_repository_id):
        """
        Yield all pipelines/workflows that are currently running, pending, or failed.


        Parameters
        ----------
        git_repository_id: str
        Identifier of the task repository.
        (gitlab: int; github: int)

        Return
        ----------
        jobs: Iteratable[dict]
        all pipelines/workflows that are currently running, pending, or failed.
        Each entry has the following fields:
            'run_id',
            'execution',
            'stdOutput',
            'started_at',
            'pipeline_name',
            'job_config',
            'pipeline'
        """
        # https://docs.github.com/en/rest/actions/workflow-jobs?apiVersion=2022-11-28#get-a-job-for-a-workflow-run
        pass

    def git_user_exists(self, user_name):
        try:
            return self.gitHoster_client.get_user(user_name) is not None
        except Exception:
            return False

    def get_git_runner_for_software_integration(
        self,
        reference_repository_name,
        user_repository_name,
        user_repository_namespace,
        github_user,
        tira_user_name,
        dockerhub_token,
        dockerhub_user,
        tira_client_token,
        repository_search_prefix,
        tira_task_id,
        tira_code_repository_id,
        tira_client_user,
        private,
    ):
        user = self.gitHoster_client.get_user()
        try:
            user_repo = user.get_repo(f"{user_repository_namespace}/{user_repository_name}")
            if user_repo:
                return user_repo
        except Exception:
            # repository does not exist.
            pass

        return self.create_software_submission_repository_for_user(
            reference_repository_name,
            user_repository_name,
            user_repository_namespace,
            github_user,
            tira_user_name,
            dockerhub_token,
            dockerhub_user,
            tira_client_token,
            repository_search_prefix,
            tira_task_id,
            tira_code_repository_id,
            tira_client_user,
            private,
        )

    def create_software_submission_repository_for_user(
        self,
        reference_repository_name,
        user_repository_name,
        user_repository_namespace,
        github_user,
        tira_user_name,
        dockerhub_token,
        dockerhub_user,
        tira_client_token,
        repository_search_prefix,
        tira_task_id,
        tira_code_repository_id,
        tira_client_user,
        private,
    ):
        reference_repo = self.gitHoster_client.get_repo(reference_repository_name)

        org = self.gitHoster_client.get_organization(user_repository_namespace)
        repo = org.create_repo(
            user_repository_name,
            f"The repository of user {tira_user_name} for code submissions in TIRA.",
            private=private,
        )
        repo.add_to_collaborators(github_user, "admin")

        repo.create_secret("TIRA_DOCKER_REGISTRY_TOKEN", dockerhub_token)
        repo.create_secret("TIRA_DOCKER_REGISTRY_USER", dockerhub_user)
        repo.create_secret("TIRA_CLIENT_TOKEN", tira_client_token)
        repo.create_secret("TIRA_CLIENT_USER", tira_client_user)
        repo.create_secret("TIRA_CODE_REPOSITORY_ID", tira_code_repository_id)

        contents = reference_repo.get_contents(repository_search_prefix)
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(reference_repo.get_contents(file_content.path))
            else:
                decoded_content = file_content.decoded_content.decode()
                decoded_content = normalize_file(decoded_content, tira_user_name, tira_task_id)
                repo.create_file(file_content.path, "Initial Commit.", decoded_content)

        return repo
