#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Manuel Willem, Steve Göring
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
neededtools="VBoxManage awk cat grep column tira"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [<host-name>] [flags]

Description:
    Lists VMs on all or on a specific hosts. VMs can be filtered
    by different options.

Options:
    <host-name>           Filter the VMs by host

Examples:
    $(basename "$0") (lists all VMs registered on the NFS server)
    $(basename "$0") webis46 -S (lists all sandboxed VMs on webis46)
    $(basename "$0") webis16 -R (lists all running VMs on webis46)
    $(basename "$0") --running (lists all running VMs)

Authors:
    Manuel Willem
    Steve Göring"
    exit 1
}

#
#    Define command line arguments and parse them.
#
DEFINE_boolean all false 'List all VMs (default option)' 'A'
DEFINE_boolean running false 'List all running VMs' 'R'
DEFINE_boolean sandbox false 'List all sandboxed VMs' 'S'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Lists VMs on all or on a specific hosts. VMs can be filtered
#    by different options.
#
main() {

    hostname="$1"
    hostname_msg="on $hostname"

    all="${FLAGS_all}"
    running="${FLAGS_running}"
    sandbox="${FLAGS_sandbox}"

    # Check if just one flag is set
    c=0
    if [ "$all" = "${FLAGS_TRUE}" ]; then
        c=$((c + 1))
    fi
    if [ "$running" = "${FLAGS_TRUE}" ]; then
        c=$((c + 1))
    fi
    if [ "$sandbox" = "${FLAGS_TRUE}" ]; then
        c=$((c + 1))
    fi

    if [ "$c" = "0" ]; then
        all="${FLAGS_TRUE}"
        c=1
    fi

    if [ "$c" != "1" ]; then
        logError "Flags cannot be combined, see:"
        usage
    fi

    if [ "$hostname" = "" ]; then
        hostname_msg="general"
    fi

    # Default header, except for -R parameter.
    tmp_file=$(tempfile)
    echo "HOST | VM-NAME | SANDBOXED" > "$tmp_file"
    echo "============ | ======================== | ==================" >> "$tmp_file"
    error_message=""

    if [ "$all" = "${FLAGS_TRUE}" ]; then
        # Filter all vms that matches $hostname and
        # transform output.
        # note: if $hostname="" grep uses all lines
        grep -P "$hostname\t" < "$_CONFIG_FILE_tira_vms" \
            | awk 'BEGIN { OFS=" | " }{ print $1, $2, $3 }' >> "$tmp_file"

        error_message="No VM's $hostname_msg!"
    fi

    if [ "$running" = "${FLAGS_TRUE}" ]; then
        # Process each line of _CONFIG_FILE_tira_vms filtered by hostname
        # and try to get vm state via remote vm-info call.

        # Change header of $tmp_file.
        echo "HOST | VM-NAME | STATUS | SANDBOXED" > "$tmp_file"
        echo "============ | ======================== | ============= | ==================" >> "$tmp_file"

        grep -P "$hostname\t" < "$_CONFIG_FILE_tira_vms" \
            | while read host vmname sandboxed; do

            status=$(tira_call vm-info -r "$host" -s "$vmname" | tail -1 | tr -d '\r')

            echo "$host | $vmname | $status | $sandboxed" >> "$tmp_file"
        done

        error_message="No running VM's $hostname_msg!"
    fi

    if [ "$sandbox" = "${FLAGS_TRUE}" ]; then
        # Filter all vms that matches $hostname and
        # all sandboxed vms and
        # transform output.
        grep -P "$hostname\t" < "$_CONFIG_FILE_tira_vms" \
            | grep -P "\tsandboxed" \
            | awk 'BEGIN { OFS=" | " }{ print $1, $2, $3 }' >> "$tmp_file"

        error_message="No sandboxed VM's $hostname_msg!"
    fi

    # If there was no error, printout nice formatted summary.
    if [ "$(wc -l < "$tmp_file")" = "2" ]; then
        # Error case, because in $tmp_file there are just the two header lines stored.
        logError "$error_message"
    else
        logInfo "Summary:"
        # Print collected values in a nice way.
        column -t -s' ' "$tmp_file"
    fi

    rm "$tmp_file" 2> /dev/null
}

#
#    Start programm with parameters.
#
main "$@"