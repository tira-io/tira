"""
p.stat().st_mtime - change time
"""

import datetime
import logging
import tempfile
from distutils.dir_util import copy_tree
from pathlib import Path
from typing import Any, Optional

import randomname
from discourse_client_in_disraptor import DiscourseApiClient
from django.conf import settings
from django.core.cache import BaseCache, cache
from django.db import connections, router
from slugify import slugify

from .data.HybridDatabase import HybridDatabase
from .git_runner import get_git_runner, get_git_runner_for_software_integration
from .util import get_tira_id, register_run

logger = logging.getLogger("tira")

model = HybridDatabase()


# reloading and reindexing
def build_model():
    """reconstruct the caches and the database."""
    model.build_model()


def reload_vms():
    """reload VM and user data from the export format of the model"""
    model.reload_vms()


def reload_datasets():
    """reload dataset data from the export format of the model"""
    model.reload_datasets()


def reload_tasks():
    """reload task data from the export format of the model"""
    model.reload_tasks()


def reload_runs(vm_id):
    """reload run data for a VM from the export format of the model"""
    model.reload_runs(vm_id)


# get methods are the public interface.
def get_vm(vm_id: str, create_if_none=False):
    """Returns a vm as dictionary with:

        {"vm_id", "user_password", "roles", "host", "admin_name",
        "admin_pw", "ip", "ssh", "rdp", "archived"}

    Some fields may be None.
    """
    return model.get_vm(vm_id, create_if_none)


def get_tasks(include_dataset_stats=False) -> list:
    return model.get_tasks(include_dataset_stats)


def get_run(dataset_id: str, vm_id: str, run_id: str, return_deleted: bool = False) -> dict:
    return model.get_run(dataset_id, vm_id, run_id, return_deleted)


def get_task(task_id: str, include_dataset_stats=False) -> dict:
    """Get a dict with the task data as follows:
    {"task_id", "task_name", "task_description", "organizer", "web", "year", "dataset_count",
    "software_count", "max_std_out_chars_on_test_data", "max_std_err_chars_on_test_data",
    "max_file_list_chars_on_test_data", "command_placeholder",  "command_description", "dataset_label",
    "max_std_out_chars_on_test_data_eval", "max_std_err_chars_on_test_data_eval",
    "max_file_list_chars_on_test_data_eval"}
    """
    return model.get_task(task_id, include_dataset_stats)


def get_dataset(dataset_id: str) -> dict[str, Any]:
    """Return a Dataset as dict with the keys:

    {"display_name", "evaluator_id", "dataset_id", "is_confidential", "is_deprecated", "year",
    "task".task_id, 'organizer', "software_count"}
    """
    return model.get_dataset(dataset_id)


def get_datasets() -> dict:
    """Get a dict of dataset_id: dataset_json_descriptor"""
    return model.get_datasets()


def get_datasets_by_task(task_id: str, include_deprecated=False, return_only_names=False) -> list[dict[str, Any]]:
    """return the list of datasets associated with this task_id
    @param task_id: id string of the task the dataset belongs to
    @param include_deprecated: Default False. If True, also returns datasets marked as deprecated.
    @return: a list of json-formatted datasets, as returned by get_dataset
    """
    return model.get_datasets_by_task(task_id, include_deprecated, return_only_names)


def load_refresh_timestamp_for_cache_key(cache, key):
    try:
        db = router.db_for_read(cache.cache_model_class)
        connection = connections[db]
        quote_name = connection.ops.quote_name

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT %s FROM %s WHERE %s = '%s'"
                % (
                    quote_name("expires"),
                    quote_name(cache._table),
                    quote_name("cache_key"),
                    cache.make_and_validate_key(key),
                )
            )

            ret = cursor.fetchall()
            if len(ret) > 0:
                return ret[0][0] - datetime.timedelta(seconds=settings.CACHES["default"]["TIMEOUT"])
    except Exception:
        pass

    return datetime.datetime.now()


def discourse_api_client():
    return DiscourseApiClient(url=settings.DISCOURSE_API_URL, api_key=settings.DISRAPTOR_API_KEY)


def tira_run_command(image: str, command: str, task_id: str):
    input_dataset = reference_dataset(task_id)

    return f"tira-run \\\n  --input-dataset {input_dataset} \\\n  --image {image} \\\n  --command '{command}'"


def reference_dataset(task_id: str):
    if task_id in settings.REFERENCE_DATASETS:
        return settings.REFERENCE_DATASETS[task_id]
    else:
        available_datasets = get_datasets_by_task(task_id)
        available_datasets = [
            i["dataset_id"]
            for i in available_datasets
            if i["dataset_id"].endswith("-training") and not i["is_confidential"] and not i["is_deprecated"]
        ]
        if len(available_datasets) > 0:
            return f"{task_id}/{available_datasets[0]}"
        else:
            return f"{task_id}/ADD-DATASET-ID-HERE"


def tira_docker_registry_token(docker_software_help):
    ret = docker_software_help.split("docker login -u ")[1].split(" -p")
    return ret[0].strip(), ret[1].split(" ")[0].strip()


