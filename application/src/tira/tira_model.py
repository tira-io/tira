"""
p.stat().st_mtime - change time
"""
from pathlib import Path
import logging
from tira.data.HybridDatabase import HybridDatabase
from django.core.cache import cache
from tira.git_runner import get_git_runner
import randomname
from django.conf import settings
from django.db import connections, router
import datetime
from tira.authentication import auth
from tira.util import get_tira_id

logger = logging.getLogger("tira")

model = HybridDatabase()


# reloading and reindexing
def build_model():
    """ reconstruct the caches and the database. """
    model.build_model()


def reload_vms():
    """ reload VM and user data from the export format of the model """
    model.reload_vms()


def reload_datasets():
    """ reload dataset data from the export format of the model """
    model.reload_datasets()


def reload_tasks():
    """ reload task data from the export format of the model """
    model.reload_tasks()


def reload_runs(vm_id):
    """ reload run data for a VM from the export format of the model """
    model.reload_runs(vm_id)


# get methods are the public interface.
def get_vm(vm_id: str, create_if_none=False):
    """ Returns a vm as dictionary with:

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
    """ Get a dict with the task data as follows:
    {"task_id", "task_name", "task_description", "organizer", "web", "year", "dataset_count",
    "software_count", "max_std_out_chars_on_test_data", "max_std_err_chars_on_test_data",
    "max_file_list_chars_on_test_data", "command_placeholder",  "command_description", "dataset_label",
    "max_std_out_chars_on_test_data_eval", "max_std_err_chars_on_test_data_eval",
    "max_file_list_chars_on_test_data_eval"}
     """
    return model.get_task(task_id, include_dataset_stats)


def get_dataset(dataset_id: str) -> dict:
    """ Return a Dataset as dict with the keys:

        {"display_name", "evaluator_id", "dataset_id", "is_confidential", "is_deprecated", "year",
        "task".task_id, 'organizer', "software_count"}
     """
    return model.get_dataset(dataset_id)


def get_datasets() -> dict:
    """ Get a dict of dataset_id: dataset_json_descriptor """
    return model.get_datasets()


def get_datasets_by_task(task_id: str, include_deprecated=False) -> list:
    """ return the list of datasets associated with this task_id
    @param task_id: id string of the task the dataset belongs to
    @param include_deprecated: Default False. If True, also returns datasets marked as deprecated.
    @return: a list of json-formatted datasets, as returned by get_dataset
    """
    return model.get_datasets_by_task(task_id, include_deprecated)


def load_refresh_timestamp_for_cache_key(cache, key):
    try:
        db = router.db_for_read(cache.cache_model_class)
        connection = connections[db]
        quote_name = connection.ops.quote_name

        with connection.cursor() as cursor:
            cursor.execute("SELECT %s FROM %s WHERE %s = '%s'" % (
                    quote_name("expires"),
                    quote_name(cache._table),
                    quote_name("cache_key"),
                    cache.make_and_validate_key(key),
                )
            )

            ret = cursor.fetchall()
            if len(ret) > 0:
                return ret[0][0] - datetime.timedelta(seconds=settings.CACHES['default']['TIMEOUT'])
    except:
        return datetime.datetime.now()


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
    docker_images = [i for i in git_runner.docker_images_in_user_repository(vm_id, cache, force_cache_refresh) if '-tira-docker-software-id-' not in i['image']]
    last_refresh = load_refresh_timestamp_for_cache_key(cache, 'docker-images-in-user-repository-tira-user-' + vm_id)

    return {
        "docker_images": docker_images,
        "docker_softwares": model.get_docker_softwares_with_runs(task_id, vm_id),
        "resources": list(settings.GIT_CI_AVAILABLE_RESOURCES.values()),
        "docker_software_help": git_runner.help_on_uploading_docker_image(vm_id, cache, force_cache_refresh),
        "docker_images_last_refresh": str(last_refresh),
        "task_is_an_information_retrieval_task": True if get_task(task_id, False).get('is_ir_task', False) else False,
        "docker_images_next_refresh": str(None if last_refresh is None else (last_refresh + datetime.timedelta(seconds=60))),
    }


def git_pipeline_is_enabled_for_task(task_id, cache, force_cache_refresh=False):
    evaluators_for_task = get_evaluators_for_task(task_id, cache, force_cache_refresh)
    git_runners_for_task = [i['is_git_runner'] for i in evaluators_for_task]
        
    # We enable the docker part only if all evaluators use the docker variant.
    return len(git_runners_for_task) > 0 and all(i for i in git_runners_for_task)


def get_evaluators_for_task(task_id, cache, force_cache_refresh=False):
    cache_key = 'get-evaluators-for-task-' + str(task_id)
    ret = cache.get(cache_key)       
    if ret is not None and not force_cache_refresh:
        return ret
        
    datasets = get_datasets_by_task(task_id)
    
    try:
        ret = [get_evaluator(i['dataset_id']) for i in datasets]
    except:
        ret = []

    logger.info(f"Cache refreshed for key {cache_key} ...")
    cache.set(cache_key, ret)
    
    return ret           

def get_docker_software(docker_software_id: int) -> dict:
    """
    Return the docker software as dict with keys:
    
    {'docker_software_id', 'display_name', 'user_image_name', 'command', 'tira_image_name', 'task_id', vm_id'}
    """ 
    return model.get_docker_software(docker_software_id)


def get_organizer(organizer_id: str):
    # TODO should return as dict
    return model.get_organizer(organizer_id)


def get_host_list() -> list:
    return model.get_host_list()


def get_ova_list() -> list:
    return model.get_ova_list()


def get_organizer_list() -> list:
    return model.get_organizer_list()


def get_vm_list():
    """ load the vm-info file which stores all active vms as such:
    <hostname>\t<vm_id>[\t<state>]\n
    ...

    returns a list of tuples (hostname, vm_id, state)
    """
    return model.get_vm_list()


def get_vms_by_dataset(dataset_id: str) -> list:
    """ return a list of vm_id's that have runs on this dataset """
    return model.get_vms_by_dataset(dataset_id)


def get_vm_runs_by_dataset(dataset_id: str, vm_id: str, return_deleted: bool = False) -> list:
    return model.get_vm_runs_by_dataset(dataset_id, vm_id, return_deleted)


def get_vm_runs_by_task(task_id: str, vm_id: str, return_deleted: bool = False) -> list:
    """ returns a list of all the runs of a user over all datasets in json (as returned by _load_user_runs) """
    return model.get_vm_runs_by_task(task_id, vm_id, return_deleted)


def get_vms_with_reviews(dataset_id: str) -> list:
    """ Get a list of all vms of a given dataset. VM's are given as a dict:
     ``{vm_id: str, "runs": list of runs, unreviewed_count: int, blinded_count: int, published_count: int}``
    """
    return model.get_vms_with_reviews(dataset_id)


def get_evaluator(dataset_id, task_id=None):
    """ returns a dict containing the evaluator parameters:

    vm_id: id of the master vm running the evaluator
    host: ip or hostname of the host
    command: command to execute to run the evaluator. NOTE: contains variables the host needs to resolve
    working_dir: where to execute the command
    """
    return model.get_evaluator(dataset_id, task_id)


def get_vm_evaluations_by_dataset(dataset_id, vm_id, only_public_results=True):
    """ Return a dict of run_id: evaluation_results for the given vm on the given dataset
    @param only_public_results: only return the measures for published datasets.
    """
    return model.get_vm_evaluations_by_dataset(dataset_id, vm_id, only_public_results)


def get_evaluations_with_keys_by_dataset(dataset_id, include_unpublished=False):
    """ Get all evaluations and evaluation measures for all vms on the given dataset.

    @param dataset_id: the dataset_id as used in tira_model
    @param include_unpublished: If True, the review status (published, blinded) is included in the evaluations.

    :returns: a tuple (ev_keys, evaluation), where ev-keys is a list of keys of the evaluation measure
    and evaluation a list of evaluations and each evaluation is a dict with {vm_id: str, run_id: str, measures: list}
    """
    return model.get_evaluations_with_keys_by_dataset(dataset_id, include_unpublished)


def get_evaluation(run_id: str):
    """ Get the evaluation of this run

    @param run_id: the id of the run
    @return: a dict with {measure_key: measure_value}
    """
    return model.get_evaluation(run_id)


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


def get_docker_softwares_with_runs(task_id, vm_id):
    """
    Returns the docker softwares as dictionaries.
    """
    return model.get_docker_softwares_with_runs(task_id, vm_id)


def get_run_review(dataset_id: str, vm_id: str, run_id: str) -> dict:
    """ Returns a review as dict with the following keys:

        {"reviewer", "noErrors", "missingOutput", "extraneousOutput", "invalidOutput", "hasErrorOutput",
        "otherErrors", "comment", "hasErrors", "hasWarnings", "hasNoErrors", "published", "blinded"}

    """
    return model.get_run_review(dataset_id, vm_id, run_id)


def get_vm_reviews_by_dataset(dataset_id: str, vm_id: str) -> dict:
    return model.get_vm_reviews_by_dataset(dataset_id, vm_id)


def get_software(task_id, vm_id, software_id):
    """ Returns the software of a vm on a task in json """
    return model.get_software(task_id, vm_id, software_id)


def get_software_by_task(task_id, vm_id):
    """ Returns the software of a vm on a task in json """
    return model.get_software_by_task(task_id, vm_id)


def get_users_vms():
    """ Return the users list. """
    return model.get_users_vms()


def add_upload(task_id, vm_id):
    """" Add empty new upload"""
    return model.add_upload(task_id, vm_id)


def delete_upload(task_id, vm_id, upload_id):
    return model.delete_upload(task_id, vm_id, upload_id)

def update_upload_metadata(task_id, vm_id, upload_id, display_name, description, paper_link):
    return model.update_upload_metadata(task_id, vm_id, upload_id, display_name, description, paper_link)


def add_uploaded_run(task_id, vm_id, dataset_id, upload_id, uploaded_file):
    """ Add the uploaded file as a new result and return it """
    return model.add_uploaded_run(task_id, vm_id, dataset_id, upload_id, uploaded_file)


def update_docker_software_metadata(docker_software_id, display_name, description, paper_link, ir_re_ranker, ir_re_ranking_input):
    return model.update_docker_software_metadata(docker_software_id, display_name, description, paper_link, ir_re_ranker, ir_re_ranking_input)

def add_docker_software(task_id, vm_id, image, command, input=None):
    """ Add the docker software to the user of the vm and return it """
    
    image, old_tag = image.split(':')
    new_tag = old_tag + '-tira-docker-software-id-' + randomname.get_name().lower()
    
    tira_image_name = get_git_integration(task_id=task_id).add_new_tag_to_docker_image_repository(image, old_tag, new_tag)

    input_docker_job, input_upload = input, None
    if 'upload' in input:
        input_docker_job, input_upload = None, input.split('-')[-1]

    return model.add_docker_software(task_id, vm_id, image + ':' + old_tag, command, tira_image_name, input_docker_job, input_upload)


def add_registration(data):
    model.add_registration(data)


def all_allowed_task_teams(task_id):
    task = get_task(task_id)
    return set([i.strip() for i in task['allowed_task_teams'].split() if i.strip()])


def user_is_registered(task_id, request):
    task = get_task(task_id)
    allowed_task_teams = all_allowed_task_teams(task_id)
    user_vm_ids = [i.strip() for i in auth.get_vm_ids(request) if i.strip()]

    return user_vm_ids is not None and len(user_vm_ids) > 0 and (len(allowed_task_teams) == 0 or any([i in allowed_task_teams for i in user_vm_ids]))


def remaining_team_names(task_id):
    already_used_teams = model.all_registered_teams()
    allowed_task_teams = sorted(list(all_allowed_task_teams(task_id)))
    return [i for i in allowed_task_teams if i not in already_used_teams]


# ------------------------------------------------------------
# add methods to add new data to the model
# ------------------------------------------------------------

def add_vm(vm_id: str, user_name: str, initial_user_password: str, ip: str, host: str, ssh: str, rdp: str):
    """ Add a new task to the database.
    This will not overwrite existing files and instead do nothing and return false
    """
    return model.add_vm(vm_id, user_name, initial_user_password, ip, host, ssh, rdp)


def create_task(task_id: str, task_name: str, task_description: str, featured: bool, master_vm_id: str,
                organizer: str, website: str, require_registration: bool, require_groups: bool, restrict_groups: bool,
                help_command: str = None, help_text: str = None, allowed_task_teams: str = None):
    """ Add a new task to the database.
     CAUTION: This function does not do any sanity checks and will OVERWRITE existing tasks
     :returns: The new task as json as returned by get_task
     """
    return model.create_task(task_id, task_name, task_description, featured, master_vm_id, organizer, website,
                             require_registration, require_groups, restrict_groups, help_command, help_text, allowed_task_teams)


def add_dataset(task_id: str, dataset_id: str, dataset_type: str, dataset_name: str, upload_name: str, irds_docker_image: str=None, irds_import_command: str=None, irds_import_truth_command: str=None) -> list:
    """ returns a list of paths of newly created datasets as string.
    """
    return model.add_dataset(task_id, dataset_id, dataset_type, dataset_name, upload_name, irds_docker_image= irds_docker_image, irds_import_command=irds_import_command, irds_import_truth_command=irds_import_truth_command)


def add_software(task_id: str, vm_id: str):
    return model.add_software(task_id, vm_id)


def add_evaluator(vm_id: str, task_id: str, dataset_id: str, command: str, working_directory: str, measures,
                  is_git_runner: bool = False, git_runner_image: str = None, git_runner_command: str = None,
                  git_repository_id: str = None):
    ret = model.add_evaluator(vm_id, task_id, dataset_id, command, working_directory, measures, is_git_runner,
                               git_runner_image, git_runner_command, git_repository_id)

    from django.core.cache import cache
    get_evaluators_for_task(task_id=task_id, cache=cache, force_cache_refresh=True)

    return ret


def add_run(dataset_id, vm_id, run_id):
    """ Add a new run to the model. Currently, this initiates the caching on the application side of things. """
    return model.add_run(dataset_id, vm_id, run_id)


def update_review(dataset_id, vm_id, run_id,
                  reviewer_id: str = None, review_date: str = None, has_errors: bool = None,
                  has_no_errors: bool = None, no_errors: bool = None, missing_output: bool = None,
                  extraneous_output: bool = None, invalid_output: bool = None, has_error_output: bool = None,
                  other_errors: bool = None, comment: str = None, published: bool = None, blinded: bool = None,
                  has_warnings: bool = False):
    """ updates the review specified by dataset_id, vm_id, and run_id with the values given in the parameters.
    Required Parameters are also required in the function """
    return model.update_review(dataset_id, vm_id, run_id, reviewer_id, review_date, has_errors, has_no_errors,
                               no_errors, missing_output, extraneous_output, invalid_output, has_error_output,
                               other_errors, comment, published, blinded, has_warnings)


def update_run(dataset_id, vm_id, run_id, deleted: bool = None):
    """ updates the run specified by dataset_id, vm_id, and run_id with the values given in the parameters.
        Required Parameters are also required in the function """
    return model.update_run(dataset_id, vm_id, run_id, deleted)


def update_software(task_id, vm_id, software_id, command: str = None, working_directory: str = None,
                    dataset: str = None, run: str = None, deleted: bool = False):
    return model.update_software(task_id, vm_id, software_id, command, working_directory, dataset,
                                 run, deleted)


def edit_task(task_id: str, task_name: str, task_description: str, featured: bool, master_vm_id: str, organizer: str, website: str,
              require_registration: str, require_groups: str, restrict_groups: str,
              help_command: str = None, help_text: str = None, allowed_task_teams=None, is_ir_task: bool = False,
              irds_re_ranking_image: str = '', irds_re_ranking_command: str = '',
              irds_re_ranking_resource: str = ''):
    """ Update the task's data """
    return model.edit_task(task_id, task_name, task_description, featured, master_vm_id, organizer, website,
                           require_registration, require_groups, restrict_groups, help_command, help_text,
                           allowed_task_teams, is_ir_task, irds_re_ranking_image, irds_re_ranking_command,
                           irds_re_ranking_resource)


def edit_dataset(task_id: str, dataset_id: str, dataset_name: str, command: str,
                 working_directory: str, measures: str, upload_name: str, is_confidential: bool = False,
                 is_git_runner: bool = False, git_runner_image: str = None, git_runner_command: str = None,
                 git_repository_id: str = None):
    """ Update the datasets's data """
    return model.edit_dataset(task_id, dataset_id, dataset_name, command, working_directory,
                              measures, upload_name, is_confidential, is_git_runner, git_runner_image,
                              git_runner_command, git_repository_id)


def delete_docker_software(task_id, vm_id, docker_software_id):
    """
    Delete a given Docker software.
    """
    return model.delete_docker_software(task_id, vm_id, docker_software_id)


def delete_software(task_id, vm_id, software_id):
    """ Set the Software's deleted flag to true and prune it from the cache.
    TODO add option to truly delete the software. """
    return model.delete_software(task_id, vm_id, software_id)


def delete_run(dataset_id, vm_id, run_id):
    return model.delete_run(dataset_id, vm_id, run_id)


def delete_task(task_id: str):
    """ Delete a task from the model """
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
    cache_key = f'tira-model-docker-get_git_integration-{organizer_id}-{task_id}-{dataset_id}'
    ret = cache.get(cache_key)        
    if ret is not None:
        return ret if return_metadata_only else get_git_runner(ret)
    
    if not organizer_id and not task_id and not dataset_id:
        raise ValueError(f'Organizer Id or task_id must be passed. But both are none')

    if dataset_id and not organizer_id and not task_id:
        task_id = model.get_dataset(dataset_id)['task']

    if task_id and not organizer_id:
        organizer_id = model.get_task(task_id, include_dataset_stats=False)['organizer_id']

    if not organizer_id:
        raise ValueError(f'Organizer Id can not be None. Got {organizer_id}')
    
    organizer = model.get_organizer(organizer_id)
    namespace_url = organizer['gitUrlToNamespace']
    
    ret = model.get_git_integration(namespace_url, '', return_dict=True, create_if_not_exists=False)
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

def latest_output_of_software_on_dataset(task_id: str, vm_id: str, software_id: str, docker_software_id: int, dataset_id: str, upload_id: int):
    run_ids = model.all_matching_run_ids(vm_id, dataset_id, task_id, software_id, docker_software_id, upload_id)

    if run_ids and len(run_ids) > 0:
        return {
            'task_id': task_id,
            'vm_id': vm_id,
            'dataset_id': dataset_id,
            'run_id': run_ids[0]
        }
    else:
        return None


def create_re_rank_output_on_dataset(task_id: str, vm_id: str, software_id: str, docker_software_id: int,
                                     dataset_id: str, return_none_if_not_exists=False):
    task = get_task(task_id, False)

    is_ir_task = task.get("is_ir_task", False)
    irds_re_ranking_image = task.get("irds_re_ranking_image", "")
    irds_re_ranking_command = task.get("irds_re_ranking_command", "")
    irds_re_ranking_resource = task.get("irds_re_ranking_resource", "")

    if not is_ir_task or not irds_re_ranking_image or not irds_re_ranking_command or not irds_re_ranking_resource:
        return None
    docker_irds_software_id = str(int(model.get_irds_docker_software_id(task_id, vm_id, software_id, docker_software_id).docker_software_id))

    reranked_job = latest_output_of_software_on_dataset(task_id, vm_id, None, docker_irds_software_id, dataset_id, None)
    if reranked_job:
        return reranked_job

    if return_none_if_not_exists:
        return None

    evaluator = model.get_evaluator(dataset_id)

    if not evaluator or 'is_git_runner' not in evaluator or not evaluator[
        'is_git_runner'] or 'git_runner_image' not in evaluator or not evaluator[
        'git_runner_image'] or 'git_runner_command' not in evaluator or not evaluator[
        'git_runner_command'] or 'git_repository_id' not in evaluator or not evaluator['git_repository_id']:
        return ValueError("The dataset is misconfigured. Docker-execute only available for git-evaluators")

    input_run = latest_output_of_software_on_dataset(task_id, vm_id, software_id, docker_software_id, dataset_id, None)
    input_run['vm_id'] = vm_id
    git_runner = get_git_integration(task_id=task_id)


    git_runner.run_docker_software_with_git_workflow(
        task_id, dataset_id, vm_id, get_tira_id(), evaluator['git_runner_image'],
        evaluator['git_runner_command'], evaluator['git_repository_id'], evaluator['evaluator_id'],
        irds_re_ranking_image, irds_re_ranking_command,
        'docker-software-' + docker_irds_software_id, irds_re_ranking_resource,
        input_run
    )

def add_input_run_id_to_all_rerank_runs():
    from tqdm import tqdm
    dataset_to_run_id = {}
    for reranking_software in tqdm(model.get_reranking_docker_softwares(), 'Get input_run_ids'):
        for dataset in get_datasets_by_task(reranking_software['task_id']):
            ls = latest_output_of_software_on_dataset(
                reranking_software['task_id'],
                reranking_software['vm_id'],
                None,
                reranking_software['docker_software_id'],
                dataset['dataset_id'],
                None
            )
            
            if ls:
                if dataset['dataset_id'] in dataset_to_run_id:
            	    raise ValueError('Amigious...')
            
                dataset_to_run_id[dataset['dataset_id']] = ls['run_id']

    for i in tqdm(model.get_all_docker_software_rerankers(), 'Update input ids'):
        for run in model.get_runs_for_docker_software(i['docker_software_id']):
            if 'input_run' not in run or not run['input_run']:
                model.update_input_run_id_for_run(run['run_id'], dataset_to_run_id[run['dataset']])

def get_all_reranking_datasets_for_task(task_id):
    return [{'dataset_id': k, 'display_name': v['display_name'], 'original_dataset_id': v['dataset_id']} for k, v in get_all_reranking_datasets().items() if v and v['task_id'] == task_id]

def get_all_reranking_datasets(force_cache_refresh=False):
    cache_key = 'get_all_reranking_datasets'
    ret = cache.get(cache_key)
    if ret is not None and not force_cache_refresh:
        return ret

    ret = {}

    for reranking_software in model.get_reranking_docker_softwares():
        for dataset in get_datasets_by_task(reranking_software['task_id']):
            reranking_input = create_re_rank_output_on_dataset(
                task_id=reranking_software['task_id'], vm_id=reranking_software['vm_id'],
                software_id=None, docker_software_id=reranking_software['docker_software_id'],
                dataset_id=dataset['dataset_id'], return_none_if_not_exists = True)

            if reranking_input:
                name = 'docker-id-' + str(reranking_software['docker_software_id']) + '-on-' + dataset['dataset_id']
                name = name.replace(' ', '-').replace('\\s', '-')
                reranking_input['display_name'] = reranking_software['display_name'] + ' on ' + dataset['dataset_id']

                ret[name] = reranking_input

    logger.info(f"Cache refreshed for key {cache_key} ...")
    cache.set(cache_key, ret)

    return ret
