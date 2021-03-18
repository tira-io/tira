#!/bin/bash

while [[ $# -gt 0 ]]
do
    case $1 in
        -n)
            NAMESPACE="$2"
            shift
            shift
            ;;
        --init)
            EXT="-c install-dependencies"
            shift
            ;;
        -h)
            echo "USAGE: logs.sh [--init] -n NAMESPACE"
            shift
            exit
            ;;
    esac
done

POD=$(kubectl get pods -n $NAMESPACE | grep tira-discourse | head -1 | sed "s/\s/\n/g" | head -1)

kubectl logs $POD $EXT -f -n $NAMESPACE
