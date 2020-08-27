#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Martin Potthast, Steve Göring
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
neededtools="sshpass"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") <runName> <inputDatasetName> <user> <userpw> <host> <sshport> <os>

Description:
    Copies the run from the virtual machine to the local run directory.

Options:
    -h | --help           Displays this help
    -r | --remote [host]  Remote control a specific host

Parameter:
    <runName>
    <inputDatasetName>
    <user>
    <userpw>
    <host>
    <sshport>
    <os>

Authors:
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
#    Copies the run from the virtual machine to the local run directory.
#
main() {

    # Check number of parameters.
    if [ "$#" -ne 7 ]; then
        logError "Wrong amount of parameters: $# but expected 7, see:"
        usage
    fi

    runDir="$_CONFIG_FILE_tira_runs_dir"

    runName="$1"
    inputDatasetName="$2"
    user="$3"
    userpw="$4"
    host="$5"
    sshport="$6"
    os="$7"

    # Define run directory on VM according os.
    if [ "$os" = "ubuntu" ] || [ "$os" = "fedora" ]; then
        vmRunDir="/tmp/$user/$runName"
    elif [ "$os" = "windows" ]; then
        vmRunDir="C:/Windows/Temp/$user/$runName"
    fi

    # Copy vmRunDir from vm to localhost.
    logInfo "$user@$host: copying $vmRunDir from VM..."
    localRunDir="$runDir/$inputDatasetName/$user"

    mkdir -p "$localRunDir"
    # Bugfix for the subsequent scp command: http://stackoverflow.com/questions/12440287/scp-doesnt-work-when-echo-in-bashrc
    # The proposed solutions all solve the problem within .bashrc, but we cannot
    # rely on users acting this way. This is why we go the brute force path and
    # delete the .bashrc before copying. We may do this, since the VM has been
    # cloned and the clone will be deleted, anyway.
    sshpass -p "$userpw" \
      ssh "$user@$host" \
        -p "$sshport" \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no \
        -o LogLevel=error \
        -t \
        -t "rm ~/.bashrc; exit;"
    sshpass -p "$userpw" \
      scp \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no \
        -o LogLevel=error \
        -r \
        -P "$sshport" "$user@$host:$vmRunDir" "$localRunDir"

    # Determine size of the run.
    (du -sb "$localRunDir/$runName" && du -hs "$localRunDir/$runName") | cut -f1 > "$localRunDir/$runName/size.txt"

    # Runs must be readable and writable by the tira user and the tira group.
    chmod -R ug+rw "$localRunDir/$runName"
    chmod ug+rw "$localRunDir"

    logInfo "$user@$host: done."
}

#
#    Start programm with parameters.
#
main "$@"
