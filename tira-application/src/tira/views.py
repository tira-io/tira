from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
import logging

from .grpc_client import GrpcClient
from .tira_model import FileDatabase
from .tira_data import get_run_runtime, get_run_file_list, get_stderr, get_stdout
from .authentication import Authentication
from .checks import Check
from .forms import *
from django.core.exceptions import PermissionDenied
from . import endpoints
from pathlib import Path
from shutil import move

model = FileDatabase()
include_navigation = True if settings.DEPLOYMENT == "legacy" else False
auth = Authentication(authentication_source=settings.DEPLOYMENT,
                      users_file=settings.LEGACY_USER_FILE)
check = Check(model, auth)

logger = logging.getLogger("tira")
logger.info("Views: Logger active")


def index(request):
    check.has_access(request, "any")

    uid = auth.get_user_id(request)
    context = {
        "include_navigation": include_navigation,
        "tasks": model.get_tasks(),
        "user_id": uid,
        "vm_id": auth.get_vm_id(request, uid),
        "role": auth.get_role(request, user_id=uid)
    }
    return render(request, 'tira/index.html', context)


def admin(request):
    check.has_access(request, ["tira", "admin"])

    context = {
        "include_navigation": include_navigation,
        "vm_list": model.get_vm_list(),
        "host_list": model.get_host_list(),
        "ova_list": model.get_ova_list(),
        "create_vm_form": CreateVmForm(),
        "archive_vm_form": ArchiveVmForm(),
        "create_task_form": CreateTaskForm(),
        "add_dataset_form": AddDatasetForm(),
        "modify_vm_form": ModifyVmForm()
    }
    return render(request, 'tira/tira_admin.html', context)


def login(request):
    """ Hand out the login form
    Note that this is only called in legacy deployment. Disraptor is supposed to catch the route to /login
    """
    check.has_access(request, 'any')

    context = {
        "include_navigation": include_navigation,
        "role": auth.get_role(request)
    }
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            # read form data, do auth.login(request, user_id, password)
            valid = auth.login(request, user_id=form.cleaned_data["user_id"], password=form.cleaned_data["password"])
            if valid:
                return redirect('tira:index')
            else:
                context["form_error"] = "Login Invalid"
    else:
        form = LoginForm()

    context["form"] = form
    return render(request, 'tira/login.html', context)


def logout(request):
    check.has_access(request, 'any')

    auth.logout(request)
    return redirect('tira:index')


def task_detail(request, task_id):
    check.has_access(request, 'any')

    uid = auth.get_user_id(request)
    context = {
        "include_navigation": include_navigation,
        "vm_id": auth.get_vm_id(request, uid),
        "role": auth.get_role(request, uid),
        "task": model.get_task(task_id),
        "tasks": model.get_datasets_by_task(task_id)
    }
    return render(request, 'tira/task_detail.html', context)


def dataset_list(request):
    check.has_access(request, 'any')

    context = {
        "include_navigation": include_navigation,
        "role": auth.get_role(request),
        "datasets": model.get_datasets()
    }
    return render(request, 'tira/dataset_list.html', context)


