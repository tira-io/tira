#!/usr/local/bin/bash

###########################################################################################
# Ensure that inputs are available
###########################################################################################

DATASET=$(tira-cli download --dataset longeval-tiny-train-20240315-training)

#As an example, could be anything else that is available
INDEX=$(tira-cli download --dataset longeval-tiny-train-20240315-training --approach 'ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)')
INDEX_WITH_BLOCKS=$(tira-cli download --dataset longeval-tiny-train-20240315-training --approach 'ir-benchmarks/tira-ir-starter/PyTerrier Index with Blocks')
BM25=$(tira-cli download --dataset longeval-tiny-train-20240315-training --approach 'ir-benchmarks/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)')

if [ -z "$TIRA_OUTPUT_DIR" ]; then
  echo 'Set TIRA_OUTPUT_DIR to '.', in the TIRA sandbox, the environment variable "$TIRA_OUTPUT_DIR" will be available'
  TIRA_OUTPUT_DIR='.'
fi

###########################################################################################
# Run on all inputs
###########################################################################################

ls ${TIRA_INPUT_RUN}

echo "INDEX:"
ls ${TIRA_INPUT_RUN}/1

echo "INDEX (BLOCKS):"
ls ${TIRA_INPUT_RUN}/2

echo "bm25:"
ls ${TIRA_INPUT_RUN}/3