def load_docker_data(task_id, vm_id, cache, force_cache_refresh):
    """
    Get the docker data for a particular user (vm_id) from the git registry.

    @return: a dict with three keys:
        - docker_images: a list of strings (the image's names)
        - docker_softwares: A list of all submitted containers with their run results as a dict with keys:
            - docker_software_id: str, display_name: str, user_image_name: str, command: str,
              tira_image_name: str, task_id: str, vm_id: str, runs: list (same as get_runs)
        - docker_software_help: A string with the help instructions
    """
    if not git_pipeline_is_enabled_for_task(task_id, cache, force_cache_refresh):
        return False

    git_runner = get_git_integration(task_id=task_id)
    docker_images = [
        i
        for i in git_runner.docker_images_in_user_repository(vm_id, cache, force_cache_refresh)
        if "-tira-docker-software-id-" not in i["image"]
    ]
    last_refresh = load_refresh_timestamp_for_cache_key(cache, "docker-images-in-user-repository-tira-user-" + vm_id)
    docker_software_help = git_runner.help_on_uploading_docker_image(vm_id, cache, force_cache_refresh)
    public_docker_softwares = model.get_public_docker_softwares(task_id)

    # removed for the moment as tira-cli uses the above already.
    # docker_login = "docker login" + docker_software_help.split("<code>docker login")[1].split("</code>")[0]

    return {
        "docker_images": docker_images,
        "resources": list(settings.GIT_CI_AVAILABLE_RESOURCES.values()),
        "docker_software_help": docker_software_help,
        "docker_images_last_refresh": str(last_refresh),
        "docker_registry_user": tira_docker_registry_token(docker_software_help)[0],
        "docker_registry_token": tira_docker_registry_token(docker_software_help)[1],
        "public_docker_softwares": public_docker_softwares,
        "task_is_an_information_retrieval_task": True if get_task(task_id, False).get("is_ir_task", False) else False,
        "docker_images_next_refresh": str(
            None if last_refresh is None else (last_refresh + datetime.timedelta(seconds=60))
        ),
        "tira_initial_run_example": "# This example shows how to execute the baseline on a small example dataset.\n"
        + "# Please adjust the --image and --command parameters accordingly.\n"
        + tira_run_command("YOUR-IMAGE", "YOUR-COMMAND", task_id),
        "tira_final_run_example":  # '# The configuration of your software is final, please do a final test:\n' +
        # docker_login + '\n' +
        '# Please append "--push true" to your previous tira-run command to upload your software.\n# I.e., the --image'
        " and --command parameters are as before.\n"
        + tira_run_command("YOUR-IMAGE", "YOUR-COMMAND", task_id)
        + " \\\n  --push true",
    }


def github_user_exists(user_name):
    g = get_git_runner_for_software_integration()
    return g.git_user_exists(user_name)


def get_discourse_token_for_user(vm_id, disraptor_user):
    ret = model.get_discourse_token_for_user(vm_id)
    if ret:
        return ret

    disraptor_description = disraptor_user + "-repo-" + vm_id
    discourse_api_key = discourse_api_client().generate_api_key(disraptor_user, disraptor_description)

    model.create_discourse_token_for_user(vm_id, discourse_api_key)

    return model.get_discourse_token_for_user(vm_id)


def get_submission_git_repo(vm_id, task_id, disraptor_user=None, external_owner=None, private=True):
    user_repository_name = slugify(task_id) + "-" + slugify(vm_id)
    repository_url = settings.CODE_SUBMISSION_REPOSITORY_NAMESPACE + "/" + user_repository_name
    ret = model.get_submission_git_repo_or_none(repository_url, vm_id)

    if ret and "repo_url" in ret or (not disraptor_user and not external_owner):
        return ret

    docker_data = load_docker_data(task_id, vm_id, cache, force_cache_refresh=False)
    docker_registry_user = docker_data["docker_registry_user"]
    docker_registry_token = docker_data["docker_registry_token"]
    reference_repository = settings.CODE_SUBMISSION_REFERENCE_REPOSITORIES[task_id]
    disraptor_description = disraptor_user + "-repo-" + task_id + "-" + vm_id
    discourse_api_key = discourse_api_client().generate_api_key(disraptor_user, disraptor_description)

    model.create_submission_git_repo(
        repository_url,
        vm_id,
        docker_registry_user,
        docker_registry_token,
        discourse_api_key,
        reference_repository,
        external_owner,
        disraptor_user,
        disraptor_description,
    )
    ret = model.get_submission_git_repo_or_none(repository_url, vm_id, return_object=True)

    g = get_git_runner_for_software_integration()
    g.get_git_runner_for_software_integration(
        reference_repository_name=reference_repository,
        user_repository_name=user_repository_name,
        user_repository_namespace=settings.CODE_SUBMISSION_REPOSITORY_NAMESPACE,
        github_user=external_owner,
        dockerhub_token=docker_registry_token,
        dockerhub_user=docker_registry_user,
        tira_client_token=discourse_api_key,
        repository_search_prefix="",
        tira_user_name=vm_id,
        tira_task_id=task_id,
        tira_code_repository_id=repository_url,
        tira_client_user=disraptor_user,
        private=private,
    )

    ret.confirmed = True
    ret.save()

    return model.get_submission_git_repo_or_none(repository_url, vm_id)


