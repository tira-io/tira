---
configs:
- config_name: inputs
  data_files:
  - split: train
    path: ["corpus.jsonl.gz", "queries.jsonl"]
- config_name: truths
  data_files:
  - split: train
    path: ["qrels.txt", "queries.jsonl", "dataset-metadata.json", "config.json", "subsample.json"]

tira_configs:
  resolve_inputs_to: "."
  resolve_truths_to: "."
  baseline:
    link: https://github.com/reneuir/lsr-benchmark/tree/main/step-03-retrieval-approaches/pyterrier-naive
    command: /run-pyterrier.py --dataset $inputDataset --retrieval BM25 --output $outputDir
    format:
      name: ["run.txt", "lightning-ir-document-embeddings", "lightning-ir-query-embeddings"]
  input_format:
    name: "lsr-benchmark-inputs"
  truth_format:
    name: "qrels.txt"
  evaluator:
    measures: ["nDCG@10","P@10"]
---

# Multi Author Analysis Example Dataset

TODO: some description.

