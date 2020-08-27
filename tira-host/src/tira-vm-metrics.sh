#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Martin Potthast, Steve Göring
#

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/core/vboxhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="VBoxManage"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <vm-name>

Description:
    Read the metrics collected about the VM.

Options:
    -h | --help           Display help documentation
Parameters:
    <vm-name>             Name of the VM

Examples:
    $(basename "$0") my_vm (local)
    $(basename "$0") -r webis46 my_vm (remote)

Authors:
    Martin Potthast
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
#    Read metrics of a vm.
#
main() {

    if [ "$#" -eq 0 ]; then
        logError "Missing arguments see:"
        usage
    fi

    vmname="$1"

    # Every parameter is parsed and extracted: now do the job.

    # Getting metrics of VM.
    get_vm_state "$vmname" state
    if [ "$state" != "running" ]; then
        logError "VM is not running!"
        exit 1
    fi

    VBoxManage metrics query "$vmname" Guest/CPU/Load/User,Guest/RAM/Usage/Total,Guest/RAM/Usage/Free \
        || logError "Metric of $vmname could not be extracted."
}

#
#    Start programm with parameters.
#
main "$@"