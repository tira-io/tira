#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
_BASHHELPER="included"
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="kubectl grep"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags]

Description: Run the specified command within a complete tira environment

Examples:
    $(basename "$0") bash"
    exit 1
}

POD=$(kubectl -n webisservices get all|grep tira-bg-web-client|grep 'Running'|grep -v 'tira-web-client-2-'|head -1|awk '{print $1}')

if [ -z "${POD}" ]
then
	echo "I could not find the tira pod in kubernetes. Have you installed kubectl and have access credentials?"
	exit 1
fi

INTERNAL_CMD="${@}"
kubectl -n webisservices exec -ti ${POD} -- bash -c "cd /usr/local/share/tira/src && ${INTERNAL_CMD}"

