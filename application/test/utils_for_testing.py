import gzip
import io
import os
import re
import shutil
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from django.conf import settings
from django.core.management import call_command
from django.http import HttpRequest
from django.http.request import QueryDict
from django.urls import URLPattern, URLResolver
from rest_framework.test import APIRequestFactory

import tira_app.model as modeldb
from tira_app.authentication import TrustedHeaderAuthentication
from tira_app.tira_model import model as tira_model

auth_backend = TrustedHeaderAuthentication()  # There must be a way to get this from rest_framework right?

# Used for some tests
now = datetime.now().strftime("%Y%m%d")
dataset_1 = f"dataset-1-{now}-training"
dataset_2 = f"dataset-2-{now}-test"
dataset_meta = f"meta-dataset-{now}-test"
software_non_public = "docker-software-1"
software_public = "docker-software-2"
software_with_inputs = "docker-software-with_inputs"


def set_up_tira_filesystem():
    shutil.rmtree(Path("tira-root"), ignore_errors=True)

    call_command("flush", interactive=False)

    Path("tira-root/model/virtual-machines/").mkdir(parents=True, exist_ok=True)
    Path("tira-root/model/virtual-machine-hosts").mkdir(parents=True, exist_ok=True)
    Path("tira-root/model/tasks/").mkdir(parents=True, exist_ok=True)
    Path("tira-root/model/users/").mkdir(parents=True, exist_ok=True)
    Path("tira-root/data/runs/dataset-1/example_participant/run-1").mkdir(parents=True, exist_ok=True)
    Path("tira-root/data/runs/dataset-of-organizer/example_participant/run-of-organizer").mkdir(
        parents=True, exist_ok=True
    )
    open("tira-root/model/virtual-machines/virtual-machines.txt", "w").write("")
    open("tira-root/model/virtual-machine-hosts/virtual-machine-hosts.txt", "w").write("")
    open("tira-root/model/users/users.prototext", "w").write("")


