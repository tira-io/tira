#!/bin/sh

export PYTHONPATH=/tira/application/src
# Reranking via: /irds_cli.sh --input_dataset_directory $inputDataset --output_dataset_path $outputDir --rerank $inputRun

python3 /tira/application/src/manage.py ir_datasets_loader_cli ${@}

