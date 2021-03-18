#!/bin/bash

if [[ $1 = "-n" ]]
then
    echo "Applying persistent volume"
    kubectl apply -f persistent-volume.yml -n $2
else
    echo "USAGE: k8s-deploy-discourse-volume.sh -n NAMESPACE"
fi