def dataset_detail(request, task_id, dataset_id):
    """ The dataset view. Users, it shows only the public leaderboard right now.
    Admins, it shows all evaluations on the dataset, as well as a list of all runs and the review interface.
     @note maybe later, we can show a consolidated view of all runs the user made on this dataset below.
     """
    check.has_access(request, 'any')

    role = auth.get_role(request, auth.get_user_id(request))

    # For all users: compile the results table from the evaluations
    vm_ids = model.get_vms_by_dataset(dataset_id)
    vm_evaluations = {vm_id: model.get_vm_evaluations_by_dataset(dataset_id, vm_id,
                                                                 only_public_results=False if role == 'admin' else True)
                      for vm_id in vm_ids}
    # This enforces an order to the measures, since they differ between datasets and are rendered dynamically
    keys = set()
    for e1 in vm_evaluations.values():
        for e2 in e1.values():
            keys.update(e2.keys())
    ev_keys = list(keys)

    evaluations = [{"vm_id": vm_id,
                    "run_id": run_id,
                    "measures": [measures[k] for k in ev_keys]}
                   for vm_id, measures_by_runs in vm_evaluations.items()
                   for run_id, measures in measures_by_runs.items()]

    # If an admin views the page, we also show all runs
    vms = None
    if role == 'admin':
        vm_runs = {vm_id: model.get_vm_runs_by_dataset(dataset_id, vm_id)
                   for vm_id in vm_ids}

        vm_reviews = {vm_id: model.get_vm_reviews_by_dataset(dataset_id, vm_id)
                      for vm_id in vm_ids}  # reviews[vm_id][run_id]

        vms = []
        for vm_id, run in vm_runs.items():
            runs = []
            for r in run:
                try:
                    runs.append({"run": r, "review": vm_reviews.get(vm_id, None).get(r["run_id"], None)})
                except TypeError as e:
                    logger.error(f"dataset: {dataset_id}, vm_id: {vm_id}, run: {r}")
                    Path(f"/mnt/ceph/tira/data/runs/{dataset_id}/{vm_id}")
                    move(Path(f"/mnt/ceph/tira/data/runs/{dataset_id}/{vm_id}"),
                         Path(f"/home/tira/{dataset_id}/{vm_id}"))
                    raise TypeError(e)
            # runs = [{"run": run, "review": vm_reviews.get(vm_id, None).get(run["run_id"], None)}
            #         for run in vm_runs.get(vm_id)]
            unreviewed_count = len([1 for r in vm_reviews[vm_id].values()
                                    if not r.get("reviewer", None)])
            vms.append({"vm_id": vm_id, "runs": runs, "unreviewed_count": unreviewed_count})
        # vms = [{"vm_id": vm_id,
        #         "runs": [{"run": run, "review": vm_reviews.get(vm_id, None).get(run["run_id"], None)}
        #                  for run in vm_runs.get(vm_id)],
        #         "unreviewed_count": len([1 for r in vm_reviews[vm_id].values()
        #                                  if not r.get("reviewer", None)])
        #         } for vm_id, run in vm_runs.items()]

    context = {
        "include_navigation": include_navigation,
        "role": role,
        "dataset_id": dataset_id,
        "task": model.get_task(task_id),
        "ev_keys": ev_keys,
        "evaluations": evaluations,
        "vms": vms,
    }

    return render(request, 'tira/dataset_detail.html', context)


# def software_user(request, user_id):
#     # TODO show all tasks or datasets a user participated in. -> depends on the disraptor groups
#     return redirect('tira:index')


