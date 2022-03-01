#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author:Steve Göring
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
neededtools="ssh"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <name>

Description:
    Open RDP session to vm.

Parameters:
    <name>             Name of the VM or username

Examples:
    $(basename "$0") my_vm (local)
    $(basename "$0") -r webis46 my_vm (remote)

Authors:
    Steve Göring"
    exit 1
}

#
#    Define command line arguments and parse them.
#
DEFINE_boolean admin false 'Administration login (default false)' 'A'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Start rdp connetion to a vm.
#
main() {
    
    logInfo "[tira-vm-rdp] Checking Parameters..."
    # Print usage screen if wrong parameter count.
    if [ "$#" -eq 0 ]; then
        logError "[tira-vm-rdp] Wrong argument count, see:"
        usage
    fi
    
    logInfo "[tira-vm-rdp] Checking Parameters done."
    
    vmname_or_user="$1"

    # Every parameter is parsed and extracted: now do the job.
    logInfo "[tira-vm-rdp] Start building rdp connection to vm..."
    
    logInfo "[tira-vm-rdp] Extract vm info."
    vm_info=$(get_vm_info_from_tira "$vmname_or_user")

    if [ "$vm_info" = "" ]; then
        logError "[tira-vm-rdp] VM-Name/user $vmname_or_user is not registered. Use tira vm-list to get a list of all vms."
        exit 1
    fi
    logInfo "[tira-vm-rdp] Extracted vm info: \n$vm_info"
    
    logInfo "[tira-vm-rdp] Set rdp connection parameters."
    admin="${FLAGS_admin}"

    if [ "$admin" = "${FLAGS_TRUE}" ]; then
        user=$(echo "$vm_info" | grep "adminName=" | sed "s|adminName=||g")
        pw=$(echo "$vm_info" | grep "adminPw=" | sed "s|adminPw=||g")
        logDebug "[tira-vm-rdp] User=Administrator"
    else
        user=$(echo "$vm_info" | grep "userName=" | sed "s|userName=||g")
        pw=$(echo "$vm_info" | grep "userPw=" | sed "s|userPw=||g")
        logDebug "[tira-vm-rdp] User= $user (default)"
    fi

    port=$(echo "$vm_info" | grep "portRdp=" | sed "s|portRdp=||g")
    host=$(echo "$vm_info" | grep "host=" | sed "s|host=||g")
    logDebug "[tira-vm-rdp] with pw: $pw using port: $port on host: $host"
    logInfo "[tira-vm-rdp] Set rdp connection parameters done."
    
    logInfo "[tira-vm-rdp] Check VM state."
    # Reset vmname in order to make sure its the actual name, not just the user name.
    vmname=$(echo "$vm_info" | grep "vmName=" | sed "s|vmName=||g")
    # Check if vm is running:
    running=$(tira_call vm-info -r "$host" "$vmname" -s| grep "running")

    if [ "$running" = "" ]; then
        logError "VM $vmname is not running, therefore no rdp connection can be established."
        exit 1
    fi
    logInfo "[tira-vm-rdp] Check VM state done. VM is running."

    logInfo "[tira-vm-rdp] Establish RDP connection: user: $user host: $host password: $pw"
    rdesktop "${host}:${port}" -u "$user" -p "$pw"

}

#
#    Start programm with parameters.
#
main "$@"
