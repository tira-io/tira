#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Adrian Teschendorf, Anna Beyer, Steve Göring
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
    $(basename "$0") [flags]

Description:
    Starts all tira VMs on a host.

Options:
    -h | --help           Display help documentation
    -r | --remote [host]  Remote control a specific host

Examples:
    $(basename "$0") (local)
    $(basename "$0") -r webis46 (remote)

Authors:
    Adrian Teschendorf
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
#    Stops all VMs on a host.
#
main() {

    # This is a critical command so it prints a prompt.
    logInfo "This command starts all VMs on this host."
    yes_no_promt "Do you want to continue?" "Process aborted."

    # Get all VMs on host.
    get_tira_vms vms
    # Start all VMs.
    for vmname in $vms; do
        tira_call vm-start "$vmname"
    done
}

#
#    Start programm with parameters.
#
main "$@"