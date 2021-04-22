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

set -e

create_group() {
    group_name="tira_vm_$vmname_or_user"
    group_bio="Members of this group have access to the virtual machine $vmname_or_user:<br><br>
<ul>
  <li>Host: $host</li>
  <li>User: $vmname_or_user</li>
  <li>Passwort: $pw</li>
  <li>SSH Port: $port</li>
  <li>RDP Port: $rdp_port</li>
  <li>SSH Example: <code>sshpass -p $pw ssh $user@$host -p $port -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no</code></li>
</ul><br><br>
Please contact us when you have questions.
"

    # Post form for group creation and store group id for invite
    group_info=$(curl -X POST "${_CONFIG_tira_disraptor_url}/admin/groups" \
        -H "Api-Key: $api_key" \
        -H "Accept: application/json" \
        -H "Content-Type: multipart/form-data" \
        -F "group[name]=$group_name" \
        -F "group[visibility_level]=2" \
        -F "group[members_visibility_level]=2" \
        -F "group[bio_raw]=$group_bio"
    )

    group_id=$(echo $group_info | jq '.basic_group.id')
}

invite_users() {
    year=$(date +"%Y" -d 'next year')

    # invite users to group created by create_group()
    curl -X POST "${_CONFIG_tira_disraptor_url}/invites" -H "Api-Key: $api_key" -H "Accept: application/json" -H "Content-Type: multipart/form-data" -F "group_ids[]=$group_id" -F "max_redemptions_allowed=20" -F "expires_at=$year-12-31"|jq -r '.link'
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

    user=$(echo "$vm_info" | grep "userName=" | sed "s|userName=||g")
    pw=$(echo "$vm_info" | grep "userPw=" | sed "s|userPw=||g")
    port=$(echo "$vm_info" | grep "portSsh=" | sed "s|portSsh=||g")
    rdp_port=$(echo "$vm_info" | grep "portRdp=" | sed "s|portRdp=||g")
    host=$(echo "$vm_info" | grep "host=" | sed "s|host=||g")
    api_key=$(cat /etc/discourse/client-api-key)

    logInfo "Create group with\n\tuser=${user}\n\tpw=${pw}\n\tssh-port=${port}\n\trdp_port=${rdp_port}\n\thost=${host}\n\tapi-key=${api_key}"

    create_group
    invite_users
}

#
#    Start programm with parameters.
#
main "$@"
