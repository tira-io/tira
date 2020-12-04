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
    Takes a snapshot of a specific VM.

Options:
    -h | --help           Display help documentation
    -r | --remote [host]  Remote control a specific host

Parameter:
    <vm-name>             Name of the VM of which you want to take a snapshot
    <snapshot-name>       Choose any name for the snapshot

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
#    Takes a snapshot of a specific vm.
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -ne 2 ]; then
        logError "Missing arguments see:"
        usage
    fi

    vmname="$1"
    snapshotname="$2"

    # Check if vm is already started.
    get_vm_state "$vmname" state

    if [ "$state" = "running" ];  then
        VBoxManage controlvm "$vmname" poweroff
        logInfo "First shutting down..."
        sleep 3
    fi

    VBoxManage snapshot "$vmname" take "$snapshotname"
    VBoxManage startvm "$vmname" --type headless
    # Immediately set guestproperty, since it is not set permanently for Ubuntu server.
    VBoxManage guestproperty set "$vmname" /VirtualBox/GuestAdd/SharedFolders/MountPrefix ""
    VBoxManage metrics setup --period 1 --samples 1 "$vmname"
}

#
#    Start programm with parameters.
#
main "$@"