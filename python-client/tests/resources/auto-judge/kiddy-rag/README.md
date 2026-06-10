---
configs:
- config_name: inputs
  data_files:
  - split: train
    path: ["runs/*/*.jsonl", "topics/*.jsonl"]
- config_name: truths
  data_files:
  - split: train
    path: ["eval/kiddie_fake.eval.ir_measures.txt"]

tira_configs:
  resolve_inputs_to: "."
  resolve_truths_to: "."
  baseline:
    link: https://github.com/trec-auto-judge/auto-judge-starter-kit/tree/main/
    command: auto-judge run --workflow /auto-judge/judges/naive/workflow.yml --rag-responses $inputDataset/runs/*/ --rag-topics $inputDataset/topics/*.jsonl --out-dir $outputDir
    file: judges/naive/Dockerfile
    format:
      name: ["trec-eval-leaderboard"]
  input_format:
    name: "trec-rag-runs"
  truth_format:
    name: "trec-eval-leaderboard"
  evaluator:
    image: ghcr.io/trec-auto-judge/auto-judge-code/cli:0.0.2
    command: trec-auto-judge evaluate --input ${inputRun}/*eval.txt --aggregate --output ${outputDir}/evaluation.prototext
---

# Minimal Spot Check Dataset: Kiddy

This is a minimal spot-check dataset (inspired by the [rag-run-validator](https://github.com/hltcoe/rag-run-validator)) that we use to showcase inputs, outputs, and evaluations with a minimal example. 

A complete dataset (our current work-in-progress definition) has a structure like:

```
├── eval
│   └── kiddie_fake.eval.ir_measures.txt
├── runs
│   └── repgen
│       ├── run1.jsonl
│       ├── run2.jsonl
│       ├── run3.jsonl
│       └── run4.jsonl
└── topics
    └── kiddie-topics.jsonl
```

Where all files in the `runs` directory are TREC RAG run files and the `kiddie_fake.eval.ir_measures.txt` file contains the ground-truth leaderboard in a format congruent to `trec_eval -q` outputs.

Only `runs` are available to LLM-Judges, whereas the final evaluation also has access to the `trec-leaberboard` ground-truth leaderboard file.

# Admin Section

Submit to TIRA via:

```
tira-cli dataset-submission --path kiddie --task trec-auto-judge --split train --dry-run
```
