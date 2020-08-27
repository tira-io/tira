#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Anna Beyer, Manuel Willem, Adrian Teschendorf, Martin Potthast, Steve Göring
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
neededtools="VBoxManage"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <vm-name>

Description:
    Takes a VM out of sandbox mode.

Options:
    -h | --help           Display help documentation
    -r | --remote [host]  Remote control a specific host

Parameters:
    <vm-name>             Name of the vm

Examples:
    $(basename "$0") my_vm (local)
    $(basename "$0") -r webis16 my_vm (remote)

Authors:
    Anna Beyer
    Manuel Willem
    Adrian Teschendorf
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
#    Takes a VM out of sandbox mode.
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -ne 1 ]; then
        logError "Missing arguments see:"
        usage
    fi

    sleep 10

    vm_reg_file="$_CONFIG_FILE_tira_vms"
    vmname="$1"

    logInfo "executing unsandbox script"

    vm_info=$(get_vm_info_from_tira "$vmname")
    vmnumber=$(echo "$vm_info" | grep "vmId" | sed "s|vmId=||g")
    vmid=$(printf "%02d\n" "$vmnumber")
    sshport=$(echo "$vm_info" | grep "portSsh" | sed "s|portSsh=||g")
    rdpport=$(echo "$vm_info" | grep "portRdp" | sed "s|portRdp=||g")
    chainname="sandbox-vm-$vmid"

    dir="$_CONFIG_FILE_tira_state_virtual_machines_dir"
    lockfile="$dir/~$vmname.sandboxed"
    progressfile="$dir/~$vmname.unsandboxing"
    oldprogressfile="$dir/~$vmname.sandboxing"

    # Is not sandboxed.
    if [ ! -e "$lockfile" ]; then
        logWarn "VM $vmname is not sandboxed!"
        exit 1
    fi

    logInfo "UNSANDBOX $vmname..."
    # Get snapshot name.
    . "$lockfile"

    # create progress file.
    touch "$progressfile"

    # remove leftovers from unsuccessful sandboxing attempts.
    if [ -f "$oldprogressfile" ]; then
        rm "$oldprogressfile"
    fi

    # Shutdown cloned vm.
    tira_call vm-stop "$vmname-clone-$snapshotName"

    # Unregister cloned vm.
    VBoxManage unregistervm --delete "$vmname-clone-$snapshotName"
    # Remove snapshot.
    #VBoxManage snapshot "$vmname" delete "$snapshotName"

    # Start original VM.
    tira_call vm-start "$vmname"

    # tira custom chains
    INPUT=tira_input
    FORWARD=tira_forward
    # Deactivate firewall rules.
    logDebug "chainname: $chainname"
    logDebug "rdpport: $rdpport"
    sudo iptables -D $FORWARD -j "$chainname"
    sudo iptables -F "$chainname"
    sudo iptables -X "$chainname"
    # Enable SSH from outside the university network.
    sudo iptables -D $INPUT -i eth+ -p tcp --dport "$sshport" -j REJECT
    sudo iptables -D $INPUT -i eth+ -p tcp --dport "$sshport" -s 141.54.0.0/16 -j ACCEPT
    sudo iptables -D $INPUT -i eth+ -p tcp --dport "$sshport" -s localhost -j ACCEPT
    sudo iptables -D $INPUT -i em+ -p tcp --dport "$sshport" -j REJECT
    sudo iptables -D $INPUT -i em+ -p tcp --dport "$sshport" -s 141.54.0.0/16 -j ACCEPT
    sudo iptables -D $INPUT -i em+ -p tcp --dport "$sshport" -s localhost -j ACCEPT
    # Enable RDP from outside the university network.
    sudo iptables -D $INPUT -i eth+ -p tcp --dport "$rdpport" -j REJECT
    sudo iptables -D $INPUT -i eth+ -p tcp --dport "$rdpport" -s 141.54.0.0/16 -j ACCEPT
    sudo iptables -D $INPUT -i eth+ -p tcp --dport "$rdpport" -s localhost -j ACCEPT
    sudo iptables -D $INPUT -i em+ -p tcp --dport "$rdpport" -j REJECT
    sudo iptables -D $INPUT -i em+ -p tcp --dport "$rdpport" -s 141.54.0.0/16 -j ACCEPT
    sudo iptables -D $INPUT -i em+ -p tcp --dport "$rdpport" -s localhost -j ACCEPT

    # Config entry.
    hostname=$(hostname)
    sed -i "s/$hostname\\t$vmname\\tsandboxed/$hostname\\t$vmname/g" "$vm_reg_file"

    # Tidy up Virtualbox directory.
    rm -rf "/home/$_CONFIG_tira_username"/VirtualBox\ VMs/"$vmname-clone-$snapshotName"

    # Remove lock file.
    rm "$lockfile"
    rm "$progressfile"
}

#
#    Start programm with parameters.
#
main "$@"