def git_pipeline_is_enabled_for_task(task_id: str, cache: BaseCache, force_cache_refresh: bool = False):
    evaluators_for_task = get_evaluators_for_task(task_id, cache, force_cache_refresh)
    git_runners_for_task = [i["is_git_runner"] for i in evaluators_for_task]

    # We enable the docker part only if all evaluators use the docker variant.
    return len(git_runners_for_task) > 0 and all(i for i in git_runners_for_task)


def get_evaluators_for_task(task_id: str, cache: BaseCache, force_cache_refresh: bool = False):
    cache_key = "get-evaluators-for-task-" + str(task_id)
    ret = cache.get(cache_key)
    if ret is not None and not force_cache_refresh:
        return ret

    datasets = get_datasets_by_task(task_id)

    try:
        ret = [get_evaluator(i["dataset_id"]) for i in datasets]
    except Exception:
        ret = []

    logger.info(f"Cache refreshed for key {cache_key} ...")
    cache.set(cache_key, ret)

    return ret


def run_is_public_and_unblinded(run_id: str) -> bool:
    """
    Returns true if the run is published, false otherwise.
    """
    try:
        return model.run_is_public_and_unblinded(run_id)
    except Exception:
        pass

    return False


def get_docker_software(docker_software_id: int) -> dict:
    """
    Return the docker software as dict with keys:

    {'docker_software_id', 'display_name', 'user_image_name', 'command', 'tira_image_name', 'task_id', vm_id'}
    """
    return model.get_docker_software(docker_software_id)


def get_runs_for_vm(vm_id, docker_software_id, upload_id):
    docker_software_id = int(docker_software_id) if docker_software_id else None
    upload_id = int(upload_id) if upload_id else None

    return model.get_runs_for_vm(vm_id, docker_software_id, upload_id)


def get_docker_software_by_name(name, vm_id, task_id) -> dict:
    return model.get_docker_software_by_name(name, vm_id, task_id)


def __formatted_error_message_for_missing_input_run(docker_software, input_run):
    if "input_docker_software_id" in docker_software and docker_software["input_docker_software_id"]:
        return (
            f"The execution of your software depends on the execution of {docker_software['input_docker_software']}"
            + f", but {docker_software['input_docker_software']} was never executed on this dataset. "
            + f"Please execute first {docker_software['input_docker_software']} on your specified dataset. Found the"
            f" input {input_run}."
        )
    else:
        return (
            "The execution of your software depends on the upload of a manual run for the group of"
            f" {docker_software['input_docker_software']}"
            + f", but {docker_software['input_docker_software']} was not uploaded for this dataset. "
            + f"Please upload first {docker_software['input_docker_software']} on your specified dataset. Found the"
            f" input {input_run}."
        )


def get_ordered_input_runs_of_software(docker_software, task_id, dataset_id, vm_id):
    input_runs, missing_input_runs = [], []

    if ("input_docker_software_id" in docker_software and docker_software["input_docker_software_id"]) or (
        "input_upload_id" in docker_software and docker_software["input_upload_id"]
    ):
        dsid = (
            int(docker_software["input_docker_software_id"])
            if "input_docker_software_id" in docker_software and docker_software["input_docker_software_id"]
            else None
        )
        uid = (
            int(docker_software["input_upload_id"])
            if "input_upload_id" in docker_software and docker_software["input_upload_id"]
            else None
        )
        input_run = latest_output_of_software_on_dataset(task_id, None, None, dsid, dataset_id, uid)

        if not input_run or not input_run.get("dataset_id", None) or not input_run.get("run_id", None):
            missing_input_runs += [__formatted_error_message_for_missing_input_run(docker_software, input_run)]
        else:
            input_run["vm_id"] = model.get_run(run_id=input_run["run_id"], vm_id=None, dataset_id=None)["vm"]
            input_runs += [input_run]

    for dsid, uid in model.get_ordered_additional_input_runs_of_software(docker_software):
        input_run = latest_output_of_software_on_dataset(task_id, None, None, dsid, dataset_id, uid)

        if not input_run or not input_run.get("dataset_id", None) or not input_run.get("run_id", None):
            missing_input_runs += [__formatted_error_message_for_missing_input_run(docker_software, input_run)]
        else:
            input_run["vm_id"] = model.get_run(run_id=input_run["run_id"], vm_id=None, dataset_id=None)["vm"]
            input_runs += [input_run]

    if not input_runs or len(input_runs) < 1:
        return None, missing_input_runs
    if len(input_runs) == 1:
        return input_runs[0], missing_input_runs
    else:
        return input_runs, missing_input_runs


def get_organizer(organizer_id: str):
    # TODO should return as dict
    return model.get_organizer(organizer_id)


def get_host_list() -> list:
    return model.get_host_list()


def get_ova_list() -> list:
    return model.get_ova_list()


def runs(task_id, dataset_id, vm_id, software_id):
    return model.runs(task_id, dataset_id, vm_id, software_id)


def get_organizer_list() -> list:
    return model.get_organizer_list()


