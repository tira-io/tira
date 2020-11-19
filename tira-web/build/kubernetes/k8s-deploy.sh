#!/bin/bash -e

echo "Apply tira deployment to kubernetes"
kubectl apply -f tira.yml

