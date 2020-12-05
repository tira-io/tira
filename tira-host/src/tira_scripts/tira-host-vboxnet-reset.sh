#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Anna Beyer, Martin Potthast, Steve Göring
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
    $(basename "$0")

Description:
    Resetting host vboxnet.

Examples:
    $(basename "$0")

Authors:
    Anna Beyer
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
#    Resetting host vboxnet.
#
main() {

    # Get existing vboxnet.
    ifaces=$(VBoxManage list hostonlyifs | grep "VBoxNetworkName: HostInterfaceNetworking-"  | awk -F'-' '{ print $2 }')

    # Removing existing vboxnet.
    for iface in $ifaces; do
        logInfo "removing $iface..."
        VBoxManage hostonlyif remove "$iface" || logError "could not remove $iface"
    done

    # Get host number.
    hostnumber=$(hostname -s | awk 'sub("webis","",$0)')
    if [ "$hostnumber" = "" ]; then
        hostnumber="0"
    fi

    # Create hostonlyif vboxnet0.
    # VBoxManage hostonlyif create

    # Create and configure hostonlyif vboxnet1-vboxnet50.
    for id in $(seq 0 50); do
        iface="vboxnet$id"
        ip="10.$hostnumber.$id.1"
        logInfo "configuring $iface..."
        VBoxManage hostonlyif create || logError "could not create $iface"
        sleep 2
        VBoxManage hostonlyif ipconfig "$iface" --ip "$ip" || logError "could not set ip $ip to $iface"
    done
}

#
#    Start programm with parameters.
#
main "$@"