def get_vm_list():
    """load the vm-info file which stores all active vms as such:
    <hostname>\t<vm_id>[\t<state>]\n
    ...

    returns a list of tuples (hostname, vm_id, state)
    """
    return model.get_vm_list()


def get_vms_by_dataset(dataset_id: str) -> list:
    """return a list of vm_id's that have runs on this dataset"""
    return model.get_vms_by_dataset(dataset_id)


def get_vm_runs_by_dataset(dataset_id: str, vm_id: str, return_deleted: bool = False) -> list:
    return model.get_vm_runs_by_dataset(dataset_id, vm_id, return_deleted)


def get_vm_runs_by_task(task_id: str, vm_id: str, return_deleted: bool = False) -> list:
    """returns a list of all the runs of a user over all datasets in json (as returned by _load_user_runs)"""
    return model.get_vm_runs_by_task(task_id, vm_id, return_deleted)


def get_vms_with_reviews(dataset_id: str) -> list:
    """Get a list of all vms of a given dataset. VM's are given as a dict:
    ``{vm_id: str, "runs": list of runs, unreviewed_count: int, blinded_count: int, published_count: int}``
    """
    return model.get_vms_with_reviews(dataset_id)


def get_evaluations_of_run(vm_id, run_id):
    return model.get_evaluations_of_run(vm_id, run_id)


def get_evaluator(dataset_id: str, task_id: Optional[str] = None) -> dict[str, Any]:
    """returns a dict containing the evaluator parameters:

    vm_id: id of the master vm running the evaluator
    host: ip or hostname of the host
    command: command to execute to run the evaluator. NOTE: contains variables the host needs to resolve
    working_dir: where to execute the command
    """
    return model.get_evaluator(dataset_id, task_id)


def get_vm_evaluations_by_dataset(dataset_id, vm_id, only_public_results=True):
    """Return a dict of run_id: evaluation_results for the given vm on the given dataset
    @param only_public_results: only return the measures for published datasets.
    """
    return model.get_vm_evaluations_by_dataset(dataset_id, vm_id, only_public_results)


def get_evaluations_with_keys_by_dataset(dataset_id, include_unpublished=False, show_only_unreviewed=False):
    """Get all evaluations and evaluation measures for all vms on the given dataset.

    @param dataset_id: the dataset_id as used in tira_model
    @param include_unpublished: If True, the review status (published, blinded) is included in the evaluations.

    :returns: a tuple (ev_keys, evaluation), where ev-keys is a list of keys of the evaluation measure
    and evaluation a list of evaluations and each evaluation is a dict with {vm_id: str, run_id: str, measures: list}
    """
    return model.get_evaluations_with_keys_by_dataset(
        dataset_id, include_unpublished, show_only_unreviewed=show_only_unreviewed
    )


def get_job_details(task_id, vm_id, job_id):
    return model.get_job_details(task_id, vm_id, job_id)


def get_evaluation(run_id: str):
    """Get the evaluation of this run

    @param run_id: the id of the run
    @return: a dict with {measure_key: measure_value}
    """
    return model.get_evaluation(run_id)


def get_count_of_missing_reviews(task_id):
    return model.get_count_of_missing_reviews(task_id)


def get_count_of_team_submissions(task_id):
    return model.get_count_of_team_submissions(task_id)


def get_software_with_runs(task_id, vm_id):
    """
    Construct a dictionary that has the software as a key and as value a list of runs with that software
    Note that we order the list in such a way, that evaluations of a run are right behind that run in the list
       (based on the input_run)
    @return:
    [{"software": sw, "runs": runs_by_software.get(sw["id"]) } for sw in softwares]
    """
    return model.get_software_with_runs(task_id, vm_id)


def get_upload_with_runs(task_id, vm_id):
    """
    Construct a dictionary that has the software as a key and as value a list of runs with that software
    Note that we order the list in such a way, that evaluations of a run are right behind that run in the list
       (based on the input_run)
    @return:
    [{"software": sw, "runs": runs_by_software.get(sw["id"]) } for sw in softwares]
    """
    return model.get_upload_with_runs(task_id, vm_id)


def get_uploads(task_id, user_id):
    return model.get_uploads(task_id, user_id)


def submissions_of_user(vm_id):
    return model.submissions_of_user(vm_id)


def cloned_submissions_of_user(vm_id, task_id):
    return model.cloned_submissions_of_user(vm_id, task_id)


def import_submission(task_id, vm_id, submission_type, s_id):
    return model.import_submission(task_id, vm_id, submission_type, s_id)


def get_upload(task_id, vm_id, upload_id):
    return model.get_upload(task_id, vm_id, upload_id)


def get_docker_softwares_with_runs(task_id, vm_id):
    """
    Returns all docker software for a task and vm with runs as dictionaries.
    """
    return model.get_docker_softwares_with_runs(task_id, vm_id)


def get_docker_softwares(task_id, vm_id):
    """
    Returns all docker software for a task and vm with runs as dictionaries.
    """
    return model.get_docker_softwares(task_id, vm_id)


