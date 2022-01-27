#!/bin/bash

scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/core/vboxhelper.sh
. "$scriptPath"/libs/shflags

neededtools="VBoxManage"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

usage() {
    echo "
Usage:
    $(basename "$0") [flags] <vm_id> <memory> <cpus>

Description:
    This script runs vboxmanage modifyvm <vmname> --memory --cpus

Options:
    -h | --help           Display help documentation

Examples:
    $(basename "$0") pan21-master 16000 2 (local)
    $(basename "$0") -r betaweb042 pan21-master 16000 2 (remote)
    exit 1
}"

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Define check methods for post conditional tests.
#
check_is_vm_started() {
    vmname="$1"
    get_vm_state "$vmname" state
    if [ "$state" != "running" ];  then
        logError "VM is not running!"
        return "false"
    fi
    return "true"
}

#
#    Modify and then start a vm.
#
main() {
    
    logInfo "[tira-vm-modify] Checking Parameters..."
    # Print usage screen if wrong parameter count.
    if [ "$#" -ne 3 ]; then
        logError "[tira-vm-modify] Wrong argument count, see:"
        usage
    fi
    logInfo "[tira-vm-modify] Checking Parameters done."

    # Extract correct vmname from nfs.
    logInfo "[tira-vm-modify] Extract vm info."
    vmname_or_user="$1"
    mem="$2"
    cpu="$3"

    vm_info=$(get_vm_info_from_tira "$vmname_or_user")
    vmname=$(echo "$vm_info" | grep "vmName" | sed "s|vmName=||g")
    if [ "$vmname" = "" ]; then
        vmname="$vmname_or_user"
    fi

    # Check if vm is a local vm, otherwise extract info and run remotly.
    if [ "$(is_tira_vm "$vmname")" = "false" ]; then
        host=$(echo "$vm_info" | grep "host=" | sed "s|host=||g")
        curhost=$(hostname --fqdn)
        if [ "$host" != "" ] && [ "$host" != "$curhost" ] ; then
            tira_call vm-modify -r "$host" "$vmname" "$mem" "$cpu"
        else
            logError "[tira-vm-modify] $vmname is not a valid username/vmname."
        fi
        return
    fi
    logInfo "[tira-vm-modify] Extract vm info done."
    
    logInfo "[tira-vm-modify] Check vm state."
    # Check if vm is already started.
    if [ $(check_is_vm_running) = "true" ]; then
      tira vm-stop "$vmname"
      logInfo "[tira-vm-modify] $vmname is already running, stopped vm."
    fi
    logInfo "[tira-vm-modify] Check vm state done. VM is not running."

    # Starting VM.
    logInfo "[tira-vm-modify] Modifying VM $vmname with memory: $mem and cpu: $cpu..."

    VBoxManage modifyvm "$vmname" --memory "$mem" --cpus "$cpu"\
        || logError "[tira-vm-modify] VM could not be modified."
    logInfo "[tira-vm-modify] Successfully modified VM $vmname."
    
    logInfo "[tira-vm-modify] Starting VM $vmname..."
    VBoxManage startvm "$vmname" --type headless \
        || logError "[tira-vm-modify] VM could not be started after modification."
    
    logInfo "[tira-vm-modify] Check if VM is started."
    unittest && check_is_vm_started "$vmname"
}
