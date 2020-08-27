#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Martin Potthast, Anna Beyer, Manuel Willem, Adrian Teschendorf, Steve Göring

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
neededtools="sudo dig"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage(){
    echo "
Usage:
    $(basename "$0") [flags] <vm-name> <snapshot-name> <mount-test-datasets>

Description:
    Puts a VM in sandbox mode: VM is only reachable within the
    university network.

Options:
    -h | --help             Display help documentation
    -r | --remote [host]    Remote control a specific host

Parameters:
    <vm-name>               Name of the VM
    <snapshot-name>         Name of the snapshot to be taken from the VM.
    <mount-test-datasets>   Flag indicates whether test datasets should be mounted or not.
                            Is either \"true\" or \"false\".

Examples:
    $(basename "$0") my_vm (local)
    $(basename "$0") -r webis16 my_vm (remote) TODO

Authors:
    Martin Potthast
    Anna Beyer
    Manuel Willem
    Adrian Teschendorf
    Steve Göring"
    exit 1
}

#
#    Define command line arguments and parse them.
#
DEFINE_string taskname "" 'taskname' 'T'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Puts a VM in sandbox mode.
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -ne 3 ]; then
        logError "Wrong amount of parameters, see:"
        usage
    fi

    sleep 10

    vmname="$1"
    snapshotName="$2"
    mounttestdatasets="$3"

    # Flag for mounting test datasets.
    if [ "$mounttestdatasets" != "true" ] && [ "$mounttestdatasets" != "false" ]; then
        logError "<mount-test-datasets> is not \"true\" or \"false\"."
        usage
    fi

    logInfo "Executing sandbox script."

    vm_info=$(get_vm_info_from_tira "$vmname")
    vmnumber=$(echo "$vm_info" | grep "vmId" | sed "s|vmId=||g")
    vmid=$(printf "%02d\n" "$vmnumber")
    sshport=$(echo "$vm_info" | grep "portSsh" | sed "s|portSsh=||g")
    rdpport=$(echo "$vm_info" | grep "portRdp" | sed "s|portRdp=||g")
    chainname="sandbox-vm-$vmid"

    # Create lock and progress file.
    dir="$_CONFIG_FILE_tira_state_virtual_machines_dir"
    lockfile="$dir/~$vmname.sandboxed"
    progressfile="$dir/~$vmname.sandboxing"

    # VM is sandboxed?
    if [ -e "$lockfile" ]; then
        logError "VM $vmname is already sandboxed!"
        exit 1
    fi
    logInfo "SANDBOX $vmname..."
    logInfo "Shutdown original vm."

    # Check if auto snapshot name should be used.
    if [ "$snapshotName" = "auto" ]; then
        timestamp=$(date +%Y-%m-%d-%H-%M-%S)
        snapshotName="$timestamp"
    fi

    echo "snapshotName=$snapshotName" > "$lockfile"
    echo "natsshport=$sshport" >> "$lockfile"
    echo "snapshotName=$snapshotName" > "$progressfile"

    vm_infos=$(get_vm_info_from_tira "$vmname")
    pw=$(echo "$vm_infos" | grep "userPw=" | sed "s|userPw=||g")

    # Shutdown original vm.
    tira_call vm-shutdown "$vmname"

    # Wait, so that vm is not running longer.
    tries=0
    get_vm_state "$vmname" state
    while [ "$state" = "running" ];  do
        sleep 20

        get_vm_state "$vmname" state
        if [[ "$tries" > 15 ]]; then
            logError "Problem with shutdown of $vmname, so stop vm."
            tira_call vm-stop "$vmname"
        fi
        tries=$((tries+1))
    done

    iface="vboxnet$vmnumber"
    # tira custom chains
    INPUT=tira_input
    FORWARD=tira_forward

    # Firewall changes for disallowing traffic to the origin vm.
    sudo iptables -N "$chainname"
    # Allow access to: api.eu-gb.personality-insights.watson.cloud.ibm.com + iam.bluemix.net/identity/token + api.symanto.net
    sudo iptables -I "$chainname" 1 -i "$iface" -d 23.45.238.21 -j ACCEPT
    sudo iptables -I "$chainname" 2 -i "$iface" -d 2.23.80.139 -j ACCEPT
    sudo iptables -I "$chainname" 3 -i "$iface" -d 13.79.133.109 -j ACCEPT
    sudo iptables -I "$chainname" 4 -i "$iface" -d 141.54.0.0/16 -j ACCEPT
    sudo iptables -I "$chainname" 5 -i "$iface" -d localhost -j ACCEPT
    sudo iptables -I "$chainname" 6 -i "$iface" -j LOG --log-prefix "ipt-$vmname: "
    sudo iptables -I "$chainname" 7 -i "$iface" -j REJECT
    sudo iptables -I $FORWARD 1 -j "$chainname"
    # Disable SSH from outside university, but allow it from the inside.
    sudo iptables -I $INPUT -i eth+ -p tcp --dport "$sshport" -j REJECT
    sudo iptables -I $INPUT -i eth+ -p tcp --dport "$sshport" -s 141.54.0.0/16 -j ACCEPT
    sudo iptables -I $INPUT -i eth+ -p tcp --dport "$sshport" -s localhost -j ACCEPT
    sudo iptables -I $INPUT -i em+ -p tcp --dport "$sshport" -j REJECT
    sudo iptables -I $INPUT -i em+ -p tcp --dport "$sshport" -s 141.54.0.0/16 -j ACCEPT
    sudo iptables -I $INPUT -i em+ -p tcp --dport "$sshport" -s localhost -j ACCEPT
    # Disable RDP from outside university, but allow it from the inside.
    sudo iptables -I $INPUT -i eth+ -p tcp --dport "$rdpport" -j REJECT
    sudo iptables -I $INPUT -i eth+ -p tcp --dport "$rdpport" -s 141.54.0.0/16 -j ACCEPT
    sudo iptables -I $INPUT -i eth+ -p tcp --dport "$rdpport" -s localhost -j ACCEPT
    sudo iptables -I $INPUT -i em+ -p tcp --dport "$rdpport" -j REJECT
    sudo iptables -I $INPUT -i em+ -p tcp --dport "$rdpport" -s 141.54.0.0/16 -j ACCEPT
    sudo iptables -I $INPUT -i em+ -p tcp --dport "$rdpport" -s localhost -j ACCEPT

    vm_ip_adress=$(echo "$vm_infos" | grep "ip=" | sed "s|ip=||g")
    logDebug "vm ip adress: $vm_ip_adress"

    # Create cloned VM.
    VBoxManage clonevm --options keepallmacs --name "$vmname-clone-$snapshotName" "$vmname" --register

    # Mounting test datasets.
    if [ "$mounttestdatasets" = "true" ]; then
        sfnametest="$_CONFIG_tira_test_datasets_name"
        sfpathtest="$_CONFIG_FILE_tira_test_datasets_dir"
        logInfo "Mounting shared folder with TEST datasets..."
        logInfo "$sfnametest -> $sfpathtest"
        VBoxManage sharedfolder add "$vmname-clone-$snapshotName" --name "$sfnametest" --hostpath "$sfpathtest" --readonly --automount
    fi

    # Start cloned copy.
    VBoxManage modifyvm "$vmname-clone-$snapshotName" --audio none # temporary fix for "VBoxManage: error: The specified string / bytes buffer was to small. Specify a larger one and retry. (VERR_CFGM_NOT_ENOUGH_SPACE) VBoxManage: error: Details: code NS_ERROR_FAILURE (0x80004005), component ConsoleWrap, interface IConsole"
    tira_call vm-start "$vmname-clone-$snapshotName"

    logInfo "...waiting..."
    sleep 40
    vm_info=$(get_vm_info_from_tira "$vmname")

    user=$(echo "$vm_info" | grep "userName=" | sed "s|userName=||g")
    pw=$(echo "$vm_info" | grep "userPw=" | sed "s|userPw=||g")
    host=$(echo "$vm_info" | grep "host=" | sed "s|host=||g")

    sharedFolderBase="/media/"

    if [[ "$vmname" = *"windows"* ]]; then
        logInfo "try to list network shares."
        sleep 20
        sharedFolderBase="//VBOXSVR/"
        sshpass -p "$pw" \
          ssh "${user}@$host" \
            -p "$sshport" \
            -o ConnectTimeout=120 \
            -o ConnectionAttempts=100 \
            -o UserKnownHostsFile=/dev/null \
            -o StrictHostKeyChecking=no \
            -o LogLevel=error \
            -t \
            -t "ls $sharedFolderBase"
    fi
    # Config entry $sandboxed.
    sed -i "s|$(hostname)\t$vmname|$(hostname)\t$vmname\tsandboxed|g" "$_CONFIG_FILE_tira_vms"

    # Wait for the shared folders to be accessible,
    # this is nessessary, because windows vms need a lot of time for first accessing shared folders.
    sfflag=0
    tries=0
    while [[ "$sfflag" -eq 0 ]]; do
        logInfo "Check if shares are accessible."
        # try to access shared folder
        sshpass -p "$pw" \
          ssh "$user@$host" \
            -p "$sshport" \
            -o UserKnownHostsFile=/dev/null \
            -o StrictHostKeyChecking=no \
            -o LogLevel=error \
            -t \
            -t "ls $sharedFolderBase; ls $sharedFolderBase$_CONFIG_tira_training_datasets_name/; exit"
        # if successful change sfflag to 1
        if [ "$?" -eq "0" ]; then
            sfflag=1
        else
            tries=$((tries+1))
            if (( $tries > 15 )); then
                logInfo "$user@$host: accessing shared folder failed."
                # get VM out of sandbox, if necessary
                if [[ "$sandboxed" = "true" ]]; then
                    logInfo  "unsandboxing virtual machine..."
                    tira_call vm-unsandbox -r "$hostname" "$vmname"
                fi
                exit 1
            fi
            sleep 5
        fi
    done
    
    # Remove progress file.
    rm "$progressfile"
}

#
#    Start programm with parameters.
#
main "$@"
