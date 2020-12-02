#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
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
neededtools="curl"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") <name>

Description:
    Create the discourse group and invite-link associated to a vm.

Parameters:
    <name>             Name of the VM or username

Examples:
    $(basename "$0") my_vm"
    exit 1
}

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Create the discourse group associated to a vm.
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -eq 0 ]; then
        logError "Missing arguments see:"
        usage
    fi

    vmname_or_user="$1"
    vm_info=$(get_vm_info_from_tira "$vmname_or_user")

    if [ "$vm_info" = "" ]; then
        logError "VM-Name/user $vmname_or_user is not registred. Use tira vm-list to get a list of all vms."
        exit 1
    fi
    logDebug "Extracted vm info: \n$vm_info"

    user=$(echo "$vm_info" | grep "userName=" | sed "s|userName=||g")
    pw=$(echo "$vm_info" | grep "userPw=" | sed "s|userPw=||g")
    port=$(echo "$vm_info" | grep "portSsh=" | sed "s|portSsh=||g")
    host=$(echo "$vm_info" | grep "host=" | sed "s|host=||g")
    api_key=$(cat /etc/discourse/client-api-key)

    logInfo "ToDo: Do it ${user} ${pw} ${port} ${host} ${api_key}"
}

#
#    Start programm with parameters.
#
main "$@"