def software_detail(request, task_id, vm_id):
    """ render the detail of the user page: vm-stats, softwares, and runs """
    check.has_access(request, ["tira", "admin", "participant", "user"], on_vm_id=vm_id)

    # 0. Early return a dummy page, if the user has no vm assigned on this task
    # TODO should be in check. If the user has no VM, check should forward to 'request-vm'.
    #   If user has no permission on the task, should forward to task page
    if auth.get_role(request, user_id=auth.get_user_id(request), vm_id=vm_id) == auth.ROLE_USER or \
            vm_id == "no-vm-assigned":
        context = {
            "include_navigation": include_navigation,
            "task": model.get_task(task_id),
            "vm_id": "no-vm-assigned",
            "role": auth.get_role(request)
        }
        return render(request, 'tira/software.html', context)
    # 2. try to load vm, # TODO if it fails return meaningful error page :D
    try:
        softwares = model.get_software(task_id, vm_id)
        runs = model.get_vm_runs_by_task(task_id, vm_id)
    except KeyError as e:
        logger.error(e)
        logger.warning(f"tried to load vm that does not exists: {vm_id} on task {task_id}")
        return redirect('tira:software-detail', task_id=task_id, vm_id="no-vm-assigned")

    # software_keys = {sw["id"] for sw in softwares}
    # run_by_software = {swk: [r for r in runs if r["software"] == swk] for swk in software_keys}
    # get all evaluations
    evals = {r["input_run_id"]: r for r in runs if "evaluator" in r["software"]}

    software = [{
        "software": sw,
        "runs": [r for r in runs if r["software"] == sw["id"]]
    } for sw in softwares]

    # print(evals)

    # TODO evaluations do not have a software_id as 'software', but 'evaluatorXYZ'
    # code that sorts the runs in a way that runs with input_run_id follow directly after their original run
    # all_run_ids = {r["run_id"] for r in runs}
    # # dependent run: these are the run where input_run_id is the run_id of another run in the batch
    # dependent_runs = {r["run_id"] for r in runs if r["input_run_id"] in all_run_ids}
    # independent_runs = all_run_ids - dependent_runs
    # r_dependent = {r["input_run_id"]: r for r in runs if r["run_id"] in dependent_runs}
    #
    # # here we assign to each software it's runs, and to each run it's dependent runs
    # for software in softwares:
    #     runs_of_current_software = run_by_software[software["id"]]
    #     r_independent = [r for r in runs_of_current_software if r["run_id"] in independent_runs]
    #
    #     for r in r_independent:
    #         if r_dependent.get(r["run_id"], None):
    #             r.get("dependent", list()).append(r_dependent[r["run_id"]])
    #     software["results"] = r_independent

    # TODO Nikolay: this sometimes just hangs infinitely. Uncommented until fixed.
    # request tira-host for vmInfo
    # vm = model.get_vm(vm_id)
    # tira_client = GrpcClient(vm.host)
    # response_vm_info = tira_client.vm_info(vm_id)

    response_vm_info = None

    print("pass")

    context = {
        "include_navigation": include_navigation,
        "task": model.get_task(task_id),
        "vm_id": vm_id,
        "software": software,
        "responseVmInfo": response_vm_info,
    }

    return render(request, 'tira/software.html', context)


def review(request, task_id, vm_id, dataset_id, run_id):
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)
    role = auth.get_role(request, auth.get_user_id(request))

    # {'software': 'software9', 'run_id': '2021-05-19-02-51-01', 'input_run_id': 'none', 'dataset': 'pan20-authorship-verification-training-dataset2-2020-03-25', 'downloadable': True}
    # run_review: {'reviewer': '', 'noErrors': False, 'missingOutput': False, 'extraneousOutput': False, 'invalidOutput': False, 'hasErrorOutput': False, 'otherErrors': False, 'comment': '', 'hasErrors': False, 'hasWarnings': False, 'hasNoErrors': False, 'published': False, 'blinded': True}
    run = model.get_run(dataset_id, vm_id, run_id)
    run_review = model.get_run_review(dataset_id, vm_id, run_id)
    print(run_review)
    runtime = get_run_runtime(dataset_id, vm_id, run_id)
    files = get_run_file_list(dataset_id, vm_id, run_id)
    files["file_list"][0] = "$outputDir"
    stdout = get_stdout(dataset_id, vm_id, run_id)
    stderr = get_stderr(dataset_id, vm_id, run_id)
    # TODO: add reviewer form if not reviewed

    context = {
        "include_navigation": include_navigation,
        'role': role,
        "review_form": ReviewForm(initial={'no_errors': True}),
        "task_id": task_id, "dataset_id": dataset_id, "vm_id": vm_id, "run_id": run_id,
        "run": run, "review": run_review, "runtime": runtime, "files": files,
        "stdout": stdout, "stderr": stderr,
    }

    return render(request, 'tira/review.html', context)


def users(request):
    """
    List of all users and virtual machines.
    """

    context = {
        "include_navigation": include_navigation,
        "role": auth.get_role(request),
        "users": model.get_users_vms()
    }
    return render(request, 'tira/user_list.html', context)


def user_detail(request, user_id):
    """
    User-virtual machine details and management.
    """

    role = auth.get_role(request, auth.get_user_id(request))

    # response = None
    # if role == 'admin':
    #     vm = model.get_vm_by_id(user_id)
    #     grpc_client = GrpcClient(vm.host)
    #     response = grpc_client.vm_info(vm.vmName)

    context = {
        "include_navigation": include_navigation,
        "role": role,
        "user": model.get_vm(user_id),
    }

    return render(request, 'tira/user_detail.html', context)


