from typing import TYPE_CHECKING

from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ... import model as modeldb

if TYPE_CHECKING:
    from typing import Any

    from rest_framework.request import Request

# TODO: this file needs to be refactored to use ModelSerializer and ModelViewSet


@api_view(["GET"])
def topics(request: "Request", dataset_id: str) -> "Response":
    """Get topics for the specified dataset id.

    Args:
        request (Request): The request that triggered the REST API call.
        dataset_id (str): The TIRA dataset id for which the topics should be returned

    Returns:
        Response: The topics.
    """
    ret = []
    import ir_datasets

    try:
        dataset = modeldb.Dataset.objects.get(dataset_id=dataset_id)
    except Exception:
        return Response()

    if not dataset.ir_datasets_id:
        raise ValueError(f'No ir dataset id specified for TIRA dataset "{dataset_id}".')

    ir_dataset = ir_datasets.load(dataset.ir_datasets_id)
    queries_iter = ir_dataset.queries_iter()
    for q in queries_iter:
        ret += [{"qid": q.query_id, "dataset_id": dataset_id, "default_text": q.default_text()}]

    return Response(ret)


@api_view(["GET"])
def topic(request: "Request", dataset_id: str, qid: str) -> "Response":
    """Get topic for the specified dataset id.

    Args:
        request (Request): The request that triggered the REST API call.
        dataset_id (str): The TIRA dataset id for which the topic should be returned
        qid (str): The query id of the topic that should be returned

    Returns:
        Response: The topics.
    """
    ret: dict[str, Any] = {}
    import ir_datasets

    try:
        dataset = modeldb.Dataset.objects.get(dataset_id=dataset_id)

        if not dataset.ir_datasets_id:
            raise ValueError(f'No ir dataset id specified for TIRA dataset "{dataset_id}".')
    except Exception:
        return Response()

    ir_dataset = ir_datasets.load(dataset.ir_datasets_id)
    queries_iter = ir_dataset.queries_iter()
    for q in queries_iter:
        if str(q.query_id) == qid:
            ret = {"qid": qid, "dataset_id": dataset_id, "default_text": q.default_text(), "docs": {}}
            try:
                ret["description"] = q.description
                ret["narrative"] = q.narrative
            except Exception:
                pass
            return Response(ret)

    raise ValueError(f"No topic found with id {qid}.")


@api_view(["GET"])
def run_by_uuid(request: "Request", run_uuid: str) -> "Response":
    """Get meta data for the specified run.

    Args:
        request (Request): The request that triggered the REST API call.
        run_uuid (str): The UUID for the run

    Returns:
        Response: The topics.
    """
    dataset_id = "clueweb09-en-trec-web-2009-20230107-training"
    run_id = f"uuid-{run_uuid}"
    ranking = {}
    for i in range(0, 50):
        ranking[str(i)] = [{"rank": j, "score": 10 - j, "doc_id": f"doc-{j}"} for j in range(1, 11)]

    return Response({"tira_run": run_id, "dataset": dataset_id, "team": "", "run": run_id, "ranking": ranking})


endpoints = [
    path("<str:dataset_id>/topics", topics),
    path("<str:dataset_id>/topic/<str:qid>", topic),
    path("runs/<str:run_uuid>", run_by_uuid),
]
