#!/bin/bash -e

kubectl delete -n default -f tira.yml || echo "tira.yml is already deleted"

