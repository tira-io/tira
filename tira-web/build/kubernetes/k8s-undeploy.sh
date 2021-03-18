#!/bin/bash -e

kubectl delete -n webisservices -f tira.yml || echo "tira.yml is already deleted"