def get_run_review(dataset_id: str, vm_id: str, run_id: str) -> dict:
    """Returns a review as dict with the following keys:

    {"reviewer", "noErrors", "missingOutput", "extraneousOutput", "invalidOutput", "hasErrorOutput",
    "otherErrors", "comment", "hasErrors", "hasWarnings", "hasNoErrors", "published", "blinded"}

    """
    return model.get_run_review(dataset_id, vm_id, run_id)


def get_vm_reviews_by_dataset(dataset_id: str, vm_id: str) -> dict:
    return model.get_vm_reviews_by_dataset(dataset_id, vm_id)


def get_software(task_id, vm_id, software_id):
    """Returns the software of a vm on a task in json"""
    return model.get_software(task_id, vm_id, software_id)


def get_software_by_task(task_id, vm_id):
    """Returns the software of a vm on a task in json"""
    return model.get_software_by_task(task_id, vm_id)


def add_upload(task_id, vm_id, rename_to: Optional[str] = None):
    """Add empty new upload"""
    return model.add_upload(task_id, vm_id, rename_to)


def delete_upload(task_id, vm_id, upload_id):
    return model.delete_upload(task_id, vm_id, upload_id)


def update_upload_metadata(task_id, vm_id, upload_id, display_name, description, paper_link):
    return model.update_upload_metadata(task_id, vm_id, upload_id, display_name, description, paper_link)


def add_uploaded_run(task_id, vm_id, dataset_id, upload_id, uploaded_file):
    """Add the uploaded file as a new result and return it"""
    return model.add_uploaded_run(task_id, vm_id, dataset_id, upload_id, uploaded_file)


def update_docker_software_metadata(
    docker_software_id, display_name, description, paper_link, ir_re_ranker, ir_re_ranking_input
):
    return model.update_docker_software_metadata(
        docker_software_id, display_name, description, paper_link, ir_re_ranker, ir_re_ranking_input
    )


def add_docker_software_mounts(docker_software, mounts):
    model.add_docker_software_mounts(docker_software, mounts)


def add_docker_software(
    task_id, vm_id, image, command, software_inputs=None, submission_git_repo=None, build_environment=None
):
    """Add the docker software to the user of the vm and return it"""

    image, old_tag = image.split(":")
    new_tag = old_tag + "-tira-docker-software-id-" + randomname.get_name().lower()

    tira_image_name = get_git_integration(task_id=task_id).add_new_tag_to_docker_image_repository(
        image, old_tag, new_tag
    )

    input_docker_job, input_upload = {}, {}
    if software_inputs:
        for software_num, software_input in zip(range(len(software_inputs)), software_inputs):
            if not isinstance(software_input, int) and "upload" in software_input:
                input_upload[software_num] = software_input.split("-")[-1]
            else:
                input_docker_job[software_num] = software_input

    return model.add_docker_software(
        task_id,
        vm_id,
        image + ":" + old_tag,
        command,
        tira_image_name,
        input_docker_job,
        input_upload,
        submission_git_repo,
        build_environment,
    )


def add_registration(data):
    model.add_registration(data)


def all_allowed_task_teams(task_id):
    task = get_task(task_id)
    return set([i.strip() for i in task["allowed_task_teams"].split() if i.strip()])


def user_is_registered(task_id, request):
    from .authentication import auth

    allowed_task_teams = all_allowed_task_teams(task_id)
    user_vm_ids = [i.strip() for i in auth.get_vm_ids(request) if i.strip()]

    return (
        user_vm_ids is not None
        and len(user_vm_ids) > 0
        and (len(allowed_task_teams) == 0 or any([i in allowed_task_teams for i in user_vm_ids]))
    )


def remaining_team_names(task_id):
    already_used_teams = model.all_registered_teams()
    allowed_task_teams = sorted(list(all_allowed_task_teams(task_id)))
    return [i for i in allowed_task_teams if i not in already_used_teams]


# ------------------------------------------------------------
# add methods to add new data to the model
# ------------------------------------------------------------


def add_vm(vm_id: str, user_name: str, initial_user_password: str, ip: str, host: str, ssh: str, rdp: str):
    """Add a new task to the database.
    This will not overwrite existing files and instead do nothing and return false
    """
    return model.add_vm(vm_id, user_name, initial_user_password, ip, host, ssh, rdp)


def create_task(
    task_id: str,
    task_name: str,
    task_description: str,
    featured: bool,
    master_vm_id: str,
    organizer: str,
    website: str,
    require_registration: bool,
    require_groups: bool,
    restrict_groups: bool,
    help_command: Optional[str] = None,
    help_text: Optional[str] = None,
    allowed_task_teams: Optional[str] = None,
):
    """Add a new task to the database.
    CAUTION: This function does not do any sanity checks and will OVERWRITE existing tasks
    :returns: The new task as json as returned by get_task
    """
    return model.create_task(
        task_id,
        task_name,
        task_description,
        featured,
        master_vm_id,
        organizer,
        website,
        require_registration,
        require_groups,
        restrict_groups,
        help_command,
        help_text,
        allowed_task_teams,
    )