def set_up_tira_environment():
    set_up_tira_filesystem()

    tira_model.edit_organizer("organizer", "organizer", "years", "web", [])
    tira_model.edit_organizer("organizer-2", "organizer-2", "years", "web", [])
    tira_model.edit_organizer("EXAMPLE-ORGANIZER", "EXAMPLE_ORGANIZER", "years", "web", [])
    evaluator = modeldb.Evaluator.objects.update_or_create(evaluator_id="big-evaluator-for-everything")[0]
    tira_model.add_vm("master-vm-for-task-1", "user_name", "initial_user_password", "ip", "host", "123", "123")
    tira_model.add_vm("example_participant", "user_name", "initial_user_password", "ip", "host", "123", "123")
    tira_model.add_vm("participant-1", "user_name", "initial_user_password", "ip", "host", "123", "123")
    tira_model.add_vm("participant-2", "user_name", "initial_user_password", "ip", "host", "123", "123")
    tira_model.add_vm("PARTICIPANT-FOR-TEST-1", "user_name", "initial_user_password", "ip", "host", "123", "123")

    tira_model.create_task(
        "task-of-organizer-1",
        "task_name",
        "task_description",
        False,
        "master-vm-for-task-1",
        "EXAMPLE-ORGANIZER",
        "website",
        False,
        False,
        False,
        "help_command",
        "",
        "",
    )

    tira_model.create_task(
        "shared-task-1",
        "task_name",
        "task_description",
        False,
        "master-vm-for-task-1",
        "organizer",
        "website",
        False,
        False,
        False,
        "help_command",
        "",
        "",
    )

    tira_model.add_dataset("shared-task-1", "dataset-1", "training", "dataset-1", "upload-name")

    tira_model.add_dataset("shared-task-1", "dataset-2", "test", "dataset-2", "upload-name")
    tira_model.add_dataset("shared-task-1", "dataset-not-published", "training", "dataset-published", "upload-name")

    tira_model.add_dataset("shared-task-1", "meta-dataset", "test", "meta-dataset", "upload-name")
    tira_model.add_dataset(
        "task-of-organizer-1", "dataset-of-organizer", "training", "dataset-of-organizer", "upload-name"
    )

    d = modeldb.Dataset.objects.get(dataset_id=f"dataset-not-published-{now}-training")
    d.is_confidential = True
    d.save()
    del d

    d = modeldb.Dataset.objects.get(dataset_id=f"dataset-of-organizer-{now}-training")
    d.is_confidential = True
    d.save()
    del d

    tira_model.add_dataset("task-of-organizer-1", "dataset-without-a-name", "training", "", "upload-name")
    tira_model.add_software(task_id="shared-task-1", vm_id="PARTICIPANT-FOR-TEST-1")

    modeldb.DockerSoftware.objects.create(
        display_name=software_non_public,
        vm=modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1"),
        task=modeldb.Task.objects.get(task_id="shared-task-1"),
        deleted=False,
    )

    modeldb.DockerSoftware.objects.create(
        display_name=software_public,
        vm=modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1"),
        task=modeldb.Task.objects.get(task_id="shared-task-1"),
        public_image_name="some image identifier",
        deleted=False,
    )

    modeldb.DockerSoftware.objects.create(
        display_name=software_with_inputs,
        vm=modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1"),
        task=modeldb.Task.objects.get(task_id="shared-task-1"),
        deleted=False,
    )

    s1_tmp = modeldb.DockerSoftware.objects.filter(
        vm=modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1"),
        task=modeldb.Task.objects.get(task_id="shared-task-1"),
        display_name=software_with_inputs,
    )[0]

    s2_tmp = modeldb.DockerSoftware.objects.filter(
        vm=modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1"),
        task=modeldb.Task.objects.get(task_id="shared-task-1"),
        display_name=software_public,
    )[0]

    s3_tmp = modeldb.DockerSoftware.objects.filter(
        vm=modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1"),
        task=modeldb.Task.objects.get(task_id="shared-task-1"),
        display_name=software_non_public,
    )[0]

    es1 = modeldb.DockerSoftware.objects.create(
        display_name="software_e1",
        vm=modeldb.VirtualMachine.objects.get(vm_id="example_participant"),
        task=modeldb.Task.objects.get(task_id="shared-task-1"),
        deleted=False,
    )

    modeldb.DockerSoftwareHasAdditionalInput.objects.create(
        position=1, docker_software=s1_tmp, input_docker_software=s2_tmp
    )
    modeldb.DockerSoftwareHasAdditionalInput.objects.create(
        position=3, docker_software=s1_tmp, input_docker_software=s2_tmp
    )
    modeldb.DockerSoftwareHasAdditionalInput.objects.create(
        position=2, docker_software=s1_tmp, input_docker_software=s3_tmp
    )

    tira_model.add_docker_software_mounts(
        {"docker_software_id": es1.docker_software_id}, {"HF_HOME": "1", "MOUNT_HF_MODEL": "2", "HF_CACHE_SCAN": "3"}
    )

    d = modeldb.Dataset.objects.get(dataset_id=dataset_meta)
    d.meta_dataset_of = dataset_1 + "," + dataset_2
    d.save()

    k_1 = 2.0
    k_2 = 1.0

    d = modeldb.Dataset.objects.get(dataset_id=dataset_1)
    for i in range(10):

        for participant in ["example_participant", "participant-1", "participant-2"]:
            run_id = f"run-{i}-{participant}"
            Path(f"tira-root/data/runs/dataset-1/{participant}/{run_id}/").mkdir(parents=True, exist_ok=True)
            with open(f"tira-root/data/runs/dataset-1/{participant}/{run_id}/run.prototext", "w") as f:
                f.write(
                    f'\nsoftwareId: "upload"\nrunId: "{run_id}"\ninputDataset:'
                    f' "dataset-1-{now}-training"\ndownloadable: true\ndeleted: false\n'
                )

            tira_model.add_run(dataset_id="dataset-1", vm_id=participant, run_id=run_id)
            run = modeldb.Run.objects.get(run_id=run_id)
            if participant == "example_participant":
                run.docker_software = es1
                run.save()

            eval_run = modeldb.Run.objects.create(
                run_id=f"run-{i}-{participant}-eval", input_run=run, input_dataset=d, evaluator=evaluator
            )
            # SERPS of participant-1 are unblinded and published
            modeldb.Review.objects.create(
                run=eval_run,
                published=participant in {"example_participant", "participant-1"},
                blinded=participant != "participant-1",
            )

            if i > 8:
                modeldb.Review.objects.update_or_create(
                    run_id=run_id,
                    defaults={
                        "published": participant in {"example_participant", "participant-1"},
                        "blinded": participant != "participant-1",
                    },
                )

            modeldb.Evaluation.objects.create(measure_key="k-1", measure_value=k_1, run=eval_run)
            modeldb.Evaluation.objects.create(measure_key="k-2", measure_value=k_2, run=eval_run)

            k_1 -= 0.1
            k_2 += 0.1

    runs_path = Path("tira-root/data/runs/dataset-1/example_participant")
    (runs_path / "run-3-example_participant" / "output").mkdir(parents=True, exist_ok=True)
    with (runs_path / "run-3-example_participant" / "output" / "run.txt").open("w") as file:
        file.write(
            "q072210025 0 doc072207504499 1 16.214817060525405 pl2-baseline\nq072210025 0 doc072212607743 2"
            " 14.878122569655583 pl2-baseline"
        )
    (runs_path / "run-3-example_participant-eval" / "output").mkdir(parents=True, exist_ok=True)
    with (runs_path / "run-3-example_participant-eval" / "output" / ".data-top-10-for-rendering.jsonl").open(
        "w"
    ) as file:
        file.write(
            '{"queries": {"q072210025": {"qid": "q072210025","query": "recipe spring roll","original_query": {"query_id":'
            ' "q072210025","text": "recipe spring roll"}}}, "documents": {}, "qrels": {}}'
        )

    Path("tira-root/data/runs/dataset-1/example_participant/run-5-example_participant/output").mkdir(
        parents=True, exist_ok=True
    )
    open("tira-root/data/runs/dataset-1/example_participant/run-5-example_participant/output/run.txt", "w").write(
        "q072210025 0 doc072207504499 1 16.214817060525405 pl2-baseline\nq072210025 0 doc072212607743 2"
        " 14.878122569655583 pl2-baseline"
    )

    Path("tira-root/data/runs/dataset-1/example_participant/run-5-example_participant-eval/output").mkdir(
        parents=True, exist_ok=True
    )
    gzip.open(
        "tira-root/data/runs/dataset-1/example_participant/run-5-example_participant-eval/output/.data-top-10-for-rendering.jsonl.gz",
        "wt",
    ).write(
        '{"queries": {"q072210025": {"qid": "q072210025","query": "recipe spring roll","original_query": {"query_id":'
        ' "q072210025","text": "recipe spring roll"}}}, "documents": {}, "qrels": {}}'
    )

    d = modeldb.Dataset.objects.get(dataset_id=dataset_2)
    for i in range(2):
        for participant in ["participant-1", "participant-2"]:
            run_id = f"run-ds2-{i}-{participant}"
            Path(f"tira-root/data/runs/dataset-2/{participant}/{run_id}/").mkdir(parents=True, exist_ok=True)
            with open(f"tira-root/data/runs/dataset-2/{participant}/{run_id}/run.prototext", "w") as f:
                f.write(
                    f'\nsoftwareId: "upload"\nrunId: "{run_id}"\ninputDataset: "dataset-2-{now}-test"\ndownloadable:'
                    " true\ndeleted: false\n"
                )

            tira_model.add_run(dataset_id="dataset-2", vm_id=participant, run_id=run_id)
            run = modeldb.Run.objects.get(run_id=run_id)

            eval_run = modeldb.Run.objects.create(
                run_id=f"run-ds2-{i}-{participant}-eval", input_run=run, input_dataset=d, evaluator=evaluator
            )

            modeldb.Review.objects.create(run=eval_run, published=participant == "participant-1")
            modeldb.Evaluation.objects.create(measure_key="k-1", measure_value=k_1, run=eval_run)
            modeldb.Evaluation.objects.create(measure_key="k-2", measure_value=k_2, run=eval_run)

            k_1 -= 0.1
            k_2 += 0.1

    with open("tira-root/data/runs/dataset-of-organizer/example_participant/run-of-organizer/run.prototext", "w") as f:
        f.write(
            '\nsoftwareId: "upload"\nrunId: "run-of-organizer"\ninputDataset:'
            f' "dataset-of-organizer-{now}-training"\ndownloadable: true\ndeleted: false\n'
        )

    tira_model.add_run(dataset_id="dataset-of-organizer", vm_id="example_participant", run_id="run-of-organizer")


