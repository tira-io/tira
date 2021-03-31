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
    if [ "$#" -ne 1 ]; then
        logError "Missing arguments see:"
        usage
    fi

    username="$1"
    
    #CALL PYTHON SCRIPT WITH ARGUMENTS
    "$scriptPath"/tira-vm-info-backup.py -u "$username" -b -v
    logInfo "Done."
}

#
#    Start programm with parameters.
#
main "$@"