def add_dataset(
    task_id: str,
    dataset_id: str,
    dataset_type: str,
    dataset_name: str,
    upload_name: str,
    irds_docker_image: Optional[str] = None,
    irds_import_command: Optional[str] = None,
    irds_import_truth_command: Optional[str] = None,
    dataset_format: Optional[str] = None,
    description: Optional[str] = None,
    chatnoir_id: Optional[str] = None,
    ir_datasets_id: Optional[str] = None,
) -> list:
    """returns a list of paths of newly created datasets as string."""
    return model.add_dataset(
        task_id,
        dataset_id,
        dataset_type,
        dataset_name,
        upload_name,
        irds_docker_image=irds_docker_image,
        irds_import_command=irds_import_command,
        irds_import_truth_command=irds_import_truth_command,
        dataset_format=dataset_format,
        description=description,
        chatnoir_id=chatnoir_id,
        ir_datasets_id=ir_datasets_id,
    )


def add_software(task_id: str, vm_id: str):
    return model.add_software(task_id, vm_id)


def add_evaluator(
    vm_id: str,
    task_id: str,
    dataset_id: str,
    command: str,
    working_directory: str,
    measures,
    is_git_runner: Optional[bool] = False,
    git_runner_image: Optional[str] = None,
    git_runner_command: Optional[str] = None,
    git_repository_id: Optional[str] = None,
):
    ret = model.add_evaluator(
        vm_id,
        task_id,
        dataset_id,
        command,
        working_directory,
        measures,
        is_git_runner,
        git_runner_image,
        git_runner_command,
        git_repository_id,
    )

    from django.core.cache import cache

    get_evaluators_for_task(task_id=task_id, cache=cache, force_cache_refresh=True)

    return ret


def add_run(dataset_id, vm_id, run_id):
    """Add a new run to the model. Currently, this initiates the caching on the application side of things."""
    return model.add_run(dataset_id, vm_id, run_id)


def update_review(
    dataset_id,
    vm_id,
    run_id,
    reviewer_id: Optional[str] = None,
    review_date: Optional[str] = None,
    has_errors: Optional[bool] = None,
    has_no_errors: Optional[bool] = None,
    no_errors: Optional[bool] = None,
    missing_output: Optional[bool] = None,
    extraneous_output: Optional[bool] = None,
    invalid_output: Optional[bool] = None,
    has_error_output: Optional[bool] = None,
    other_errors: Optional[bool] = None,
    comment: Optional[str] = None,
    published: Optional[bool] = None,
    blinded: Optional[bool] = None,
    has_warnings: bool = False,
):
    """updates the review specified by dataset_id, vm_id, and run_id with the values given in the parameters.
    Required Parameters are also required in the function"""
    return model.update_review(
        dataset_id,
        vm_id,
        run_id,
        reviewer_id,
        review_date,
        has_errors,
        has_no_errors,
        no_errors,
        missing_output,
        extraneous_output,
        invalid_output,
        has_error_output,
        other_errors,
        comment,
        published,
        blinded,
        has_warnings,
    )


def update_run(dataset_id, vm_id, run_id, deleted: Optional[bool] = None):
    """updates the run specified by dataset_id, vm_id, and run_id with the values given in the parameters.
    Required Parameters are also required in the function"""
    return model.update_run(dataset_id, vm_id, run_id, deleted)


def update_software(
    task_id,
    vm_id,
    software_id,
    command: Optional[str] = None,
    working_directory: Optional[str] = None,
    dataset: Optional[str] = None,
    run: Optional[str] = None,
    deleted: bool = False,
):
    return model.update_software(task_id, vm_id, software_id, command, working_directory, dataset, run, deleted)


def edit_task(
    task_id: str,
    task_name: str,
    task_description: str,
    featured: bool,
    master_vm_id: str,
    organizer: str,
    website: str,
    require_registration: str,
    require_groups: str,
    restrict_groups: str,
    help_command: Optional[str] = None,
    help_text: Optional[str] = None,
    allowed_task_teams: Optional[str] = None,
    is_ir_task: bool = False,
    irds_re_ranking_image: str = "",
    irds_re_ranking_command: str = "",
    irds_re_ranking_resource: str = "",
):
    """Update the task's data"""

    if allowed_task_teams:
        allowed_task_teams = "\n".join([slugify(i) for i in allowed_task_teams.split("\n")])

    return model.edit_task(
        task_id,
        task_name,
        task_description,
        featured,
        master_vm_id,
        organizer,
        website,
        require_registration,
        require_groups,
        restrict_groups,
        help_command,
        help_text,
        allowed_task_teams,
        is_ir_task,
        irds_re_ranking_image,
        irds_re_ranking_command,
        irds_re_ranking_resource,
    )


def edit_dataset(
    task_id: str,
    dataset_id: str,
    dataset_name: str,
    command: str,
    working_directory: str,
    measures: str,
    upload_name: str,
    is_confidential: bool = False,
    is_git_runner: bool = False,
    git_runner_image: Optional[str] = None,
    git_runner_command: Optional[str] = None,
    git_repository_id: Optional[str] = None,
    dataset_format: Optional[str] = None,
    description: Optional[str] = None,
    chatnoir_id: Optional[str] = None,
    ir_datasets_id: Optional[str] = None,
):
    """Update the datasets's data"""
    return model.edit_dataset(
        task_id,
        dataset_id,
        dataset_name,
        command,
        working_directory,
        measures,
        upload_name,
        is_confidential,
        is_git_runner,
        git_runner_image,
        git_runner_command,
        git_repository_id,
        dataset_format,
        description,
        chatnoir_id,
        ir_datasets_id,
    )


