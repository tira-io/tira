#!/bin/bash -e

POD=$(kubectl -n default get all|grep tira-bg-web-client|grep 'Running'|grep -v 'tira-web-client-2-'|head -1|awk '{print }')

if [ -z "${POD}" ]
then
	echo "I could not find the tira pod in kubernetes. Have you installed kubectl and have access credentials?"
	exit 1
fi

kubectl -n default exec -ti ${POD} -- bash -c 'cd /usr/local/share/tira/src && bash'

