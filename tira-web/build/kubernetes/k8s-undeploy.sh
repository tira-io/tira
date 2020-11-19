#!/bin/bash -e

kubectl delete -f tira.yml || echo "tira.yml is already deleted"

