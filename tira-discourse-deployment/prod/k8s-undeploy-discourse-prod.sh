#!/bin/bash

echo "Deleting discourse-prod.yml"
kubectl delete -f discourse-prod.yml -n webisservices || echo "discourse-prod.yml is already deleted"
