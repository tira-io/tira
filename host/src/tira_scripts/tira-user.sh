#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Steve Göring

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
_BASHHELPER="included"
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="ssh useradd groupmod addgroup sudo ssh-keygen sshpass"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags]

Description:

Examples:
    $(basename "$0") -c webis16
    $(basename "$0") -d

Authors:
    Steve Göring"
    exit 1
}

tira_user="$_CONFIG_tira_username"
tira_group="$_CONFIG_tira_groupname"
randomconst="Bhv0S"

#
#    Create tira user.
#
#    \params $@ tira nfs hostname
#
create_user() {
    logInfo "Create tira user"
    host="$@"

    group_exists=$(getent group | cut -d: -f1 | grep "$tira_group")
    if [ "$group_exists" != "" ]; then
        logError "$tira_group group is already there. Exit."
        exit 0
    fi
    logInfo "SSH Key Exchange with tira nfs host."
    read_password "Please insert tira NFS host password:" password
    ssh_key_exchange "$tira_user@$host" "$password"

    # Get Group and User ID from NFS-Host
    # Make sure that the group id of the tira group corresponds to the group id
    # used for the Tira NFS host (cat /etc/group lists group ids):
    logInfo "Extract user and group id from nfs-host: $host."
    userid=$(ssh "$tira_user@$host" \
            -o UserKnownHostsFile=/dev/null \
            -o StrictHostKeyChecking=no \
            -o LogLevel=error \
            "id -u \"$tira_user\"" 2> /dev/null)
    groupid=$(ssh "$tira_user@$host" \
            -o UserKnownHostsFile=/dev/null \
            -o StrictHostKeyChecking=no \
            -o LogLevel=error \
            "getent group \"$tira_group\" | cut -d: -f3" 2> /dev/null)

    logInfo "userid: $userid, groupid: $groupid"

    if [ "$userid" = "" ] || [ "$groupid" = "" ]; then
        logError "Userid and groupid could not be extracted, check if $host is a tira-nfs host."
        userid="1010"
        groupid="1010"
    fi

    # Create tira group.
    sudo addgroup --gid "$groupid" "$tira_group"
    # If vbox is not installed, create dummy vboxusers group.
    sudo addgroup vboxusers

    # Create the tira user.
    sudo useradd -g "$tira_group" -G vboxusers -s "/bin/bash" -m -d "/home/$tira_user" "$tira_user"
    sudo usermod -u "$userid" "$tira_user"

    logInfo "Set tira user password:"
    sudo passwd "$tira_user"

    logInfo "Do sudoers modifications, so that tira user can access iptables."

    tmp_file=$(tempfile)

    sudo cp "/etc/sudoers" "$tmp_file"

    tira_rule_test=$(sudo grep "$tira_group" "$tmp_file")
    if [ "$tira_rule_test" = "" ]; then

        echo "# Allow tira to execute iptables without password entry #TIRA$randomconst" | sudo tee -a "$tmp_file" > /dev/null
        echo "# do not modify: #TIRA$randomconst" | sudo tee -a "$tmp_file" > /dev/null
        echo "Defaults:%$tira_user  umask = 0002 #TIRA$randomconst" | sudo tee -a "$tmp_file" > /dev/null
        echo "Defaults:%$tira_user  umask_override #TIRA$randomconst" | sudo tee -a "$tmp_file" > /dev/null
        echo "$tira_group ALL=NOPASSWD: /sbin/iptables #TIRA$randomconst" | sudo tee -a "$tmp_file" > /dev/null
        echo "%$tira_group ALL=(tira) NOPASSWD: /usr/bin/tira, /bin/touch, /bin/mkdir #TIRA$randomconst" | sudo tee -a "$tmp_file" > /dev/null

        # Check if it is valid
        sudo visudo -c -f "$tmp_file"
        if [ "$?" -eq "0" ]; then
            sudo cp "$tmp_file" "/etc/sudoers"
        else
            logError "There is something wrong with sudoers file."
        fi
    else
        logWarn "There were already settings for tira user in sudoers file."
    fi
    sudo rm -rf "$tmp_file"

    logInfo "Log in as tira user in local computer and generate ssh key and create ~/.tira."
    su "$tira_user" -c "ssh-keygen; mkdir -p ~/.tira"
}

#
#    Delete tira user.
#
delete_user() {
    logInfo "Remove user: $tira_user"
    sudo userdel "$tira_user" 2> /dev/null
    logInfo "Remove group: $tira_group"
    sudo groupdel "$tira_group" 2> /dev/null

    logInfo "Undo visudo entries:"

    tmp_file=$(tempfile)

    sudo cp "/etc/sudoers" "$tmp_file"

    tira_rule_test=$(sudo grep "$tira_group" "$tmp_file")
    if [ "$tira_rule_test" != "" ]; then

        sudo sed -i "\|#TIRA|d" "$tmp_file"
        # Check if it is valid
        sudo visudo -c -f "$tmp_file"
        if [ "$?" -eq "0" ]; then
            sudo cp "$tmp_file" "/etc/sudoers"
        else
            logError "There is something wrong with sudoers file."
        fi
    else
        logWarn "There were no settings for tira user in sudoers file."
    fi
    sudo rm -rf "$tmp_file"

    logInfo "Done."
}

#
#    Define command line arguments and parse them.
#
DEFINE_string create "" 'create tira user, parameter=NFS Host' 'c'
DEFINE_boolean delete false 'delete tira user' 'd'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Creates or deletes tira user with all settings.
#
main() {

    create="${FLAGS_create}"
    delete="${FLAGS_delete}"

    if [ "$create" != "" ] && [ "$delete" = "${FLAGS_TRUE}" ]; then
        logError "Parameters delete and create cannot be combined, see:"
        usage
    fi

    # Create or delete tira user.
    if [ "$create" != "" ]; then
        if [ "$(host_alive "$create")" = "false" ]; then
            logError "NFS Host is not reachable. Exit."
            exit 0
        fi
        create_user "$create"
        return
    fi
    if [ "$delete" = "${FLAGS_TRUE}" ]; then
        delete_user
        return
    fi

}

#
#    Start programm with parameters.
#
main "$@"
