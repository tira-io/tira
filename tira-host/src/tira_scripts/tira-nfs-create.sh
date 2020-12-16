#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Martin Potthast, Adrian Teschendorf, Steve Göring
#    TODO: Improve file permissions of the TIRA directories.

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
_BASHHELPER="included"
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="apt-get service sudo tee"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags]

Description:
    Installs NFS on a local machine, creates and registers the TIRA directory.

    This script installs the following packages:
        - nfs-kernel-server
        - openssh-server

    This script creates the following directories:
        - /srv/tira/*           Creates the TIRA directoriy structure.

    This script creates or modifies the following system configuration files:
        - /etc/exports          Adds NFS shares for the TIRA directory.

    Watch out for any side effects of these changes!

Options:
    -h | --help           Display help documentation

Example:
    $(basename "$0")

Authors:
    Martin Potthast
    Adrian Teschendorf
    Steve Göring"
    exit 1
}

export_nfs_network() {
    logTodo "hard coded network adresses"
    networks="141.54.147.0/24 141.54.159.0/24 141.54.172.0/24 141.54.178.0/24 141.54.132.0/24 127.0.0.0/24"

    for network in $networks; do
        line="$_CONFIG_tira_srv $network(rw,sync,no_subtree_check)"

        if [ ! -e /etc/exports ] || [ "$(grep -c "^$line\$" /etc/exports)" -eq 0 ]; then
            echo "$line" | sudo tee -a /etc/exports > /dev/null
        fi
    done
}

#
#    Define command line arguments and parse them.
#
FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Create TIRA directory structure and share it via NFS.
#
main() {

    # Check pre-conditions.
    if [ -d "$_CONFIG_tira_srv" ]; then
        logError "$_CONFIG_tira_srv already exists. Aborting."
        exit 1
    fi

    # NFS-create is a critical command so prompts its user for conformation.
    logInfo "This command turns this machine into a TIRA NFS sever."
    yes_no_promt "Do you wish to continue?" "Aborting."


    # Create TIRA directory structure.
    logInfo "Creating TIRA directory structure."

    logTodo "no, use CONFIG Variables, and apply '| sed' to change nfs path to server"
    sudo mkdir -p -m 777 "/srv/tira/data"
    sudo mkdir -p -m 777 "/srv/tira/data/datasets"
    sudo mkdir -p -m 777 "/srv/tira/data/datasets/test-datasets"
    sudo mkdir -p -m 777 "/srv/tira/data/datasets/test-datasets-truth"
    sudo mkdir -p -m 777 "/srv/tira/data/datasets/training-datasets"
    sudo mkdir -p -m 777 "/srv/tira/data/datasets/training-datasets-truth"
    sudo mkdir -p -m 777 "/srv/tira/data/runs"
    sudo mkdir -p -m 777 "/srv/tira/data/virtual-machine-templates"
    sudo mkdir -p -m 777 "/srv/tira/log"
    sudo mkdir -p -m 777 "/srv/tira/log/errors"
    sudo mkdir -p -m 777 "/srv/tira/log/hosts"
    sudo mkdir -p -m 777 "/srv/tira/log/virtual-machine-hosts"
    sudo mkdir -p -m 777 "/srv/tira/log/virtual-machines"
    sudo mkdir -p -m 777 "/srv/tira/model"
    sudo mkdir -p -m 777 "/srv/tira/model/datasets"
    sudo mkdir -p -m 777 "/srv/tira/model/datasets/test-datasets"
    sudo mkdir -p -m 777 "/srv/tira/model/datasets/training-datasets"
    sudo mkdir -p -m 777 "/srv/tira/model/organizers"
    sudo mkdir -p -m 777 "/srv/tira/model/runs"
    sudo mkdir -p -m 777 "/srv/tira/model/softwares"
    sudo mkdir -p -m 777 "/srv/tira/model/tasks"
    sudo mkdir -p -m 777 "/srv/tira/model/users"
    sudo mkdir -p -m 777 "/srv/tira/model/virtual-machine-hosts"
    sudo mkdir -p -m 777 "/srv/tira/model/virtual-machine-templates"
    sudo mkdir -p -m 777 "/srv/tira/model/virtual-machines"
    sudo mkdir -p -m 777 "/srv/tira/state"
    sudo mkdir -p -m 777 "/srv/tira/state/softwares"
    sudo mkdir -p -m 777 "/srv/tira/state/virtual-machines"

    (umask 000; touch $_CONFIG_tira_srv/model/virtual-machine-hosts/$_CONFIG_tira_hosts_name)
    (umask 000; touch $_CONFIG_tira_srv/model/virtual-machines/$_CONFIG_tira_vms_name)
    (umask 000; touch $_CONFIG_tira_srv/log/virtual-machine-hosts/$_CONFIG_tira_hosts_log_name)
    (umask 000; touch $_CONFIG_tira_srv/log/virtual-machines/$_CONFIG_tira_vms_log_name)


    # Install required packages: nfs-kernel-server.
    logInfo "Installing packages."
    sudo apt-get update

    if sudo apt-get -qq install "nfs-kernel-server"; then
        logInfo "nfs-kernel-server installation was successful."
    else
        logError "Error installing nfs-kernel-server - process aborted."
        exit 1
    fi

    if sudo apt-get -qq install "openssh-server"; then
        logInfo "openssh-server installation was successful."
    else
        logError "Error installing openssh-server - process aborted."
        exit 1
    fi


    # Export TIRA directory within the university networks.
    export_nfs_network


    # Start NFS server and reload the exports file.
    sudo service nfs-kernel-server start
    sleep 2

    sudo exportfs -ra

    logInfo "Done."
}

#
#    Start programm with parameters.
#
main "$@"
