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
neededtools="curl jq"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") <name>

Description:
    Delete the discourse group associated to a vm.

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

set -e

delete_group() {
    group_name="tira_vm_$vmname_or_user"
    api_key=$(cat /etc/discourse/client-api-key)
    group_id=$(curl -X GET "${_CONFIG_tira_disraptor_url}/groups/$group_name" -H "Api-Key: $api_key" -H "Accept: application/json"| jq -r '.group.id')
    curl -X DELETE "${_CONFIG_tira_disraptor_url}/admin/groups/$group_id" -H "Api-Key: $api_key"
}

#
#    Delete the discourse group associated to a vm.
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
        logError "VM-Name/user $vmname_or_user is not registered. Use tira vm-list to get a list of all vms."
        exit 1
    fi

    user=$(echo "$vm_info" | grep "userName=" | sed "s|userName=||g")
    logInfo "Delete group of user ${user}"

    delete_group
}

#
#    Start programm with parameters.
#
main "$@"
