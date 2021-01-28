#!/bin/bash -e

echo "Apply tira deployment to kubernetes"
kubectl apply -n default -f tira.yml

