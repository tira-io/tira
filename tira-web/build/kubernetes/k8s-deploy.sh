#!/bin/bash -e

echo "Apply tira deployment to kubernetes"
kubectl apply -n webisservices -f tira.yml