def __resolve_path(url_pattern: str, params: "Optional[dict[str, Any]]" = None) -> str:
    """
    Replaces django template variables with their value from params

    >>> __resolve_path("v1/runs/<str:run_id>/review", {"run_id": "blah"})
    /v1/runs/blah/review
    """

    def _replace_with_value(match: re.Match) -> str:
        assert params is not None, "Keys were present but no dictionary was given"
        return str(params[match.group(2)])

    return re.sub(r"<(\w+):(\w+)>", _replace_with_value, f"/{url_pattern}")


def mock_request(
    groups: str, url_pattern: str, method="GET", body: "Optional[dict]" = None, params: "Optional[dict]" = None
) -> HttpRequest:
    path = __resolve_path(url_pattern, params)
    # Stuff prefixed with HTTP_ will be added to the headers and to META otherwise
    headers = {
        "HTTP_X-Disraptor-App-Secret-Key": os.getenv("DISRAPTOR_APP_SECRET_KEY"),
        "HTTP_X-Disraptor-User": "ignored-user.",
        "HTTP_X-Disraptor-Groups": groups,
        "CSRF_COOKIE": "aasa",
    }
    factory = APIRequestFactory()
    ret = factory.generic(method=method, path=path, data=body if body is not None else "", **headers)
    assert isinstance(ret, HttpRequest)
    # These should be empty anyway from the code above but are immutable. Override to make them mutable
    ret.GET = QueryDict("", mutable=True)
    ret.POST = QueryDict("", mutable=True)
    return ret


