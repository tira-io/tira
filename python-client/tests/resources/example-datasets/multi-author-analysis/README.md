---
configs:
- config_name: inputs
  data_files:
  - split: train
    path: "system-inputs/*/*/*"
- config_name: truths
  data_files:
  - split: train
    path: "truths/*/*"

tira_configs:
  resolve_inputs_to: "system-inputs"
  resolve_truths_to: "truths"
  baseline:
    link: https://github.com/pan-webis-de/pan-code/tree/master/clef25/multi-author-analysis/naive-baseline
    command: /predict.py --dataset $inputDataset --output $outputDir --predict 0
    format:
      name: "multi-author-writing-style-analysis-solutions"
  input_format:
    name: "multi-author-writing-style-analysis-problems"
  truth_format:
    name: "multi-author-writing-style-analysis-truths"
  evaluator:
    image: registry.webis.de/code-lib/public-images/pan24-multi-author-analysis-evaluator:latest
    command: "python3 /evaluator/evaluator.py -p ${inputRun} -t ${inputDataset} -o ${outputDir}"
---

# Multi Author Analysis Example Dataset

TODO: some description.

