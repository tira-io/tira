#!/bin/bash -e

SRC_DIR=${TIRA_EVALUATION_OUTPUT_DIR}

DIR_TO_CHANGE=$(echo ${TIRA_OUTPUT_DIR}| awk -F '/output' '{print $1}')


if [ -f "${DIR_TO_CHANGE}/job-to-execute.txt" ]; then

    git remote set-url origin "https://$(cat /etc/tira-git-credentials/GITCREDENTIALUSERNAME):$(cat /etc/tira-git-credentials/GITCREDENTIALPASSWORD)@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git"

    git remote get-url origin

    git config user.email "tira-automation@tira.io"
    git config user.name "TIRA Automation"

   TARGET_FILE="${DIR_TO_CHANGE}/job-executed-on-$(date +'%Y-%m-%d-%I-%M-%S').txt"

    echo "mv ${DIR_TO_CHANGE}/job-to-execute.txt ${TARGET_FILE}"
    mv ${DIR_TO_CHANGE}/job-to-execute.txt ${TARGET_FILE}
    git rm ${DIR_TO_CHANGE}/job-to-execute.txt
    git add ${TARGET_FILE}
    git commit -m "TIRA-Automation: software was executed and evaluated." || echo "No changes to commit"

    git push -o ci.skip origin HEAD:$CI_COMMIT_BRANCH

    echo "git fetch origin main"
    git fetch origin main

    echo "git checkout -b main origin/main"
    git checkout -b main origin/main
    
    echo "git reset --hard origin/main"
    git reset --hard origin/main
    
    echo "git merge origin/$CI_COMMIT_BRANCH"
    git merge origin/$CI_COMMIT_BRANCH
    
    echo "git push origin main -o ci.skip"
    git push origin main -o ci.skip
else
    echo "The file ${DIR_TO_CHANGE}/job-to-execute.txt does not exist, I cant change it."
fi

if [ -f "${TIRA_FINAL_EVALUATION_OUTPUT_DIR}" ]; then
    echo "${TIRA_FINAL_EVALUATION_OUTPUT_DIR} exists already. Exit."
    exit 0
fi

if [ -d "${TIRA_FINAL_EVALUATION_OUTPUT_DIR}" ]; then
    echo "${TIRA_FINAL_EVALUATION_OUTPUT_DIR} exists already. Exit."
    exit 0
fi

mkdir -p "${SRC_DIR}"
su tira
mkdir -p "${TIRA_FINAL_EVALUATION_OUTPUT_DIR}"

echo "cp -r ${SRC_DIR} ${TIRA_FINAL_EVALUATION_OUTPUT_DIR}"
cp -r ${SRC_DIR} ${TIRA_FINAL_EVALUATION_OUTPUT_DIR}

EVAL_RUN_ID=$(echo $TIRA_FINAL_EVALUATION_OUTPUT_DIR| awk -F '/' '{print ($NF)}')
python3 -c "from tira.git_integration.gitlab_integration import persist_tira_metadata_for_job; persist_tira_metadata_for_job('${TIRA_FINAL_EVALUATION_OUTPUT_DIR}', '${EVAL_RUN_ID}', 'evaluate-software-result')"

su root
echo "chown directories"
chown -R tira:tira ${TIRA_FINAL_EVALUATION_OUTPUT_DIR}
chown -R tira:tira ${TIRA_FINAL_EVALUATION_OUTPUT_DIR}/../${TIRA_RUN_ID}

echo "python3 /tira/application/src/tira/git_integration/grpc_wrapper.py --input_run_vm_id ${TIRA_VM_ID} --dataset_id ${TIRA_DATASET_ID} --run_id ${TIRA_RUN_ID} --transaction_id 1 --task confirm-run-execute"
python3 /tira/application/src/tira/git_integration/grpc_wrapper.py --input_run_vm_id ${TIRA_VM_ID} --dataset_id ${TIRA_DATASET_ID} --run_id ${TIRA_RUN_ID} --transaction_id 1 --task confirm-run-execute

echo "python3 /tira/application/src/tira/git_integration/grpc_wrapper.py --input_run_vm_id ${TIRA_VM_ID} --dataset_id ${TIRA_DATASET_ID} --run_id ${EVAL_RUN_ID} --transaction_id  ${TIRA_EVALUATOR_TRANSACTION_ID} --task confirm-run-eval"
python3 /tira/application/src/tira/git_integration/grpc_wrapper.py --input_run_vm_id ${TIRA_VM_ID} --dataset_id ${TIRA_DATASET_ID} --run_id ${EVAL_RUN_ID} --transaction_id  ${TIRA_EVALUATOR_TRANSACTION_ID} --task confirm-run-eval

env|grep 'TIRA' >> task.env

python3 -c 'from tira.git_integration.gitlab_integration import delete_branch_of_repository; delete_branch_of_repository()'

