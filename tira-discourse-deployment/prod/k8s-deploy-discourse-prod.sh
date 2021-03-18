#!/bin/bash

if kubectl get secret | grep -q discourse-prod-secret
then
    echo "Applying Discourse production environment"
    ./k8s-deploy-discourse-prod-volume.sh
    kubectl apply -f discourse-prod.yml
else
    echo "Secret 'discourse-prod-secret' does not exist. Create first!"
fi
