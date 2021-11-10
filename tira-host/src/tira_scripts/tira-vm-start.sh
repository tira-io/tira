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
    $(basename "$0") [flags] <name>

Description:
    Starts a VM on a host.

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
check_is_vm_started() {
    vmname="$1"
    get_vm_state "$vmname" state
    if [ "$state" != "running" ];  then
        logError "VM is not running!"
        exit 1
    fi
}

#
#    Start a vm.
#
main() {
    
    logInfo "[tira-vm-start] Checking parameters..."
    # Print usage screen if wrong parameter count.
    if [ "$#" -eq 0 ]; then
        logError "[tira-vm-start] Missing arguments see:"
        usage
    fi
    logInfo "[tira-vm-start] Checking parameters done."

    sleep 10

    logInfo "[tira-vm-start] Getting vmname..."
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
        curhost=$(hostname --fqdn)
        if [ "$host" != "" ] && [ "$host" != "$curhost" ] ; then
            tira_call vm-start -r "$host" "$vmname"
        else
            logError "[tira-vm-start] $vmname is not a valid username/vmname."
        fi
        return
    fi
    
    logInfo "[tira-vm-start] Getting vmname done."
    
    logInfo "[tira-vm-start] Checking VM state..."
    # Check if vm is already started.
    get_vm_state "$vmname" state

    if [ "$state" = "running" ];  then
        logError "[tira-vm-start] VM is already running!"
        exit 1
    fi
    
    logInfo "[tira-vm-start] VM is not running."
    logInfo "[tira-vm-start] Checking VM state done."

    # Starting VM.
    logInfo "[tira-vm-start] Starting VM '$vmname'..."

    # solving "sf_" prefix problem
    # TODO "check if one guestproperty call is enough"

    VBoxManage guestproperty set "$vmname" \
        /VirtualBox/GuestAdd/SharedFolders/MountPrefix ""

    VBoxManage startvm "$vmname" --type headless \
        || logError "[tira-vm-start] Failed to start VM '$vmname'."

    # Immediately set guestproperty, since it is not
    # set permanently for Ubuntu server.
    VBoxManage guestproperty set "$vmname" \
        /VirtualBox/GuestAdd/SharedFolders/MountPrefix ""

    VBoxManage metrics setup --period 1 --samples 1 "$vmname"

    unittest && check_is_vm_started "$vmname"

    # restart dnsmasq: https://github.com/tira-io/tira9-application2/issues/8
    ssh tira@localhost -C 'sudo systemctl restart dnsmasq'
    
    logInfo "[tira-vm-start] Started VM '$vmname'."
}

#
#    Start programm with parameters.
#
main "$@"
