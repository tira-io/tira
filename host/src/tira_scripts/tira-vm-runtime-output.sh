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
neededtools="ssh"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <vm-name> <run-id>

Description:
    Check the current run output inside the sandboxed VM.

Options:
    -h | --help           Display help documentation
Parameters:
    <vm-name>             Name of the VM
    <run-id>              ID of the current run

Examples:
    $(basename "$0") my_vm run_id (local)
    $(basename "$0") -r webis46 my_vm run_id (remote)

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
#    Check the current run output inside the sandboxed VM.
#
main() {

    logInfo "[tira-vm-runtime-output] Checking Parameters..."
    if [ "$#" -eq 0 ]; then
        logError "[tira-vm-runtime-output] Missing arguments see:"
        usage
    fi
    logInfo "[tira-vm-runtime-output] Checking Parameters done."
    
    logInfo "[tira-vm-runtime-output] Get VM info..."
    vmname="$1"
    runid="$2"

    vm_info=$(get_vm_info_from_tira "$vmname")
    if [ "$vm_info" = "" ]; then
        logError "[tira-vm-runtime-output] VM-Name/user $vmname_or_user is not registred. Use tira vm-list to get a list of all vms."
        exit 1
    fi
    user=$(echo "$vm_info" | grep "userName=" | sed "s|userName=||g")
    pw=$(echo "$vm_info" | grep "userPw=" | sed "s|userPw=||g")
    host=$(echo "$vm_info" | grep "host=" | sed "s|host=||g")
    
    logInfo "[tira-vm-runtime-output] Get VM info done."
    
    
    logInfo "[tira-vm-runtime-output] Create runtime output directory..."

    if [[ "$vmname" == *"ubuntu"* ]] || [[ "$vmname" == *"fedora"* ]]; then
        tmpRunDir="/tmp/$user/$runid"
    elif [[ "$vmname" == *"windows"* ]]; then
        tmpRunDir="/cygdrive/c/Windows/Temp/$user/$runid"
    fi
    tmpRunDirOutput="$tmpRunDir/output"
    
    logInfo "[tira-vm-runtime-output] Create runtime output directory done."

    logInfo "[tira-vm-runtime-output] Checking if VM is sandboxed and cloned VM is running..."
    sandboxLockFile="$_CONFIG_FILE_tira_state_virtual_machines_dir/~$vmname.sandboxed"
    if [ ! -e "$sandboxLockFile" ]; then
        logError "[tira-vm-runtime-output] VM $vmname is not sandboxed!"
        exit 1
    fi
    . "$sandboxLockFile"

    vmclonename="$vmname-clone-$runid"
    # TODO "Calling get_vm_state directly with \$vmclonename does not work. It still uses the value of the \$vmname variable."
    vmname="$vmclonename"
    get_vm_state "$vmclonename" state
    if [ "$state" != "running" ]; then
        logError "[tira-vm-runtime-output] VM clone $vmclonename is not running!"
        exit 1
    fi
    logInfo "[tira-vm-runtime-output] VM is sandboxed and cloned VM is running."
    
    # TODO "Clonend VM expects to be called from localhost, so that this script must be called with the -r option to work. Not sure, how to solve this."
    logDebug "[tira-vm-runtime-output] pw: $pw  host: ${user}@localhost port: $natsshport"
    logInfo "[tira-vm-runtime-output] Show VM runtime output. Latest output begin:"

    # with the following extension, the command can be startet without the -r host parameter of the main script, but it is nessessary to update this script, e.g. get_vm_state call would not work
    # ssh -t "$host"
    sshpass -p "$pw" \
      ssh "${user}@$host" \
        -p "$natsshport" \
        -o ConnectTimeout=15 \
        -o ConnectionAttempts=100 \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no \
        -o LogLevel=error \
        -t \
        -t "printf 'StdOut tail (last 1000 bytes):\n'; \
            tail -c 1000 $tmpRunDir/stdout.txt; \
            printf '\nStdErr tail (last 1000 bytes):\n'; \
            tail -c 1000 $tmpRunDir/stderr.txt; \
            printf '\nLast touched files:\n'; \
            ls -lAtgoh --time-style=long-iso $tmpRunDirOutput \
            | awk '{if(NR>1)print}' \
            | awk '{printf(\"%10s %5s  %5s  %2s  %-40s\n\", \$4, \$5, \$3, \$2, \$6);}' \
            | head"
      
      logInfo "[tira-vm-runtime-output] Stopped showing VM runtime output."
}

#
#    Start programm with parameters.
#
main "$@"
