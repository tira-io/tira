#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Anna Beyer, Steve Göring, Martin Potthast
#

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="VBoxManage"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") <ova> <vm-name> <user> <password> <ip> <sshport> <rdpport> <admin-password>

Description:
    Import and configure a VM, then start it.

Parameters:
    <ova>
    <vm-name>             Name of the VM
    <user>
    <password>
    <ip>
    <sshport>
    <rdpport>
    <admin-password>

Examples:
    $(basename "$0") my_vm (local)

Authors:
    Anna Beyer
    Steve Göring"
    exit 1
}


#
#    Virtual machine configuration: windows
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -ne 8 ]; then
        logError "Missing arguments see:"
        usage
    fi

    # Get arguments.
    ova="$1"
    vm="$2"
    user="$3"
    pw="$4"
    ip="$5"
    sshport="$6"
    rdpport="$7"
    pwtira="$8"
    vmid=$((sshport - 44400))

    if [ ! -f "$ova" ]; then
        logError "OVA does not exist."
        exit 1
    fi

    iface="vboxnet$vmid"
    usertira='administrator'

    sfname1="$_CONFIG_tira_training_datasets_name"
    sfhostpath1="$_CONFIG_FILE_tira_training_datasets_dir"

    # Import ova file.
    VBoxManage import "$ova" --vsys 0 --vmname "$vm"

    # Network settings.
    VBoxManage hostonlyif create
    VBoxManage hostonlyif ipconfig "$iface" --ip "$ip"
    VBoxManage modifyvm "$vm" --nic1 hostonly --hostonlyadapter1 "$iface"

    # Remote machine settings.
    VBoxManage modifyvm "$vm" --vrde on
    VBoxManage modifyvm "$vm" --vrdeport "$rdpport"
    VBoxManage modifyvm "$vm" --vrdeauthtype external

    # User rdp authentication.
    pwhash=$(VBoxManage internalcommands passwordhash "$pw" | sed "s/Password hash: //g")
    VBoxManage setextradata "$vm" "VBoxAuthSimple/users/$user" "$pwhash"

    # Admin rdp authentication.
    pwhashtira=$(VBoxManage internalcommands passwordhash "$pwtira" | sed "s/Password hash: //g")
    VBoxManage setextradata "$vm" "VBoxAuthSimple/users/$usertira" "$pwhashtira"

    # Shared folder.
    VBoxManage sharedfolder add "$vm" --name "$sfname1" --hostpath "$sfhostpath1" --readonly --automount

    # Start vm.
    tira_call vm-start "$vm"
}

#
#    Start programm with parameters.
#
main "$@"
