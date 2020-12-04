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

create_group() {
    group_name="tira-vm-$vmname_or_user"
    group_bio="Members of this group have access to the virtual machine $vmname_or_user on $host.<br><br>
    The password for the virtual machine $vmname_or_user was sent to the participants in a separate mail.<br>The virtual machine can be accessed via SSH (host $host, port $port) or RDP (host $host, port $port_rdp) to install the software(s) that participate in the shared task.<br><br>You can SSH into the virtual machine with: sshpass -p $pw ssh $user@$host.medien.uni-weimar.de -p $port -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

    # Post form for group creation and store group id for invite
    group_info=$(curl -X POST "https://disraptor.tira.io/admin/groups" -H "Api-Key: $api_key" -H "Accept: application/json" -H "Content-Type: multipart/form-data" -F "group[name]=$group_name" -F "group[messageable_level]=2" -F "group[member_visibility_level]=2" -F "group[bio_raw]=$group_bio")

    group_id=$(group_info | jq '.basic_group.id')
}

invite_users() {
    year=$(date +"%Y" -d 'next year')

    # invite users to group created by create_group()
    curl -X POST "https://disraptor.tira.io/invites/link" -H "Api-Key: $api_key" -H "Accept: application/json" -H "Content-Type: multipart/form-data" -F "group_ids[]=$group_id" -F "max_redemptions_allowed=20" -F "expires_at=$year-12-31"
}

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
        logError "VM-Name/user $vmname_or_user is not registered. Use tira vm-list to get a list of all vms."
        exit 1
    fi
    logDebug "Extracted vm info: \n$vm_info"

    user=$(echo "$vm_info" | grep "userName=" | sed "s|userName=||g")
    pw=$(echo "$vm_info" | grep "userPw=" | sed "s|userPw=||g")
    port=$(echo "$vm_info" | grep "portSsh=" | sed "s|portSsh=||g")
    rdp_port=$(echo "$vm_info" | grep "portRdp=" | sed "s|portRdp=||g")
    host=$(echo "$vm_info" | grep "host=" | sed "s|host=||g")
    api_key=$(cat /etc/discourse/client-api-key)

    logInfo "ToDo: Do it ${user} ${pw} ${port} ${host} ${api_key}"

    create_group
    invite_users
}

#
#    Start programm with parameters.
#
main "$@"