def delete_docker_software(task_id, vm_id, docker_software_id):
    """
    Delete a given Docker software.
    """
    return model.delete_docker_software(task_id, vm_id, docker_software_id)


def delete_software(task_id, vm_id, software_id):
    """Set the Software's deleted flag to true and prune it from the cache.
    TODO add option to truly delete the software."""
    return model.delete_software(task_id, vm_id, software_id)


def delete_run(dataset_id, vm_id, run_id):
    return model.delete_run(dataset_id, vm_id, run_id)


def delete_task(task_id: str):
    """Delete a task from the model"""
    return model.delete_task(task_id)


def delete_dataset(dataset_id: str):
    return model.delete_dataset(dataset_id)


def edit_organizer(organizer_id: str, name: str, years: str, web: str, namespace_url: str, private_token: str):
    git_integrations = []
    git_integration = model.get_git_integration(namespace_url, private_token)
    if git_integration:
        git_integrations = [git_integration]

    return model.edit_organizer(organizer_id, name, years, web, git_integrations)


def all_git_integrations(self):
    return model.all_git_integrations()


def get_git_integration(organizer_id=None, task_id=None, dataset_id=None, return_metadata_only=False):
    from django.core.cache import cache

    cache_key = f"tira-model-docker-get_git_integration-{organizer_id}-{task_id}-{dataset_id}"
    ret = cache.get(cache_key)
    if ret is not None:
        return ret if return_metadata_only else get_git_runner(ret)

    if not organizer_id and not task_id and not dataset_id:
        raise ValueError("Organizer Id or task_id must be passed. But both are none")

    if dataset_id and not organizer_id and not task_id:
        task_id = model.get_dataset(dataset_id)["task"]

    if task_id and not organizer_id:
        organizer_id = model.get_task(task_id, include_dataset_stats=False)["organizer_id"]

    if not organizer_id:
        raise ValueError(f"Organizer Id can not be None. Got {organizer_id}")

    organizer = model.get_organizer(organizer_id)
    namespace_url = organizer["gitUrlToNamespace"]

    ret = model.get_git_integration(namespace_url, "", return_dict=True, create_if_not_exists=False)
    cache.set(cache_key, ret)

    return ret if return_metadata_only else get_git_runner(ret)


# ------------------------------------------------------------
# add methods to check for existence
# ------------------------------------------------------------


def task_exists(task_id: str) -> bool:
    return model.task_exists(task_id)


def dataset_exists(dataset_id: str) -> bool:
    return model.dataset_exists(dataset_id)


def vm_exists(vm_id: str) -> bool:
    return model.vm_exists(vm_id)


def organizer_exists(organizer_id: str) -> bool:
    return model.organizer_exists(organizer_id)


def run_exists(vm_id: str, dataset_id: str, run_id: str) -> bool:
    return model.run_exists(vm_id, dataset_id, run_id)


def software_exists(task_id: str, vm_id: str, software_id: str) -> bool:
    return model.software_exists(task_id, vm_id, software_id)


def latest_output_of_software_on_dataset(
    task_id: str,
    vm_id: str,
    software_id: Optional[str],
    docker_software_id: Optional[int],
    dataset_id: str,
    upload_id: Optional[int],
):
    run_ids = model.all_matching_run_ids(vm_id, dataset_id, task_id, software_id, docker_software_id, upload_id)

    if run_ids and len(run_ids) > 0:
        return {"task_id": task_id, "vm_id": vm_id, "dataset_id": dataset_id, "run_id": run_ids[0]}
    else:
        return None


