#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Manuel Willem, Steve Göring
#

#
#    Loading libaries and toolkits.
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
#    Define the usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <name>

Description:
    Stops a VM on a host.

Parameters:
    <name>             Name of the VM or username

Examples:
    $(basename "$0") my_vm (local)
    $(basename "$0") -r webis46 my_vm (remote)

Authors:
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
#    Define check methods for post conditional tests.
#
check_is_vm_stopped() {
    vmname="$1"
    get_vm_state "$vmname" state
    if [ "$state" = "running" ];  then
        logError "VM is not stopped!"
        exit 1
    fi
}

#
#    Power off the vm.
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -eq 0 ]; then
        logError "Missing arguments see:"
        usage
    fi

    sleep 10

    # Extract correct vmname from nfs.
    vmname_or_user="$1"

    vm_info=$(get_vm_info_from_tira "$vmname_or_user")
    vmname=$(echo "$vm_info" | grep "vmName" | sed "s|vmName=||g")
    if [ "$vmname" = "" ]; then
        vmname="$vmname_or_user"
    fi

    # Check if vm is a local vm, otherwise extract info and run remotly.
    if [ "$(is_tira_vm "$vmname")" = "false" ]; then
        host=$(echo "$vm_info" | grep "host=" | sed "s|host=||g")
        logTodo "check if host is not the extracted host"
        if [ "$host" != "" ]; then
            tira_call vm-stop -r "$host" "$vmname"
        else
            logError "$vmname is not a valid username/vmname."
        fi
        return
    fi

    # Every parameter is parsed and extracted: now do the job.

    # Check if vm is started.
    get_vm_state "$vmname" state

    if [ "$state" != "running" ];  then
        logWarn "VM is not running!"
        exit 1
    fi

    # Stopping VM.
    logInfo "Powering off local vm $vmname..."
    VBoxManage controlvm "$vmname" poweroff \
        || logError "Vm could not be stopped!"

    unittest && check_is_vm_stopped "$vmname"

}

#
#    Start programm with parameters.
#
main "$@"
