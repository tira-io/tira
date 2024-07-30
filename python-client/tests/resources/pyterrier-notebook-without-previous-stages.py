from tira.rest_api_client import Client
from tira.third_party_integrations import ensure_pyterrier_is_loaded, persist_and_normalize_run

ensure_pyterrier_is_loaded()
import pyterrier as pt  # noqa: E402

tira = Client()
dataset_id = "longeval-tiny-train-20240315-training"
pt_dataset = pt.get_dataset(f"irds:ir-lab-padua-2024/{dataset_id}")
index = tira.pt.load_index()
bm25 = pt.BatchRetrieve(index, wmodel="BM25", verbose=True)
print("Create run")
run = bm25(pt_dataset.get_topics("title"))
print("Done, run was created")
persist_and_normalize_run(run, "bm25-default_weights")