def create_re_rank_output_on_dataset(
    task_id: str,
    vm_id: str,
    software_id: str,
    docker_software_id: int,
    dataset_id: str,
    return_none_if_not_exists=False,
):
    task = get_task(task_id, False)

    is_ir_task = task.get("is_ir_task", False)
    irds_re_ranking_image = task.get("irds_re_ranking_image", "")
    irds_re_ranking_command = task.get("irds_re_ranking_command", "")
    irds_re_ranking_resource = task.get("irds_re_ranking_resource", "")

    if not is_ir_task or not irds_re_ranking_image or not irds_re_ranking_command or not irds_re_ranking_resource:
        return None
    docker_irds_software_id = str(
        int(model.get_irds_docker_software_id(task_id, vm_id, software_id, docker_software_id).docker_software_id)
    )

    reranked_job = latest_output_of_software_on_dataset(task_id, vm_id, None, docker_irds_software_id, dataset_id, None)
    if reranked_job:
        return reranked_job

    if return_none_if_not_exists:
        return None

    evaluator = model.get_evaluator(dataset_id)

    if (
        not evaluator
        or "is_git_runner" not in evaluator
        or not evaluator["is_git_runner"]
        or "git_runner_image" not in evaluator
        or not evaluator["git_runner_image"]
        or "git_runner_command" not in evaluator
        or not evaluator["git_runner_command"]
        or "git_repository_id" not in evaluator
        or not evaluator["git_repository_id"]
    ):
        return ValueError("The dataset is misconfigured. Docker-execute only available for git-evaluators")

    input_run = latest_output_of_software_on_dataset(task_id, vm_id, software_id, docker_software_id, dataset_id, None)
    path_to_run = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / vm_id / input_run["run_id"] / "output"
    rerank_run_id = input_run["run_id"] + "-rerank-" + get_tira_id()
    rerank_dir = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / vm_id / rerank_run_id

    input_run["vm_id"] = vm_id
    output_directory = tempfile.TemporaryDirectory()
    raw_command = evaluator["git_runner_command"]
    raw_command = raw_command.replace("$outputDir", "/tira-output/current-output")
    raw_command = raw_command.replace("$inputDataset", "/tira-input/current-input")

    # docker run --rm -ti --entrypoint sh -v ${PWD}:/data -v /mnt/ceph/tira/data/datasets/training-datasets/ir-benchmarks/clueweb12-trec-misinfo-2019-20240214-training/:/irds-data/:ro docker.io/webis/tira-ir-datasets-starter:0.0.56
    # export TIRA_INPUT_DATASET=/irds-data/ /irds_cli.sh --ir_datasets_id ignored --rerank /data/output-run/ --input_dataset_directory /irds-data/
    # command = [
    #    [
    #        "sudo",
    #        "podman",
    #        "--storage-opt",
    #        "mount_program=/usr/bin/fuse-overlayfs",
    #        "run",
    #        "-v",
    #        f"{output_directory}:/tira-output/current-output",
    #        "-v",
    #        f"{path_to_run}:/tira-input/current-input:ro",
    #        "--entrypoint",
    #        "sh",
    #        evaluator["git_runner_image"],
    #        "-c",
    #        raw_command,
    #    ]
    # ]

    print("Input run:", path_to_run)
    print("Rerank dir:", rerank_dir)

    rerank_dir.mkdir(parents=True, exist_ok=True)
    register_run(dataset_id, vm_id, rerank_run_id, evaluator["evaluator_id"])

    def register_reranking():
        rerank_dir.mkdir(parents=True, exist_ok=True)
        copy_tree(output_directory.name, rerank_dir / "output")
        register_run(dataset_id, vm_id, rerank_run_id, evaluator["evaluator_id"])

    # return run_cmd_as_documented_background_process(command, vm_id, task_id, 'Create Re-ranking file.',
    #                                                ['Create rerankings.'], register_reranking)


def add_input_run_id_to_all_rerank_runs():
    from tqdm import tqdm

    dataset_to_run_id = {}
    for reranking_software in tqdm(model.get_reranking_docker_softwares(), "Get input_run_ids"):
        for dataset in get_datasets_by_task(reranking_software["task_id"]):
            ls = latest_output_of_software_on_dataset(
                reranking_software["task_id"],
                reranking_software["vm_id"],
                None,
                reranking_software["docker_software_id"],
                dataset["dataset_id"],
                None,
            )

            if ls:
                if dataset["dataset_id"] in dataset_to_run_id:
                    raise ValueError("Ambigious...")

                dataset_to_run_id[dataset["dataset_id"]] = ls["run_id"]

    for i in tqdm(model.get_all_docker_software_rerankers(), "Update input ids"):
        for run in model.get_runs_for_docker_software(i["docker_software_id"]):
            if "input_run" not in run or not run["input_run"]:
                model.update_input_run_id_for_run(run["run_id"], dataset_to_run_id[run["dataset"]])


def get_all_reranking_datasets_for_task(task_id):
    return [
        {"dataset_id": k, "display_name": v["display_name"], "original_dataset_id": v["dataset_id"]}
        for k, v in get_all_reranking_datasets().items()
        if v and v["task_id"] == task_id
    ]


def get_all_reranking_datasets(force_cache_refresh=False):
    cache_key = "get_all_reranking_datasets"
    ret = cache.get(cache_key)
    if ret is not None and not force_cache_refresh:
        return ret

    ret = {}

    for reranking_software in model.get_reranking_docker_softwares():
        for dataset in get_datasets_by_task(reranking_software["task_id"]):
            reranking_input = create_re_rank_output_on_dataset(
                task_id=reranking_software["task_id"],
                vm_id=reranking_software["vm_id"],
                software_id=None,
                docker_software_id=reranking_software["docker_software_id"],
                dataset_id=dataset["dataset_id"],
                return_none_if_not_exists=True,
            )

            if reranking_input:
                name = "docker-id-" + str(reranking_software["docker_software_id"]) + "-on-" + dataset["dataset_id"]
                name = name.replace(" ", "-").replace("\\s", "-")
                reranking_input["display_name"] = reranking_software["display_name"] + " on " + dataset["dataset_id"]

                ret[name] = reranking_input

    logger.info(f"Cache refreshed for key {cache_key} ...")
    cache.set(cache_key, ret)

    return ret


def all_registrations(task_id):
    return model.all_registrations(task_id)
