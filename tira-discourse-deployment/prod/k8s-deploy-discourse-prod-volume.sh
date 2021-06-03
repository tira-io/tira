#!/bin/bash

echo "Applying persistent volumes"
kubectl apply -f discourse-prod-volumes.yml -n tira
