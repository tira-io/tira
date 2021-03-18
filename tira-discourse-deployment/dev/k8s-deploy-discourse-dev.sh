#!/bin/bash

set -e

if [[ $1 = "-n" ]]
then
    echo "Apply discourse deployment to kubernetes"
    ./k8s-deploy-discourse-volume.sh -n $2
    kubectl apply -f discourse-dev.yml -n $2
else
    echo "USAGE: k8s-deploy-discourse.sh -n NAMESPACE"
fi
