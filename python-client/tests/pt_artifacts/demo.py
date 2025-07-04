import os
from pathlib import Path
import pyterrier as pt
from pyterrier.measures import *
import pyterrier_alpha as pta


dataset = pt.get_dataset("irds:vaswani") # disks45/nocr/trec-robust-2004
topics  = dataset.get_topics()
qrels   = dataset.get_qrels()


# Test piping reranker into artifact retriever --> working
# -------------------------------------------------------------------------
print("Testing reranker with artifact retriever...")
artifact_indexer = pta.Artifact.from_url("tira:vaswani/tira-ir-starter/Index (tira-ir-starter-pyterrier)")
artifact_retriever = pta.Artifact.from_url("tira:vaswani/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)")
#artifact_retriever.on_column_mismatch = "warn"
res_artifact_retriever = artifact_retriever.transform(topics)
eval_scores = pt.Evaluate(res_artifact_retriever, qrels, metrics=["map", "ndcg"])
print("BM25 Artifact retriever evaluation (BM25):", eval_scores)

bo1 = pt.rewrite.Bo1QueryExpansion(artifact_indexer)

res_rewrite = (artifact_retriever >> bo1 >> artifact_retriever).transform(topics)
eval_scores_rewrite = pt.Evaluate(res_rewrite, qrels, metrics=["map", "ndcg"])
print("BM25 Artifact retriever evaluation (BM25 + Bo1):", eval_scores_rewrite)