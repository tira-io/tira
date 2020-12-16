#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Steve Göring
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
neededtools="cat"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags]

Description:
    Backup a list or all registred VMs.

Examples:
    $(basename "$0") (local) -l list.txt
    $(basename "$0") (local) -a

    $(basename "$0") -r webis46 (remote)

Authors:
    Steve Göring"
    exit 1
}

#
#    Define command line arguments and parse them.
#
DEFINE_string list '' 'filename of vm list (format: hostname | vmname)' 'l'
DEFINE_boolean all false 'backup all vms' 'a'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Stops all VMs on a host.
#
main() {

    list="${FLAGS_list}"
    all="${FLAGS_all}"

    if [ "$list" = "" ] && [ "$all" = "${FLAGS_FALSE}" ]; then
        logError "This script need at least one parameter."
        usage
    fi

    tmp_file=$(tempfile)

    if [ "$list" != "" ]; then
        logInfo "This command creates backups of all VMs stored in file $list."
        sed "s/ *| */|/g" "$list" \
            | awk 'BEGIN { FS="|" }{ if (NF > 1) { print $1, $2}}' \
            > "$tmp_file"
    fi
    if [ "$all" = "${FLAGS_TRUE}" ]; then
        logInfo "This command creates backups of all registred VMs."
        awk 'BEGIN { FS=" " }{ print $1, $2}' < "$_CONFIG_FILE_tira_vms" \
            > "$tmp_file"
    fi

    # This is a critical command so it prints a prompt.
    yes_no_promt "Do you want to continue?" "Process aborted."

    # Process each vm.
    while read host vmname; do
        # Check if it is a valid host.
        hostmatch=$(grep "$host" < "$_CONFIG_FILE_tira_hosts")
        if [ "$hostmatch" = "" ]; then
            logWarn "$host is not registred, ignoring."
            continue
        fi

        # Check if it is a valid vmname.
        vmmatch=$(grep "$vmname" < "$_CONFIG_FILE_tira_vms" | grep "$host")
        if [ "$vmmatch" = "" ]; then
            logWarn "$vmname is not registred on $host, ignoring."
            continue
        fi

        # Extract username from $vmname.
        user="$(echo "$vmname" | cut -d '-' -f 1)"
        logInfo "Processing $vmname on $host of user $user."

        tira_call vm-backup -r "$host" "$vmname" "$user" < /dev/null
        logInfo "Done!"

    done < "$tmp_file"

    rm -rf "$tmp_file"
}

#
#    Start programm with parameters.
#
main "$@"
