#!/bin/bash -e

echo "Apply tira deployment to kubernetes"
kubectl -n webisservices apply -f tira.yml

