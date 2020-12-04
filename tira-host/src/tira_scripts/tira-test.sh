#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Steve Göring, Martin Potthast
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
neededtools="cvs tar"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags]

Description:
    Test all vm settings.

Examples:
    $(basename "$0") -u username

Authors:
    Steve Göring
    Martin Potthast"
    exit 1
}

#
#    Define command line arguments and parse them.
#
DEFINE_string vm "" 'vm to check, default: check all vms' 'V'
DEFINE_string vmlist "" 'vmlist to check, default: check all vms' 'L'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Check that dkms is installed.
#    \param $1 vmname
#
check_dkms_installed_on_ubuntu() {
    vmname="$1"
    res=$($scriptPath/tira-vm-ssh.sh "$vmname" -C 'dpkg -l | grep -q "dkms"; echo $?' 2> /dev/null < /dev/null | tail -1)

    if [[ "$res" = "0"* ]]; then
        logOK "$FUNCNAME"
    else
        logFail "$FUNCNAME vm: $vmname"
    fi
}

#
#    Check that vboxadd kernel modul is loaded.
#    \param $1 vmname
#
check_vboxadd_module_ubuntu() {
    vmname="$1"
    res=$($scriptPath/tira-vm-ssh.sh "$vmname" -C 'lsmod | grep -q "vboxadd"; echo $?' 2> /dev/null < /dev/null | tail -1)

    if [[ "$res" = "0"* ]]; then
        logOK "$FUNCNAME"
    else
        logFail "$FUNCNAME vm: $vmname"
    fi
}

#
#    Check grub timeout settings.
#    \param $1 vmname
#
check_grub_timeout_settings_ubuntu() {
    vmname="$1"
    res=$($scriptPath/tira-vm-ssh.sh "$vmname" -C 'grep -xq "GRUB_RECORDFAIL_TIMEOUT=1" /etc/default/grub; echo $?' 2> /dev/null < /dev/null | tail -1)

    if [[ "$res" = "0"* ]]; then
        logOK "$FUNCNAME"
    else
        logFail "$FUNCNAME vm: $vmname"
    fi
}

#
#    Check vbox shared folder access for ubuntu.
#    \param $1 vmname
#
check_access_shares_ubuntu() {
    vmname="$1"
    res=$($scriptPath/tira-vm-ssh.sh "$vmname" -C 'ls -1 /media/training-datasets/* > /dev/null 2>&1; echo $?' 2> /dev/null < /dev/null | tail -1)

    if [[ "$res" = "0"* ]]; then
        logOK "$FUNCNAME"
    else
        logFail "$FUNCNAME vm: $vmname"
    fi
}

#
#    Check vbox shared folder access for ubuntu.
#    \param $1 vmname
#
check_access_shares_windows() {
    vmname="$1"
    res=$($scriptPath/tira-vm-ssh.sh "$vmname" -C 'ls -1 //VBOXSVR/training-datasets/* > /dev/null 2>&1; echo $?' 2> /dev/null < /dev/null | tail -1)

    if [[ "$res" = "0"* ]]; then
        logOK "$FUNCNAME"
    else
        logFail "$FUNCNAME vm: $vmname"
    fi
}

#
#    Check nodns settings for ssh on ubuntu.
#    \param $1 vmname
#
check_ssh_nodns_ubuntu() {
    vmname="$1"
    res=$($scriptPath/tira-vm-ssh.sh "$vmname" -C 'grep -q "UseDNS no" /etc/ssh/sshd_config; echo $?' 2> /dev/null < /dev/null | tail -1)

    if [[ "$res" = "0"* ]]; then
        logOK "$FUNCNAME"
    else
        logFail "$FUNCNAME vm: $vmname"
    fi
}

#
#    Check nodns settings for ssh on windows.
#    \param $1 vmname
#
check_ssh_nodns_windows() {
    vmname="$1"
    res=$($scriptPath/tira-vm-ssh.sh "$vmname" -C 'grep -q "UseDNS no" /etc/sshd_config; echo $?' 2> /dev/null < /dev/null | tail -1)

    if [[ "$res" = "0"* ]]; then
        logOK "$FUNCNAME"
    else
        logFail "$FUNCNAME vm: $vmname"
    fi
}

#
#    Check ubuntu vm settings.
#    \param $1 vmname
#    \param $2 vm info
#
check_ubuntu_vm() {
    vmname="$1"
    check_access_shares_ubuntu "$vmname"
    check_ssh_nodns_ubuntu "$vmname"
    check_grub_timeout_settings_ubuntu "$vmname"
    check_dkms_installed_on_ubuntu "$vmname"
}

#
#    Check ubuntu vm settings.
#    \param $1 vmname
#    \param $2 vm info
#
check_windows_vm() {
    vmname="$1"
    check_access_shares_windows "$vmname"
    check_ssh_nodns_windows "$vmname"
}

#
#    Check one vm.
#    \param $1 vmname
#
check_vm() {
    vmname="$1"
    vm_info=$(get_vm_info_from_tira "$vmname" 2> /dev/null)

    if [ "$vm_info" != "" ]; then
        host=$(echo "$vm_info" | grep "host" | sed "s|host=||g")
        vm_full_name=$(echo "$vm_info" | grep "vmName" | sed "s|vmName=||g")
        status=$(tira_call vm-info -r "$host" -s "$vm_full_name" 2> /dev/null < /dev/null | tail -1 | grep "running")
        if [ "$status" != "" ]; then
            if [[ "$vm_full_name" = *"ubuntu"* ]]; then
                check_ubuntu_vm "$vmname" "$vm_info"
            else
                check_windows_vm "$vmname" "$vm_info"
            fi
        else
            logWarn "VM $vmname is not running."
        fi
    else
        logWarn "VM $vmname is not registered correctly."
    fi
}

#
#    Check all vm settings.
#
main() {
    vm="${FLAGS_vm}"
    vmlist="${FLAGS_vmlist}"

    if [ "$vm" != "" ] && [ "$vmlist" != "" ]; then
        logError "Parameters are wrong, it is not possible to specify a list and a single vm for a check."
        return 1
    fi
    if [ "$vmlist" != "" ] && [ ! -f "$vmlist" ]; then
        logError "$vmlist is not a valid file."
        return 1
    fi

    # Check vm list.
    if [ "$vmlist" != "" ]; then
        logInfo "check list"
        tmp_file="$vmlist"

        while read vmname; do
            logInfo "$vmname"
            check_vm "$vmname"
        done < "$tmp_file"

        return 0
    fi

    # Check all virtual machines, if there was no vm as parameter.
    if [ "$vm" = "" ]; then
        tmp_file=$(tempfile)
        awk 'BEGIN { FS=" " }{ print $2}' < "$_CONFIG_FILE_tira_vms" > "$tmp_file"

        while read vmname; do
            logInfo "$vmname"
            check_vm "$vmname"
        done < "$tmp_file"
        rm -rf "$tmp_file"
        return 0
    fi

    # Default case: check one vm.
    check_vm "$vm"
}

#
#    Start programm with parameters.
#
main "$@"

