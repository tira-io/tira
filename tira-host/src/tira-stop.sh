#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Adrian Teschendorf, Steve Göring
#    Note: Uses parts of control-vm.sh by Anna Beyer
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
    $(basename "$0") [flags]

Description:
    Stops all VMs on a host.

Parameters:
    <vm-name>             Name of the VM

Examples:
    $(basename "$0") my_vm (local)
    $(basename "$0") -r webis46 my_vm (remote)
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
#    Define check methods for post conditional tests.
#
check_all_vm_stopped() {
    vms="$1"
    err=false
    for vmname in $vms; do
        get_vm_state "$vmname" state
        if [ "$state" = "running" ];  then
            logError "VM $vmname is running!"
            err=true
        fi
    done
    if [ "$err" = "true" ]; then
        logError "Not every vm is stopped!"
    else
        logInfo "Every vm is stopped."
    fi
}

#
#    Stops all VMs on a host.
#
main() {

    # This is a critical command so it prints a prompt.
    logInfo "This command stops all VMs on this host."
    yes_no_promt "Do you want to continue?" "Process aborted."

    # "yes" was choosen.

    # Get all names of running VMs.
    get_tira_vms vms

    # Shutdown all VMs.
    for vmname in $vms; do
        tira_call vm-stop "$vmname"
    done

    unittest && check_all_vm_stopped "$vms"
}

#
#    Start programm with parameters.
#
main "$@"
