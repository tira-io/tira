#!/bin/bash

scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/core/vboxhelper.sh
. "$scriptPath"/libs/shflags

neededtools="VBoxManage"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

usage() {
    echo "
Usage:
    $(basename "$0") [flags] <vm_id> <memory> <cpus>

Description:
    This script runs vboxmanage modifyvm <vmname> --memory --cpus

Options:
    -h | --help           Display help documentation

Examples:
    $(basename "$0") pan21-master 16000 2 (local)
    $(basename "$0") -r betaweb042 pan21-master 16000 2 (remote)
    exit 1
}"

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
        return "false"
    fi
    return "true"
}

#
#    Start a vm.
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -ne 3 ]; then
        logError "Wrong arguments, see:"
        usage
    fi

    # Extract correct vmname from nfs.
    vmname_or_user="$1"
    mem="$2"
    cpu="$3"

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
            tira_call vm-modify -r "$host" "$vmname" "$mem" "$cpu"
        else
            logError "$vmname is not a valid username/vmname."
        fi
        return
    fi

    if [ $(check_is_vm_running) = "true" ]; then
      tira vm-stop "$vmname"
    fi
    # Check if vm is already started.

    # Starting VM.
    logInfo "'$vmname' getting started ..."

    VBoxManage modifyvm "$vmname" --memory "$mem" --cpus "$cpu"\
        || logError "vm could not be modified"

    VBoxManage startvm "$vmname" --type headless \
        || logError "vm could not be started after modification"

    unittest && check_is_vm_started "$vmname"
}