def method_for_url_pattern(url_pattern: str):
    patterns = {f"{pre}{pat.pattern}": pat for pre, pat in get_django_url_patterns()}
    return patterns[url_pattern].callback


def route_to_test(
    url_pattern, params, group_to_expected_status_code: dict[str, int], method="GET", hide_stdout=False, body=None
):
    metadata_for_groups = {}

    for group, expected_status_code in group_to_expected_status_code.items():
        params_for_group = deepcopy({} if not params else params)
        params_for_group["request"] = mock_request(group, url_pattern, method=method, body=body, params=params)

        metadata_for_groups[group] = {"params": params_for_group, "expected_status_code": expected_status_code}

    return (url_pattern, method_for_url_pattern(url_pattern), metadata_for_groups, hide_stdout)


def execute_method_behind_url_and_return_status_code(method_bound_to_url_pattern, request, hide_stdout):
    if hide_stdout:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            ret = method_bound_to_url_pattern(**request)
    else:
        ret = method_bound_to_url_pattern(**request)

    if str(type(ret)) == "<class 'django.http.response.Http404'>":
        return 404
    return ret.status_code


def __django_url_patterns(resolver: URLResolver, prefix: str = "") -> "Iterable[tuple[str, URLPattern]]":
    """Iterates all URLPatterns resolved by the provided ``resolver`` and their URLs.

    Args:
        resolver (URLResolver): The resolver for which to fetch the urls and their associated ``URLPattern``.
        prefix (str, optional): An optional prefix to prepend to all paths. Defaults to "".

    Raises:
        TypeError: Raised if an unexpected datatype is found to be resolved by the ``URLResolver``. This error should
            not be captured since it is an internal problem.

    Returns:
        Iterable[tuple[str, URLPattern]]: An iterable of paths and the URLPattern they are resolved to.
    """
    for p in resolver.url_patterns:
        if isinstance(p, URLPattern):
            yield prefix, p
        elif isinstance(p, URLResolver):
            yield from __django_url_patterns(p, f"{prefix}{p.pattern}")
        else:
            raise TypeError(f"Unexpected entry-type in urlpatterns for {p}")


def get_django_url_patterns(
    urlpatterns: "Optional[list[Union[URLResolver, URLPattern]]]" = None,
) -> "Iterable[tuple[str, URLPattern]]":
    """Returns an iterable of all configured django endpoints.

    Args:
        urlpatterns (Optional[list[Union[URLResolver, URLPattern]]], optional): A list of the url patterns to extract
            all configured endpoints on. If None, the endpoints that are configured for django will be used. Defaults
            to None.

    Raises:
        TypeError: Raised if an unexpected datatype is found to be resolved by the ``URLResolver``. This error should
            not be captured since it is an internal problem.

    Returns:
        Iterable[tuple[str, URLPattern]]: An iterable of paths and the URLPattern they are resolved to.
    """
    if urlpatterns is None:
        urlconf = __import__(settings.ROOT_URLCONF, {}, {}, [""])
        urlpatterns = urlconf.urlpatterns
        assert isinstance(urlpatterns, list)

    for p in urlpatterns:
        if isinstance(p, URLPattern):
            yield "", p
        elif isinstance(p, URLResolver):
            yield from __django_url_patterns(p, p.pattern)
        else:
            raise TypeError(f"Unexpected entry-type in urlpatterns for {p}")


def assert_all_url_patterns_are_tested(tested_url_patterns: "Iterable[str]"):
    """
    Asserts that tested_url_patterns is identical or a superset to all the endpoints registered with django.
    """
    untested = set(f"{pre}{pat.pattern}" for pre, pat in get_django_url_patterns()).difference(tested_url_patterns)
    assert len(untested) == 0, f"{len(untested)} patterns are untested: {untested}; tested: {tested_url_patterns}"
