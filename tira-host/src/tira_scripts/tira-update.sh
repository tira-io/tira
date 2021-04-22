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
    Install new tira version.

Examples:
    $(basename "$0") -u username

Authors:
    Steve Göring"
    exit 1
}

#
#    Define command line arguments and parse them.
#
DEFINE_string user "$USER" 'cvs user' 'u'
# DEFINE_boolean all false 'update all registred hosts' 'a'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Propagate new TIRA Version to a host or to all registred hosts.
#
main() {
    user=${FLAGS_user}

    logTodo "find a better way to update all hosts!"
    # all=${FLAGS_all}

    # if [ "$all" = "${FLAGS_TRUE}" ]; then
    #    logInfo "This command updates all registred tira hosts."
        # This is a critical command so it prints a prompt.
    #    yes_no_promt "Do you want to continue?" "Process aborted."

    #    while read host; do
    #        tira_call update -r "$host" -u "$user" < /dev/null
    #    done < "$_CONFIG_FILE_tira_hosts"

    #    logInfo "Done!"
    #    return
    # fi

    logInfo "Update local installed tira version."


    # Read all directorys in tira repository and extract last version.
    tira_dirs=$(cvs -d "${user}@${_CONFIG_tira_cvs_root}" rls "${_CONFIG_tira_cvs_subdir}" 2>/dev/null)
    last_tira_version=$(echo "$tira_dirs" | grep "tira.-application" | tail -1)

    cd "$scriptPath"
    logInfo "Create backup of current version (old.tar.bz2)."
    sudo rm -rf old.tar.bz2
    tmp=$(tempfile)

    sudo tar -cjvf "$tmp".tar.bz2 ./* >/dev/null

    logInfo "Delete current version."
    sudo rm -rf ./*
    sudo mv "$tmp".tar.bz2 old.tar.bz2
    sudo rm -rf "$tmp".tar.bz2

    logInfo "Last tira application version: $last_tira_version"
    logInfo "Install this version."

    # Directory switching is needed for cvs checkout, because cvs does not
    # support checking out in the current directory.
    installdir=$(basename "$(pwd)")
    cd ..
    sudo cvs -d "${user}@${_CONFIG_tira_cvs_root}" co -d "$installdir" \
        "${_CONFIG_tira_cvs_subdir}/${last_tira_version}/src/"
    cd "$installdir"

    # Set run permissions for all needed scripts.
    sudo chmod +x core/*.sh
    sudo chmod +x core/*.py
    sudo chmod +x ./*.sh
    sudo chmod +x ./*.py

    # Remove unneded CVS directories.
    find . -name "CVS" -print | sudo xargs rm -rf
    find . -name ".cvsignore" -print | sudo xargs rm -rf

    # Set permissions for tira log
    sudo touch "$_LOG_FILE"
    sudo chown "$_CONFIG_tira_username" "$_LOG_FILE"
    sudo chgrp "$_CONFIG_tira_groupname" "$_LOG_FILE"
    sudo chmod 666 "$_LOG_FILE"

    # logInfo "Run ip tables script."
    # sudo "./tira-iptables.sh" eth0

    logInfo "Done."
}

#
#    Start programm with parameters.
#
main "$@"
