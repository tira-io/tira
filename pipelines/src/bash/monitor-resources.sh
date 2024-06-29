#!/usr/bin/sh

RESULTS_DIR="${1}/profiling"

if [ "$#" -ne 1 ]
then
    echo "please pass argument for output directory"
    exit 1
fi

if [ -e ${1} ]
then
    mkdir ${RESULTS_DIR}
else
    echo "Directory '${1}' does not exist"
    exit 1
fi

cat /proc/cpuinfo > ${RESULTS_DIR}/cpuinfo
cat /proc/meminfo > ${RESULTS_DIR}/meminfo
nvidia-smi &> ${RESULTS_DIR}/nvidia-smi.out

for i in $(seq 1 20)
do
    echo "DATE: $(date)" &>> ${RESULTS_DIR}/ps.log
    ps aux &>> ${RESULTS_DIR}/ps.log
    nvidia-smi -q -d UTILIZATION,MEMORY &>> ${RESULTS_DIR}/nvidia-smi.log
    sleep 3
done

for i in $(seq 1 60)
do
    echo "DATE: $(date)" &>> ${RESULTS_DIR}/ps.log
    echo ps aux &>> ${RESULTS_DIR}/ps.log
    nvidia-smi -q -d UTILIZATION,MEMORY &>> ${RESULTS_DIR}/nvidia-smi.log
    sleep 30
done

while :
do
    echo "DATE: $(date)" &>> ${RESULTS_DIR}/ps.log
    echo ps aux &>> ${RESULTS_DIR}/ps.log
    nvidia-smi -q -d UTILIZATION,MEMORY &>> ${RESULTS_DIR}/nvidia-smi.log
    sleep 60
done