# ------------------- ajax calls --------------------------------


def add_review(request, task_id, vm_id, dataset_id, run_id):
    """
    # 'hasErrorOutput': False,
    # 'hasErrors': False
    # 'hasWarnings': False
    # 'hasNoErrors': False
    these should be filled by the model when updating review data
    """
    check.has_access(request, ["tira", "admin"])

    context = {}

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():

            no_errors = form.cleaned_data["no_errors"]
            output_error = form.cleaned_data["output_error"]
            software_error = form.cleaned_data["software_error"]
            comment = form.cleaned_data["comment"]



            try:  # TODO how to get the reviewer name??
                # TODO implement
                # model.update_review(run_id, reviewerId, reviewDate,
                #                     noErrors, missingOutput, extraneousOutput,
                #                     invalidOutput, hasErrorOutput, otherErrors,
                #                     comment, hasErrors, hasWarnings, hasNoErrors)
                print(no_errors, output_error, software_error, comment)

                context["status"] = "success"
            except KeyError as e:
                logger.error(e)
                context["status"] = "fail"
                return JsonResponse(context)
        else:
            context["status"] = "fail"
            context["review_form_error"] = "Form Invalid (check formatting)"
            return JsonResponse(context)
    else:
        HttpResponse("Permission Denied")

    return JsonResponse(context)


def admin_reload_data(request):
    check.has_access(request, ["tira", "admin"])

    if request.method == 'GET':
        # post_id = request.GET['post_id']
        model.build_model()
        return HttpResponse("Success!")


def admin_create_vm(request):
    """ Hook for create_vm posts. Responds with json objects indicating the state of the create process. """
    check.has_access(request, ["tira", "admin"])

    context = {
        "complete": [],
        'failed': []
    }

    def parse_create_string(create_string: str):
        for line in create_string.split("\n"):
            line = line.split(",")
            yield line[0], line[1], line[2]

    if request.method == "POST":
        form = CreateVmForm(request.POST)
        if form.is_valid():
            try:
                bulk_create = list(parse_create_string(form.cleaned_data["bulk_create"]))
            except IndexError:
                context["create_vm_form_error"] = "Error Parsing input. Are all lines complete?"
                return JsonResponse(context)

            # TODO dummy code talk to Nikolay!
            # TODO check semantics downstream (vm exists, host/ova does not exist)
            # for create_command in parse_create_string(form.cleaned_data["bulk_create"]):
            #     if create_vm(*create_command):
            #         model.add_ongoing_execution(*create_command)
            return endpoints.bulk_vm_create(request, bulk_create)
            # context['bulkCommandId'] = bulk_id
        else:
            context["create_vm_form_error"] = "Form Invalid (check formatting)"
            return JsonResponse(context)
    else:
        HttpResponse("Permission Denied")

    return JsonResponse(context)


def admin_get_command_queue():
    return endpoints.get_bulk_command_status()


def admin_archive_vm():
    return None


def admin_modify_vm():
    return None


