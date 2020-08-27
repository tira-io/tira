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
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="VBoxManage"
debug && check_tools "$neededtools"

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <vm-name>

Description:
    Takes a a screenshot of a VM and saves it to /tmp/<vm-name>.

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
#    Define check methods for post conditional tests.
#
check_is_screenshoting_done() {
    file="$1"
    if [ ! -f "$1" ]; then
        logError "$file could not be created."
        exit 1
    fi
}

#
#     Take a a screenshot.
#
main() {

    if [ "$#" -eq 0 ]; then
        logError "Missing arguments see:"
        usage
    fi

    vmname="$1"
    screenshotname="/tmp/$vmname.png"

    # Every parameter is parsed and extracted: now do the job.

    # Check if vm is running.
    get_vm_state "$vmname" state

    if [ "$state" != "running" ];  then
        logError "VM is not running!"
        exit 1
    fi

    # Take a screenshot of VM.
    logInfo "Taking screenshot of $vmname...and store as $screenshotname"
    VBoxManage controlvm "$vmname" screenshotpng "$screenshotname" \
        || logError "Could not take screenshot of vm $vmname."

    chmod g+r "$screenshotname"
    unittest && check_is_screenshoting_done "$screenshotname"
}

#
#    Start programm with parameters.
#
main "$@"