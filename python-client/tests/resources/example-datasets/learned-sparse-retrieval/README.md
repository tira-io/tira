---
configs:
- config_name: inputs
  data_files:
  - split: train
    path: ["corpus.jsonl.gz", "queries.jsonl"]
- config_name: truths
  data_files:
  - split: train
    path: ["qrels.txt", "queries.jsonl"]

tira_configs:
  resolve_inputs_to: "."
  resolve_truths_to: "."
  baseline:
    link: https://github.com/pan-webis-de/pan-code/tree/master/clef25/multi-author-analysis/naive-baseline
    command: /predict.py --dataset $inputDataset --output $outputDir --predict 0
    format:
      name: "multi-author-writing-style-analysis-solutions"
  input_format:
    name: "lsr-benchmark-inputs"
  truth_format:
    name: "qrels.txt"
  evaluator:
    image: registry.webis.de/code-lib/public-images/pan24-multi-author-analysis-evaluator:latest
    command: "python3 /evaluator/evaluator.py -p ${inputRun} -t ${inputDataset} -o ${outputDir}"
---

# Multi Author Analysis Example Dataset

TODO: some description.

