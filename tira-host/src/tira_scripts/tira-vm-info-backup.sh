#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Manuel Willem, Anna Beyer, Steve Göring
#

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/core/vboxhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <vm-name> <user-name>

Description:
    Creates a backup .ova file of a VM.

Options:
    -h | --help           Display help documentation
    -r | --remote [host]  Remote control a specific host

Parameters:
    <vm-name>             Name of the VM
    <user-name>           Name of the user

Examples:
    $(basename "$0") my_vm User123 (local)
    $(basename "$0") -r webis46 my_vm User123 (remote)"
    
    exit 1
}

#
#    Define command line arguments and parse them.
#
FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -ne 2 ]; then
        logError "Missing arguments see:"
        usage
    fi

    vmname="$1"
    username="$2"
    timestamp=$(date +%Y-%m-%d-%H-%M-%S)

    # Check if vm is registred.
    if [ "$(is_tira_vm "$vmname")" = "false" ]; then
        logError "Vm $vmname is not a registred virtual tira machine."
        exit 1
    fi

    # Check if it is a vm of the given user.
    if [ "$(is_tira_vm_of_user "$vmname" "$username")" = "false" ]; then
        logError "Vm $vmname is not registred for user $username."
        exit 1
    fi

    
    #CALL PYTHON SCRIPT WITH ARGUMENTS
    ./tira-info-backup.py -u "$username"
    logInfo "Done."
}

#
#    Start programm with parameters.
#
main "$@"