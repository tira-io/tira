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
    $(basename "$0") -r webis46 my_vm User123 (remote)

Authors:
    Manuel Willem
    Anna Beyer
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
#    Creates a backup .ova file of a VM.
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -ne 2 ]; then
        logError "[tira-vm-backup] Missing arguments see:"
        usage
    fi

    vmname="$1"
    username="$2"
    timestamp=$(date +%Y-%m-%d-%H-%M-%S)

    # Check if vm is registred.
    logInfo "[tira-vm-backup] Check if VM is registered..."
    if [ "$(is_tira_vm "$vmname")" = "false" ]; then
        logError "[tira-vm-backup] Vm $vmname is not a registred virtual tira machine."
        exit 1
    fi
    logInfo "[tira-vm-backup] VM is registered."
    
    # Check if it is a vm of the given user.
    logInfo "[tira-vm-backup] Check if VM is registered for user $username."
    if [ "$(is_tira_vm_of_user "$vmname" "$username")" = "false" ]; then
        logError "[tira-vm-backup] Vm $vmname is not registred for user $username."
        exit 1
    fi
    logInfo "[tira-vm-backup] VM is registered for $username."

    backupdir="$_CONFIG_tira_nfs/backup/"
    backupfilename="${backupdir}${_CONFIG_tira_backup_name_prefix}-${username}-${timestamp}.ova"

    logInfo "[tira-vm-backup] Unsandbox $vmname..."
    tira_call vm-unsandbox "$vmname"
    logInfo "[tira-vm-backup] ...waiting..."
    sleep 5

    logInfo "[tira-vm-backup] Stop $vmname..."
    tira_call vm-stop "$vmname"
    logInfo "[tira-vm-backup] ...waiting..."
    sleep 5
    logInfo "[tira-vm-backup] Exporting $vmname..."
    VBoxManage export "$vmname" -o "$backupfilename"
    logInfo "[tira-vm-backup] VM backup done."
}

#
#    Start programm with parameters.
#
main "$@"