def admin_create_task(request):
    """ Create an entry in the model for the task. Use data supplied by a model.
     Return a json status message. """
    check.has_access(request, ["tira", "admin"])

    context = {}

    if request.method == "POST":
        form = CreateTaskForm(request.POST)
        if form.is_valid():
            # sanity checks
            if not check.vm_exists(form.cleaned_data["master_vm_id"]):
                context["status"] = "fail"
                context[
                    "create_task_form_error"] = f"Master VM with ID {form.cleaned_data['master_vm_id']} does not exist"
                return JsonResponse(context)

            if not check.organizer_exists(form.cleaned_data["organizer"]):
                context["status"] = "fail"
                context["create_task_form_error"] = f"Organizer with ID {form.cleaned_data['organizer']} does not exist"
                return JsonResponse(context)

            if check.task_exists(form.cleaned_data["task_id"]):
                context["status"] = "fail"
                context["create_task_form_error"] = f"Task with ID {form.cleaned_data['task_id']} already exist"
                return JsonResponse(context)

            if model.create_task(form.cleaned_data["task_id"], form.cleaned_data["task_name"],
                                 form.cleaned_data["task_description"], form.cleaned_data["master_vm_id"],
                                 form.cleaned_data["organizer"], form.cleaned_data["website"]):
                context["status"] = "success"
                context["created"] = {
                    "task_id": form.cleaned_data["task_id"], "task_name": form.cleaned_data["task_name"],
                    "task_description": form.cleaned_data["task_description"],
                    "master_vm_id": form.cleaned_data["master_vm_id"],
                    "organizer": form.cleaned_data["organizer"], "website": form.cleaned_data["website"]}
            else:
                context["status"] = "fail"
                context["create_task_form_error"] = f"Could not create {form.cleaned_data['task_id']}. Contact Admin."
                return JsonResponse(context)
        else:
            context["status"] = "fail"
            context["create_task_form_error"] = "Form Invalid (check formatting)"
            return JsonResponse(context)
    else:
        HttpResponse("Permission Denied")

    return JsonResponse(context)


def admin_add_dataset(request):
    """ Create an entry in the model for the task. Use data supplied by a model.
     Return a json status message. """
    check.has_access(request, ["tira", "admin"])

    context = {}

    if request.method == "POST":
        form = AddDatasetForm(request.POST)
        if form.is_valid():
            # TODO should be calculated from dataset_name
            dataset_id_prefix = form.cleaned_data["dataset_id_prefix"]
            dataset_name = form.cleaned_data["dataset_name"]
            master_vm_id = form.cleaned_data["master_vm_id"]
            task_id = form.cleaned_data["task_id"]
            command = form.cleaned_data["command"]
            working_directory = form.cleaned_data["working_directory"]
            measures = [line.split(',') for line in form.cleaned_data["measures"].split('\n')]

            # sanity checks
            if not check.vm_exists(master_vm_id):
                context["status"] = "fail"
                context["add_dataset_form_error"] = f"Master VM with ID {master_vm_id} does not exist"
                return JsonResponse(context)

            if not check.task_exists(task_id):
                context["status"] = "fail"
                context["add_dataset_form_error"] = f"Task with ID {task_id} does not exist"
                return JsonResponse(context)

            if check.dataset_exists(dataset_id_prefix):
                context["status"] = "fail"
                context["add_dataset_form_error"] = f"Task with ID {dataset_id_prefix} already exist"
                return JsonResponse(context)

            try:
                new_paths = []
                if form.cleaned_data["create_training"]:
                    new_paths += model.add_dataset(task_id, dataset_id_prefix, "training", dataset_name)
                    model.add_evaluator(master_vm_id, task_id, dataset_id_prefix, "training", command,
                                        working_directory, measures)

                if form.cleaned_data["create_test"]:
                    new_paths += model.add_dataset(task_id, dataset_id_prefix, "test", dataset_name)
                    model.add_evaluator(master_vm_id, task_id, dataset_id_prefix, "test", command, working_directory,
                                        measures)

                if form.cleaned_data["create_dev"]:
                    new_paths += model.add_dataset(task_id, dataset_id_prefix, "dev", dataset_name)
                    model.add_evaluator(master_vm_id, task_id, dataset_id_prefix, "dev", command, working_directory,
                                        measures)

                context["status"] = "success"
                context["created"] = {"dataset_id": dataset_id_prefix, "new_paths": new_paths}

            except KeyError as e:
                logger.error(e)
                context["status"] = "fail"
                context["create_task_form_error"] = f"Could not create {dataset_id_prefix}: {e}"
                return JsonResponse(context)
        else:
            context["status"] = "fail"
            context["create_task_form_error"] = "Form Invalid (check formatting)"
            return JsonResponse(context)
    else:
        HttpResponse("Permission Denied")

    return JsonResponse(context)
