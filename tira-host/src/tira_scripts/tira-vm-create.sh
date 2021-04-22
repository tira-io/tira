#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Martin Potthast, Adrian Teschendorf, Anna Beyer, Steve Göring

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="python du df cut awk"
debug && check_tools "$neededtools"  # If debug, check that tools are available.


#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <ova-file> <user-name>

Description:
    Creates a VM from a template OVA file and configures it for a user.

Parameters:
    <ova-file>            Name of the file of the operating system
    <user-name>           Choose any name for the user

Examples:
    $(basename "$0") ubuntu.ova User123 (local)
    $(basename "$0") -r webis46 win7.ova User456 (remote)

Authors:
    Martin Potthast
    Adrian Teschendorf
    Anna Beyer
    Steve Göring"
    exit 1
}

#
#    Define command line arguments and parse them.
#
DEFINE_boolean list false 'list available ova images' 'l'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Creates a VM from a template OVA file and configures it for a user.
#
main() {

    list="${FLAGS_list}"
    if [ "$list" = "${FLAGS_TRUE}" ]; then
        logInfo "List all available ova images:"
        find "$_CONFIG_FILE_tira_vm_dir" -name "*.ova" -exec basename {} \;
        exit 0
    fi

    if [ "$#" -ne 2 ]; then
        logError "Wrong number of parameters."
        usage
    fi

    sleep 10

    # Location of the ova file.
    ova="$_CONFIG_FILE_tira_vm_dir/$1"
    username="$2"

    vm_info=$(get_vm_info_from_tira "$username")
    if [ "$vm_info" != "" ]; then
        logError "$username has already a registred vm. $username are unique!"
        exit 1
    fi

    # Perform sanity checks.
    if [ ! -f "$ova" ]; then
        logError "OVA file not found: $ova"
        exit 1
    fi
    if [ $(get_owner "$ova") != "$_CONFIG_tira_username"  ]; then
        logError "Owner of $ova is not $_CONFIG_tira_username."
        exit 1
    fi
    if [ $(get_group "$ova") != "$_CONFIG_tira_username"  ]; then
        logError "Group of $ova is not $_CONFIG_tira_username."
        exit 1
    fi

    ovasize=$(du -b "$ova" | cut -f 1)
    ovasizeinflated="$((2 * ovasize))"

    diskspaceavailable=$(df -B1 -P ~/VirtualBox\ VMs/ | awk 'NR==2 {print $4}')

    if [ "$ovasizeinflated" -ge "$diskspaceavailable" ]; then
        logError "Expected inflated file size of OVA $ova bigger than available disk space in ~/VirtualBox\ VMs/: $ovasizeinflated > $diskspaceavailable"
        exit 1
    fi

    # Execute configre-vm script.
    scriptPath="$(dirname "$(readlink -f "$0")")"
    python "$scriptPath/tira-configure-vm.py" "$ova" "$username"

    # restart dnsmasq: https://github.com/tira-io/tira9-application2/issues/8
    ssh tira@localhost -C 'sudo systemctl restart dnsmasq'
}

#
#    Start programm with parameters.
#
main "$@"
