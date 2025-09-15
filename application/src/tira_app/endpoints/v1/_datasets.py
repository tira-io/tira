import json
import tempfile
import zipfile
from hashlib import md5
from pathlib import Path
from shutil import copyfileobj
from typing import TYPE_CHECKING

import markdown
import requests
from django.conf import settings
from django.urls import path
from rest_framework import pagination
from rest_framework.permissions import AllowAny
from rest_framework.serializers import CharField, ModelSerializer, SerializerMethodField
from rest_framework_json_api.views import ModelViewSet

from ... import model as modeldb
from ... import tira_model as model
from ...data.s3 import S3Database

if TYPE_CHECKING:
    from typing import Any, Optional

# TODO: this file needs to be refactored to use ModelSerializer and ModelViewSet


class DatasetSerializer(ModelSerializer):
    id = CharField(source="dataset_id")
    mirrors = SerializerMethodField()
    default_task_name = SerializerMethodField()
    ir_datasets_id = SerializerMethodField()
    description = SerializerMethodField()
    file_listing = SerializerMethodField()
    format = SerializerMethodField()
    format_configuration = SerializerMethodField()
    evaluator = SerializerMethodField()
    truth_format_configuration = SerializerMethodField()
    truth_format = SerializerMethodField()
    trusted_eval = SerializerMethodField()

    class Meta:
        model = modeldb.Dataset
        fields = [
            "id",
            "dataset_id",
            "description",
            "default_task",
            "default_task_name",
            "display_name",
            "is_confidential",
            "is_deprecated",
            "ir_datasets_id",
            "chatnoir_id",
            "mirrors",
            "file_listing",
            "format",
            "format_configuration",
            "evaluator",
            "truth_format_configuration",
            "truth_format",
            "trusted_eval",
        ]

    def get_mirrors(self, obj):
        return mirrors_for_dataset(obj.dataset_id)

    def get_description(self, obj):
        return markdown.markdown(obj.description) if obj.description else None

    def get_default_task_name(self, obj):
        return obj.default_task.task_name if obj.default_task else None

    def get_file_listing(self, obj):
        return obj.get_file_listing()

    def get_truth_format_configuration(self, obj):
        return obj.get_truth_format_configuration()

    def get_trusted_eval(self, obj):
        return obj.get_trusted_evaluation()

    def get_truth_format(self, obj):
        return obj.get_truth_format()

    def get_format(self, obj):
        return obj.get_format()

    def get_format_configuration(self, obj):
        return obj.get_format_configuration()

    def get_ir_datasets_id(self, obj):
        if obj.ir_datasets_id and obj.ir_datasets_id_2:
            return [obj.ir_datasets_id, obj.ir_datasets_id_2]
        else:
            return obj.ir_datasets_id

    def get_evaluator(self, obj):
        if (
            obj.evaluator
            and obj.evaluator.is_git_runner
            and obj.evaluator.git_runner_image
            and obj.evaluator.git_runner_command
        ):
            return {"image": obj.evaluator.git_runner_image, "command": obj.evaluator.git_runner_command}
        else:
            return None


class _DatasetView(ModelViewSet):
    queryset = modeldb.Dataset.objects.filter(is_deprecated=False)
    serializer_class = DatasetSerializer
    pagination_class = pagination.CursorPagination
    lookup_field = "dataset_id"
    permission_classes = [AllowAny]


def load_mirrored_resource(md5_sum: str) -> "Optional[dict[str, Any]]":
    ret: Optional[dict[str, Any]] = None

    try:
        obj = modeldb.MirroredResource.objects.filter(md5_sum=md5_sum).first()
        ret = {"md5_sum": obj.md5_sum, "md5_first_kilobyte": obj.md5_first_kilobyte, "size": obj.size}
        ret["mirrors"] = {}
        ret["mirrors"] = json.loads(obj.mirrors)
    except Exception:
        pass

    return ret


def upload_mirrored_resource(zipped: Path):
    zip_bytes = Path(zipped).read_bytes()

    md5_sum = str(md5(zip_bytes).hexdigest())
    md5_first_kilobyte = str(md5(zip_bytes[:1024]).hexdigest())

    target_dir = Path(settings.TIRA_ROOT) / "data" / "mirrored-resources"
    target_dir.mkdir(exist_ok=True, parents=True)
    target_dir = target_dir / md5_sum

    existing_resource = load_mirrored_resource(md5_sum)

    if not existing_resource:
        with open(target_dir, "wb") as f_target, open(zipped, "rb") as s:
            copyfileobj(s, f_target)

    ret = modeldb.MirroredResource.objects.create(
        md5_sum=md5_sum,
        md5_first_kilobyte=md5_first_kilobyte,
        size=len(zip_bytes),
        mirrors="webis-s3",
    )

    s3_db = S3Database()
    s3_db.upload_mirrored_resource(ret)
    return ret


