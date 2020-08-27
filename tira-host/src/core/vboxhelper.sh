#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Virtualbox helper functions.
#
#    Author: Steve Göring
#

#
#    Include bashhelper.
#
thisscriptpath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. $thisscriptpath/bashhelper.sh

#
#    Get the state of a virtual machine.
#
#    \params $1 vmname, $2 result variable
#    Example call:
#        get_vm_state "vmname" state
#
get_vm_state() {
    vmname="$1"
    __resultvar="$2"
    state=$(VBoxManage showvminfo $vmname \
        | grep '^State' \
        | sed 's/^State:\s*//' \
        | sed 's/\s(since.*$//')

    if [[ -z "$state" ]]; then
        logError "status of vm '$vmname' could not be extracted"
    fi
    logDebug "get status of vm: $vmname, status: $state"
    eval "$__resultvar=\"$state\""
}

#
#    Get network interface name of registred tira vm.
#
#    \params $1 vm name
#    \params $2 result variable
#
#    Example call:
#        get_vm_netinterface "$vmname" "iface"
#
get_vm_netinterface() {
    __resultvar="$2"
    vmname="$1"
    iface=$(VBoxManage showvminfo "$vmname" --machinereadable \
        | grep hostonlyadapter \
        | awk ' { gsub(/"/,"",$0); split($0,a,"="); print a[2]}')

    eval "$__resultvar=\"$iface\""
}

#
#    Get all registred tira vms of this host.
#
#    \params $1 result variable
#    Example call:
#        get_tira_vms vms
#
get_tira_vms() {
    __resultvar="$1"
    vms=$(VBoxManage list vms \
        | grep -e '..-tira-ubuntu\|..-tira-fedora\|..-tira-windows'\
        | awk '{ gsub(/\"/,"",$0) split($0,a," "); print a[1]}' )

    eval "$__resultvar=\"$vms\""
}

#
#    Check if vm is a registred tira vm of this host.
#
#    \params $1 vmname
#    \return on stdout true or false
#    Example call:
#        is_tira_vm "vmname"
#
is_tira_vm() {
    get_tira_vms vms

    res=$(echo "$vms" | grep -Fx "$1")
    if [ "$res" != "" ]; then
        echo "true"
        return
    fi

    echo "false"
}

#
#    Check if vm is a registred tira vm on this host
#    for the user.
#
#    \params $1 vmname
#    \params $2 username
#    \return on stdout true or false
#    Example call:
#        is_tira_vm_of_user "vmname" "username"
#
is_tira_vm_of_user() {
    get_tira_vms vms

    res=$(echo "$vms" | grep -Fx "$1" | grep "^$2-")
    if [ "$res" != "" ]; then
        echo "true"
        return
    fi

    echo "false"
}

