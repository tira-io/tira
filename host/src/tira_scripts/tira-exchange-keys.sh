#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Steve Göring

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="ssh"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] [hostname]

Description:
    Exchange ssh keys to all registred tira hosts
    or to specific hostname.

Examples:
    $(basename "$0")

Authors:
    Steve Göring"
    exit 1
}

#
#    Define command line arguments and parse them.
#
DEFINE_string password '' 'password' 'p'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Exchange  tira user SSH keys between
#    two clients (host1, host2) with password.
#
#    \params $1 host1
#    \params $2 host2
#    \params $3 tira user password for each hosts
#
#    Example call:
#       exchange_keys "$this_host" "$hostname" "$tirapw"
#
exchange_keys() {
    this_host="$1"
    hostname="$2"
    tirapw="$3"

    logInfo "Key exchange from $this_host to $hostname."
    output=$( (ssh_key_exchange "$_CONFIG_tira_username@$hostname" "$tirapw") 2>&1)

    if [ "$output" = "" ]; then
        logInfo "Key exchange from $hostname to $this_host."
        # Run function ssh_key_exchange on $hostname via ssh.
        typeset -f | ssh "$_CONFIG_tira_username@$hostname"  \
            -o UserKnownHostsFile=/dev/null \
            -o StrictHostKeyChecking=no \
            -o LogLevel=error \
            "$(cat); ssh_key_exchange $_CONFIG_tira_username@$this_host $tirapw"
    else
        logError "Problems with $hostname (permission denied," \
            "$_CONFIG_tira_username user does not exists or wrong password)."
    fi
}

#
#    Exchange SSH Keys with all registred TIRA hosts.
#
main() {

    logInfo "SSH key exchange."

    this_host="$(hostname)"
    tirapw="${FLAGS_password}"
    logInfo "$_CONFIG_FILE_tira_hosts"

    if [ ! -f "$_CONFIG_FILE_tira_hosts" ]; then
        logError "$_CONFIG_FILE_tira_hosts does not exist. Exit."
        exit 1
    fi
    if [ "$tirapw" = "" ]; then
        read_password "Please enter tira password for each tira host:" tirapw
    fi

    # Exchange key with all tira hosts.
    if [ "$1" = "" ]; then
        logInfo "Exchange keys with all registred hosts"
        # Iterate over all registred host.
        while read hostname; do
            exchange_keys "$this_host" "$hostname" "$tirapw"
        done < "$_CONFIG_FILE_tira_hosts"
        exit 0
    fi

    # Exchange key with specific host.
    hostname="$1"
    exchange_keys "$this_host" "$hostname" "$tirapw"
    exchange_keys "$this_host" "localhost" "$tirapw"
}

#
#    Start programm with parameters.
#
main "$@"
