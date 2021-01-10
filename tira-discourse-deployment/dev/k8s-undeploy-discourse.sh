#!/bin/bash

set -e

#POD=$(kubectl get pods | grep tira-discourse | sed "s/\s/\n/g" | head -n 1)

#POSTMASTER_PID=$(kubectl exec -it $POD -- sudo -u postgres cat shared/postgres_data/postmaster.pid | head -1)

#kubectl exec -it $POD -- "kill $POSTMASTER_PID"
kubectl delete -f discourse-dev.yml || echo "discourse.yml is already deleted"