def upload_dataset_part_as_mirrored_resource(task_id: str, dataset_id: str, dataset_type: str) -> str:
    dataset_suffix = "" if dataset_type == "input" else "-truth"

    if dataset_id.endswith("-test"):
        dataset_prefix = "test-"
    elif dataset_id.endswith("-training"):
        dataset_prefix = "training-"
    else:
        raise ValueError(f"can not handle dataset id {dataset_id}.")

    target_directory: Path = (
        model.model.data_path / (dataset_prefix + "datasets" + dataset_suffix) / task_id / dataset_id
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        zipped = Path(tmp_dir) / f"{target_directory.stem}.zip"
        with zipfile.ZipFile(zipped, "w") as zipf:
            for f in target_directory.rglob("*"):
                zipf.write(f, arcname=f.relative_to(target_directory.parent))

        dataset = modeldb.Dataset.objects.get(dataset_id=dataset_id)
        mirror = upload_mirrored_resource(zipped)

        modeldb.DatasetHasMirroredResource.objects.create(
            dataset=dataset, mirrored_resource=mirror, resource_type=f"{dataset_type}s"
        )

        return mirror.md5_sum


def mirrors_for_dataset(dataset_id: str) -> "dict[str, dict[str, Any]]":
    ret: dict[str, dict[str, Any]] = {"truths": {}, "inputs": {}}
    for i in modeldb.DatasetHasMirroredResource.objects.filter(dataset__dataset_id=dataset_id):
        resource_type = i.resource_type
        subdirectory = i.subdirectory
        rename_to = i.rename_to
        i = load_mirrored_resource(i.mirrored_resource.md5_sum)
        if not i or not i["mirrors"] or not resource_type or resource_type not in ret:
            continue
        ret[f"{resource_type}-md5_sum"] = i["md5_sum"]
        if subdirectory:
            ret[f"{resource_type}-subdirectory"] = subdirectory
        if rename_to:
            ret[f"{resource_type}-rename_to"] = rename_to

        for k, v in i["mirrors"].items():
            ret[resource_type][k] = v

    return ret


def download_mirrored_resource(url: str, name: str):
    response = requests.get(url)

    if response.status_code != 200 or not response.ok:
        raise ValueError(f"Failed to load {url}. Response code {response.status_code}.")

    md5_sum = str(md5(response.content).hexdigest())
    md5_first_kilobyte = str(md5(response.content[:1024]).hexdigest())
    size = len(response.content)

    target_dir = Path(settings.TIRA_ROOT) / "data" / "mirrored-resources"
    target_dir.mkdir(exist_ok=True, parents=True)
    target_dir = target_dir / md5_sum

    mirrors = {}
    existing_resource = load_mirrored_resource(md5_sum)

    if not existing_resource:
        with open(target_dir, "wb") as f:
            f.write(response.content)

    if existing_resource and "mirrors" in existing_resource and existing_resource["mirrors"]:
        mirrors = existing_resource["mirrors"]

    mirrors[name] = url

    if not existing_resource:
        modeldb.MirroredResource.objects.create(
            md5_sum=md5_sum,
            md5_first_kilobyte=md5_first_kilobyte,
            size=size,
            mirrors=json.dumps(mirrors),
        )
    else:
        modeldb.MirroredResource.objects.filter(md5_sum=md5_sum).update(mirrors=json.dumps(mirrors))

    return modeldb.MirroredResource.objects.filter(md5_sum=md5_sum).first()


def add_mirrored_resource(dataset_id: str, url_inputs: str, url_truths: str, name: str):
    urls = []
    for url in [url_inputs, url_truths]:
        found = False
        for i in modeldb.DatasetHasMirroredResource.objects.filter(dataset__dataset_id=dataset_id):
            i = load_mirrored_resource(i.mirrored_resource.md5_sum)
            if not i:
                raise ValueError("could not read existing resources")
            if url_inputs in i["mirrors"].values():
                print(f"Mirrored URL {url_inputs} already exists: {i}")
                found = True
        if not found:
            urls += [url]

    dataset = modeldb.Dataset.objects.filter(dataset_id=dataset_id).first()

    for url in urls:
        resource_type = "inputs" if url == url_inputs else "truths"
        mirror = download_mirrored_resource(url, name)

        if not modeldb.DatasetHasMirroredResource.objects.filter(
            dataset=dataset, mirrored_resource=mirror, resource_type=resource_type
        ):
            modeldb.DatasetHasMirroredResource.objects.create(
                dataset=dataset, mirrored_resource=mirror, resource_type=resource_type
            )

        print(load_mirrored_resource(mirror.md5_sum))


endpoints = [
    path("", _DatasetView.as_view({"get": "list"})),
    path("all", _DatasetView.as_view({"get": "list"})),
    path("view/<str:dataset_id>", _DatasetView.as_view({"get": "retrieve"})),
]
