#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Martin Potthast, Steve Göring
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
neededtools="sshpass"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <name>

Description:
    Shuts down a given user's virtual machine via command line.

Parameters:
    <name>                Name of the VM, or username

Examples:
    $(basename "$0") User456 (local)

Authors:
    Martin Potthast
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
check_is_vm_stopped() {
    vmname="$1"
    get_vm_state "$vmname" state
    if [ "$state" = "running" ];  then
        logError "VM is not stopped!"
        exit 1
    fi
}

#
#     Shuts down a given user's virtual machine via command line.
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -ne 1 ]; then
        logError "Wrong number of parameters, see:"
        usage
    fi

    # Extract correct vmname from nfs.
    vmname_or_user="$1"

    vm_info=$(get_vm_info_from_tira "$vmname_or_user")
    vmname=$(echo "$vm_info" | grep "vmName" | sed "s|vmName=||g")
    if [ "$vmname" = "" ]; then
        vmname="$vmname_or_user"
    fi
    host=$(echo "$vm_info" | grep "host" | sed "s|host=||g")
    sshport=$(echo "$vm_info" | grep "portSsh" | sed "s|portSsh=||g")
    user=$(echo "$vm_info" | grep "userName" | sed "s|userName=||g")
    userpw=$(echo "$vm_info" | grep "userPw" | sed "s|userPw=||g")
    if [[ "$vmname" == *"ubuntu"* ]]; then
        os="ubuntu"
    elif [[ "$vmname" == *"fedora"* ]]; then
        os="fedora"
    else
        os="windows"
    fi
    
    # Check if vm is a local vm, otherwise extract info and run remotly.
    if [ "$(is_tira_vm "$vmname")" = "false" ]; then
        logTodo "check if host is not the extracted host"
        if [ "$host" != "" ]; then
            tira_call vm-shutdown -r "$host" "$vmname"
        else
            logError "$vmname is not a valid username/vmname."
        fi
        return
    fi

    # Every parameter is parsed and extracted: now do the job.

    # Check if vm is started.
    get_vm_state "$vmname" state

    if [ "$state" != "running" ];  then
        logWarn "VM is not running!"
        exit 1
    fi


    if [ "$os" = "ubuntu" ] || [ "$os" = "fedora" ]; then
        shutdownCmd="echo $userpw | sudo -S shutdown -h now"
    elif [ "$os" = "windows" ]; then
        shutdownCmd="shutdown.exe /s /f /t 0"
    fi


    # Shutting down VM.

    logInfo "Shutting down VM of $user on $host with cmd $shutdownCmd ..."
    sshpass -p "$userpw" \
      ssh "$user@$host" -p "$sshport" \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no \
        -o LogLevel=error \
        -t \
        -t "$shutdownCmd"
        
    unittest && check_is_vm_stopped "$vmname"
}

#
#    Start programm with parameters.
#
main "$@"
