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
    $(basename "$0") [flags] <ovafile>

Description:
    Imports a tira VM from an ova file.

Parameters:
    <ovafile>          OVA filename

Examples:
    $(basename "$0") my_vm (local)
    $(basename "$0") -r webis46 my_vm (remote)

Authors:
    Steve Göring, Martin Potthast"
    exit 1
}

#
#    Define command line arguments and parse them.
#
FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

get_username() {
    python - <<END
param = "$@"
# TODO: This way of extracting the user name relies on its file name.
print("-".join(param.split("-")[1:-6]))
END
}

#
#    Imports a vm from an ova file.
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -eq 0 ]; then
        logError "Missing arguments see:"
        usage
    fi

    ovafile="$1"
    if [ ! -f "$ovafile" ]; then
        logError "$ovafile is not a valid file."
        exit 1
    fi

    logInfo "Import ova file."
    vmimportname=$(VBoxManage import "$ovafile" -n | grep " 1: Suggested VM name \"" | sed "s| 1: Suggested VM name \"||g" | sed "s|\"||g")
    username=$(get_username "$(basename $ovafile)")

    logInfo "extracted username: $username"
    vm_info=$(get_vm_info_from_tira "$username")

    if [ "$vm_info" = "" ]; then
        logError "VM-Name/user $vmname_or_user is not registred."
        exit 1
    fi

    logInfo "Name of imported vm: $vmimportname"
    logInfo "$username"
    logInfo "$vm_info"

    VBoxManage import "$ovafile"

    vmname=$(echo "$vm_info" | grep "vmName=" | sed "s|vmName=||g")
    VBoxManage modifyvm "$vmimportname" --name "$vmname"
}

#
#    Start programm with parameters.
#
main "$@"
