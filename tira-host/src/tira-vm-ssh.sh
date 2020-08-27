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
    Open SSH session to vm.

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
DEFINE_string cmd "" 'command to execute' 'C'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Start ssh connetion to a vm.
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -eq 0 ]; then
        logError "Missing arguments see:"
        usage
    fi

    vmname_or_user="$1"

    # Every parameter is parsed and extracted: now do the job.
    vm_info=$(get_vm_info_from_tira "$vmname_or_user")

    if [ "$vm_info" = "" ]; then
        logError "VM-Name/user $vmname_or_user is not registred. Use tira vm-list to get a list of all vms."
        exit 1
    fi
    logDebug "Extracted vm info: \n$vm_info"

    admin="${FLAGS_admin}"
    cmd="${FLAGS_cmd}"
    user=""
    pw=""
    if [ "$admin" = "${FLAGS_TRUE}" ]; then
        user=$(echo "$vm_info" | grep "adminName=" | sed "s|adminName=||g")
        pw=$(echo "$vm_info" | grep "adminPw=" | sed "s|adminPw=||g")
        logDebug "User=Administrator"
    else
        user=$(echo "$vm_info" | grep "userName=" | sed "s|userName=||g")
        pw=$(echo "$vm_info" | grep "userPw=" | sed "s|userPw=||g")
        logDebug "User= $user (default)"
    fi
    port=$(echo "$vm_info" | grep "portSsh=" | sed "s|portSsh=||g")
    host=$(echo "$vm_info" | grep "host=" | sed "s|host=||g")
    logDebug "with pw: $pw using port: $port on host: $host"

    # Reset vmname in order to make sure its the actual name, not just the user name.
    vmname=$(echo "$vm_info" | grep "vmName=" | sed "s|vmName=||g")
    # Check if vm is running:
    running=$(tira_call vm-info -r "$host" "$vmname" -s| grep "running")

    if [ "$running" = "" ]; then
        logError "Vm $vmname is not running, therefore no ssh connection can be established."
        exit 1
    fi

    logInfo "Build SSH connection: user: $user password: $pw"

    if [ "$cmd" = "" ]; then
        sshpass -p "$pw" ssh "${user}@${host}" -p "$port" \
            -o ConnectTimeout=15 \
            -o ConnectionAttempts=100 \
            -o StrictHostKeyChecking=no \
            -o UserKnownHostsFile=/dev/null
    else
        # Replace variable names (password).
        #cmd=$(echo "$cmd" | sed "s|\$pw|$pw|g")
        logInfo "run command: \"$cmd\""
        sshpass -p "$pw" ssh "${user}@${host}" -p "$port" \
            -o ConnectTimeout=15 \
            -o ConnectionAttempts=100 \
            -o StrictHostKeyChecking=no \
            -o UserKnownHostsFile=/dev/null \
            -o LogLevel=error -t -t "$cmd"
    fi


}

#
#    Start programm with parameters.
#
main "$@"
