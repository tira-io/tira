#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Adrian Teschendorf, Manuel Willem, Steve Göring
#

#
#    Loading libaries and toolkits.
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
#    Define the usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0")

Description:
    Lists all TIRA hosts which are registered by the NFS server.

Options:
    -h | --help                Display help documentation

Examples:
    $(basename "$0")

Authors:
    Adrian Teschendorf
    Manuel Willem
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
#    Lists all TIRA hosts which are registered by the NFS server.
#
main() {

    # Display the hosts.txt file if the NFS server is mounted.
    if [ ! -e "$_CONFIG_FILE_tira_hosts" ]; then
        logError "no NFS server mounted!"
        exit 1
    fi
    logInfo "Registered hosts:"
    cat "$_CONFIG_FILE_tira_hosts"

}

#
#    Start programm with parameters.
#
main "$@"
