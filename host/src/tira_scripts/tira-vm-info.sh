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
. "$scriptPath"/core/vboxhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="VBoxManage timeout"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <vm-name>

Description:
    Displays information on a specific VM.

Parameters:
    <vm-name>             Name of the VM

Examples:
    $(basename "$0") my_vm (local)
    $(basename "$0") -r webis46 my_vm (remote)
    $(basename "$0") -s my_vm

Authors:
    Manuel Willem
    Steve Göring"
    exit 1
}

#
#    Define command line arguments and parse them.
#
DEFINE_boolean status false 'get status of vm' 's'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Get vm information.
#
main() {
    statusFlag="${FLAGS_status}"

    if [ "$#" -eq 0 ]; then
        logError "Missing arguments see:"
        usage
    fi

    vmname="$1"

    # Every parameter is parsed and extracted: now do the job.
#    if [ "$(is_tira_vm "$vmname")" = "false" ]; then
#        logError "Vm $vmname is not available on this host."
#        return
#    fi

    # Extract info of VM $vname.
    if [ "$statusFlag" -ne "${FLAGS_TRUE}" ]; then
        logInfo "Information about local vm $vmname..."
        timeout 5s VBoxManage showvminfo "$vmname" || logError "VM info error."

    else
        # Just printout vm state.
        get_vm_state "$vmname" state
        echo "$state"
    fi

}

#
#    Start programm with parameters.
#
main "$@"