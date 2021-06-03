#!/bin/bash

echo "Deleting discourse-prod.yml"
kubectl delete -f discourse-prod.yml -n tira || echo "discourse-prod.yml is already deleted"
