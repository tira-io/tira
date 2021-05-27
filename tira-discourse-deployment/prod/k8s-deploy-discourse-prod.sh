#!/bin/bash

if kubectl get secret -n tira | grep -q discourse-prod-secret
then
    echo "Applying Discourse production environment"
    ./k8s-deploy-discourse-prod-volume.sh
    kubectl apply -f discourse-prod.yml -n tira
else
    echo "Secret 'discourse-prod-secret' does not exist. Create first!"
fi
