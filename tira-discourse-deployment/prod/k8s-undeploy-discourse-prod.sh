#!/bin/bash

echo "Deleting discourse-prod.yml"
kubectl delete -f discourse-prod.yml || echo "discourse-prod.yml is already deleted"
