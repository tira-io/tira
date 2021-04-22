#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Martin Potthast, Manuel Willem, Steve Göring

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
    Deletes a VM from a host.

Options:
    -h | --help           Display help documentation
    -r | --remote [host]  Remote control a specific host

Parameters:
    <vm-name>             Name of the VM

Examples:
    $(basename "$0") my_vm (local)
    $(basename "$0") -r webis46 my_vm (remote)

Authors:
    Martin Potthast
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
#    Deletes a tira VM from a host.
#
main() {

    if [ "$#" -ne 1 ]; then
        logError "Wrong number of parameters, see:"
        exit 1
    fi

    sleep 10

    vmname="$1"

    # Check if VM exists on this host.
    get_tira_vms vms
    check=$(echo "$vms" | grep "$vmname")

    if [ "$check" = "" ]; then
        logError "No VM named \"$vmname\" exists on $(hostname)."
        exit 1
    fi

    # Check if vm is already started.
    get_vm_state "$vmname" state

    if [ "$state" = "running" ];  then
        logInfo "$vmname is still running."
        yes_no_promt "Do you really want to proceed?" "Aborting."

        VBoxManage controlvm "$vmname" poweroff
        sleep 3
    fi

    # Delete the VM and unregister it in TIRA's log files.
    VBoxManage unregistervm "$vmname" --delete
    sed -i "\|$vmname|d" "$_CONFIG_FILE_tira_vms"
    sed -i "\|$vmname|d" "$_CONFIG_FILE_tira_local_home/vms.txt"
    echo "$(hostname) $vmname $(date +%Y-%m-%d) deleted" >> "$_CONFIG_FILE_tira_vms_log"
    logInfo "VM deleted!"
}

#
#    Start programm with parameters.
#
main "$@"
