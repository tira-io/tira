#!/bin/bash

POD=$(kubectl get pods | grep tira-discourse | head -1 | sed "s/\s/\n/g" | head -1)

if [[ $1 = "--init" ]]
then
    kubectl logs $POD -c install-dependencies -f
else
    kubectl logs $POD -f
fi
