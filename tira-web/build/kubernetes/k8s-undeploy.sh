#!/bin/bash -e

kubectl -n webisservices delete -f tira.yml || echo "tira.yml is already deleted"

