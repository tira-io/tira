import json
from hashlib import md5
from pathlib import Path

import requests
from django.conf import settings
from django.urls import path
from rest_framework import pagination
from rest_framework.permissions import AllowAny
from rest_framework.serializers import CharField, ModelSerializer, SerializerMethodField
from rest_framework_json_api.views import ModelViewSet

from ... import model as modeldb


class DatasetSerializer(ModelSerializer):
    id = CharField(source="dataset_id")
    mirrors = SerializerMethodField()
    default_task_name = SerializerMethodField()
    ir_datasets_id = SerializerMethodField()

    class Meta:
        model = modeldb.Dataset
        fields = [
            "id",
            "dataset_id",
            "default_task",
            "default_task_name",
            "display_name",
            "is_confidential",
            "is_deprecated",
            "ir_datasets_id",
            "chatnoir_id",
            "mirrors",
        ]

    def get_mirrors(self, obj):
        return mirrors_for_dataset(obj.dataset_id)

    def get_default_task_name(self, obj):
        return obj.default_task.task_name if obj.default_task else None

    def get_ir_datasets_id(self, obj):
        if obj.ir_datasets_id and obj.ir_datasets_id_2:
            return [obj.ir_datasets_id, obj.ir_datasets_id_2]
        else:
            return obj.ir_datasets_id


class _DatasetView(ModelViewSet):
    queryset = modeldb.Dataset.objects.all()
    serializer_class = DatasetSerializer
    pagination_class = pagination.CursorPagination
    lookup_field = "dataset_id"
    permission_classes = [AllowAny]


def load_mirrored_resource(md5_sum):
    ret = None

    try:
        obj = modeldb.MirroredResource.objects.filter(md5_sum=md5_sum).first()
        ret = {"md5_sum": obj.md5_sum, "md5_first_kilobyte": obj.md5_first_kilobyte, "size": obj.size}
        ret["mirrors"] = {}
        ret["mirrors"] = json.loads(obj.mirrors)
    except:
        pass

    return ret


def mirrors_for_dataset(dataset_id: str):
    ret = {"truths": {}, "inputs": {}}
    for i in modeldb.DatasetHasMirroredResource.objects.filter(dataset__dataset_id=dataset_id):
        resource_type = i.resource_type
        i = load_mirrored_resource(i.mirrored_resource.md5_sum)
        if not i or not i["mirrors"] or not resource_type or resource_type not in ret:
            continue

        for k, v in i["mirrors"].items():
            ret[resource_type][k] = v

    return ret


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
                md5_sum=md5_sum, md5_first_kilobyte=md5_first_kilobyte, size=size, mirrors=json.dumps(mirrors)
            )
        else:
            modeldb.MirroredResource.objects.update(md5_sum=md5_sum, mirrors=json.dumps(mirrors))

        mirror = modeldb.MirroredResource.objects.filter(md5_sum=md5_sum).first()
        if not modeldb.DatasetHasMirroredResource.objects.filter(
            dataset=dataset, mirrored_resource=mirror, resource_type=resource_type
        ):
            modeldb.DatasetHasMirroredResource.objects.create(
                dataset=dataset, mirrored_resource=mirror, resource_type=resource_type
            )

        print(load_mirrored_resource(md5_sum))


endpoints = [
    path("", _DatasetView.as_view({"get": "list"})),
    path("all", _DatasetView.as_view({"get": "list"})),
    path("view/<str:dataset_id>", _DatasetView.as_view({"get": "retrieve"})),
]
