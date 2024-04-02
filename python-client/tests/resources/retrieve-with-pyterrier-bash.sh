#!/bin/bash

###########################################################################################
# Ensure that inputs are available
###########################################################################################

DATASET=$(tira-cli download --dataset longeval-tiny-train-20240315-training)

#As an example, could be anything else that is available
INDEX=$(tira-cli download --dataset longeval-tiny-train-20240315-training --approach 'ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)')

if [ -z "$TIRA_OUTPUT_DIR" ]; then
  echo 'Set TIRA_OUTPUT_DIR to '.', in the TIRA sandbox, the environment variable "$TIRA_OUTPUT_DIR" will be available'
  TIRA_OUTPUT_DIR='.'
fi

###########################################################################################
# Run on all inputs
###########################################################################################

JAR_FILE=$( cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
JAR_FILE="${JAR_FILE}/target/longeval24-1.0-SNAPSHOT-jar-with-dependencies.jar"

java -jar ${JAR_FILE} --input $DATASET --output $TIRA_OUTPUT_DIR --index $INDEX
