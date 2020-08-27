#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Adrian Teschendorf, Steve Göring
#

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="cat"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags]

Description:
    Displays information on the hosts and VMs registered on the NFS server.

Options:
    -h | --help                Display help documentation
    -r | --remote [nfs|host]   Connect to the NFS server or a registered host

Examples:
    $(basename "$0") (local)
    $(basename "$0") -r webis16 (remote)

Authors:
    Adrian Teschendorf
    Steve Göring"
    exit 1
}

#
#    Define command line arguments and parse them.
#
FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Displays information on the hosts and VMs registered on the NFS server.
#
main() {

    # Check if NFS is mounted.
    if [ ! -e "$_CONFIG_FILE_tira_vms" ] || [ ! -e "$_CONFIG_FILE_tira_hosts" ] ; then
        logError "No NFS server mounted."
        exit 1
    fi

    logInfo "Registered hosts:"
    cat "$_CONFIG_FILE_tira_hosts"
    logInfo "Registered VMs:"
    cat "$_CONFIG_FILE_tira_vms"
}

#
#    Start programm with parameters.
#
main "$@"