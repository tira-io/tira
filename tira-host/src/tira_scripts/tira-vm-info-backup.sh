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
    $(basename "$0") [flags] <user-name>

Description:
    Backs up all metadata for a given user.

Options:
    -h | --help           Display help documentation

Parameters:
    <user-name>           Name of the user

Examples:
    $(basename "$0") User123"

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
    # Print help if no parameters supplied.
    if [ "$#" -eq 0 ]; then
        logError "Missing arguments see:"
        "$scriptPath"/tira-vm-info-backup.py --help
    fi
    #CALL PYTHON SCRIPT WITH ARGUMENTS
    "$scriptPath"/tira-vm-info-backup.py "$@"
}

#
#    Start program with parameters.
#
main "$@"