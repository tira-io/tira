"""
p.stat().st_mtime - change time
"""
from pathlib import Path
import logging
from tira.data.HybridDatabase import HybridDatabase

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
def get_vm(vm_id: str):
    """ Returns a vm as dictionary with:

        {"vm_id", "user_password", "roles", "host", "admin_name",
        "admin_pw", "ip", "ssh", "rdp", "archived"}

    Some fields may be None.
    """
    return model.get_vm(vm_id)


def get_tasks() -> list:
    return model.get_tasks()


def get_run(dataset_id: str, vm_id: str, run_id: str, return_deleted: bool = False) -> dict:
    return model.get_run(dataset_id, vm_id, run_id, return_deleted)


def get_task(task_id: str) -> dict:
    """ Get a dict with the task data as follows:
    {"task_id", "task_name", "task_description", "organizer", "web", "year", "dataset_count",
    "software_count", "max_std_out_chars_on_test_data", "max_std_err_chars_on_test_data",
    "max_file_list_chars_on_test_data", "command_placeholder",  "command_description", "dataset_label",
    "max_std_out_chars_on_test_data_eval", "max_std_err_chars_on_test_data_eval",
    "max_file_list_chars_on_test_data_eval"}
     """
    return model.get_task(task_id)


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


def get_software_with_runs(task_id, vm_id):
    """
    Construct a dictionary that has the software as a key and as value a list of runs with that software
    Note that we order the list in such a way, that evaluations of a run are right behind that run in the list
       (based on the input_run)
    @return:
    [{"software": sw, "runs": runs_by_software.get(sw["id"]) } for sw in softwares]


    """
    return model.get_software_with_runs(task_id, vm_id)


def get_run_review(dataset_id: str, vm_id: str, run_id: str) -> dict:
    """ Retunrs a review as dict with the following keys:

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


# ------------------------------------------------------------
# add methods to add new data to the model
# ------------------------------------------------------------

def add_vm(vm_id: str, user_name: str, initial_user_password: str, ip: str, host: str, ssh: str, rdp: str):
    """ Add a new task to the database.
    This will not overwrite existing files and instead do nothing and return false
    """
    return model.add_vm(vm_id, user_name, initial_user_password, ip, host, ssh, rdp)


def create_task(task_id: str, task_name: str, task_description: str, master_vm_id: str,
                organizer: str, website: str, help_command: str = None, help_text: str = None):
    """ Add a new task to the database.
     CAUTION: This function does not do any sanity checks and will OVERWRITE existing tasks
     :returns: The new task as json as returned by get_task
     """
    return model.create_task(task_id, task_name, task_description, master_vm_id, organizer, website, help_command,
                             help_text)


def add_dataset(task_id: str, dataset_id: str, dataset_type: str, dataset_name: str) -> list:
    """ returns a list of paths of newly created datasets as string.
    """
    return model.add_dataset(task_id, dataset_id, dataset_type, dataset_name)


def add_software(task_id: str, vm_id: str):
    return model.add_software(task_id, vm_id)


def add_evaluator(vm_id: str, task_id: str, dataset_id: str, dataset_type: str, command: str,
                  working_directory: str, measures):
    return model.add_evaluator(vm_id, task_id, dataset_id, dataset_type, command, working_directory, measures)


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


def delete_software(task_id, vm_id, software_id):
    """ Set the Software's deleted flag to true and prune it from the cache.
    TODO add option to truly delete the software. """
    return model.delete_software(task_id, vm_id, software_id)


def delete_run(dataset_id, vm_id, run_id):
    return model.delete_run(dataset_id, vm_id, run_id)


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
