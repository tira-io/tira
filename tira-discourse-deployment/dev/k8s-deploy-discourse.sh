#!/bin/bash

set -e

echo "Apply discourse deployment to kubernetes"
./k8s-deploy-discourse-volume.sh
kubectl apply -f discourse-dev.yml
