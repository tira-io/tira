#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Manuel Willem, Steve Göring
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
    $(basename "$0") [flags] <vm-name> <snapshot-name>

Description:
    Recreates a VM from a snapshot.

Options:
    -h | --help           Display help documentation
    -r | --remote [host]  Remote control a specific host
Parameter:
    <vm-name>             Name of the VM of which you want to reset
    <snapshot-name>       Name of the snapshot

Examples:
    $(basename "$0") my_vm snap1 (local)
    $(basename "$0") -r webis46 my_vm snap2 (remote)

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
#    Recreates a VM from a snapshot.
#
main() {
    
    logInfo "[tira-vm-restore] Checking Parameters..."
    # Print usage screen, if wrong parameter count.
    if [ "$#" -ne 2 ]; then
        logError "[tira-vm-restore] Wrong argument count, see:"
        usage
    fi
    logInfo "[tira-vm-restore] Checking Parameters done."
    
    sleep 10

    logInfo "[tira-vm-restore] Get VM info and state..."
    vmname="$1"
    snapshotname="$2"

    get_vm_state "$vmname" state

    # If VM is running, shut it down.
    if [ "$state" = "running" ]; then
        logInfo "[tira-vm-restore] VM is running, shutting down now..."
        tira_call vm-stop "$vmname"
        sleep 3
    fi
    logInfo "[tira-vm-restore] Get VM info and state done."
    
    logInfo "[tira-vm-restore] Restoring VM from snapshot..."
    VBoxManage snapshot "$vmname" restore "$snapshotname"
    logInfo "[tira-vm-restore] Restored VM from snapshot."
    
    logInfo "[tira-vm-restore] Starting restored VM..."
    tira_call vm-start "$vmname"
    logInfo "[tira-vm-restore] Started restored VM."
}

#
#    Start programm with parameters.
#
main "$@"
