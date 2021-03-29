#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Adrian Teschendorf, Steve Göring
#

#
#    Load libaries and toolkits.
#
scriptPath="$(dirname "$(readlink -f "$0")")"
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="ssh sed"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage: $(basename "$0") <command> [option] <arguments>
    (Use $(basename "$0") <command> --help to display help information for a specific command)

Description:
    This is the TIRA main script which parses all the command line inputs.
    Remote control will log in as the Tira user.

Options:
    -h | --help       Display help documentation
    -r | --remote     Use remote control

Commands:
    k8s               Run the specified command (e.g. a bash shell) in a tira environment with full admin privileges
    host-list         List all TIRA hosts
    exchange-keys     SSH Key exchange with all registred hosts (or one specific)
    run-copy-to-local Copy a run from a VM to the central run directory
    run-execute       Execute a submission for a task and retrieve the output
    run-eval          Evaluates a user's run
    start             Start all VMs on a TIRA host
    status            Display host and VM information
    stop              Stop all VMs on a TIRA host
    backup            Backup a list or all registred VMs
    import            Imports a list VMs
    vm-backup         Create a backup of a VM
    vm-import         Imports a backup of a VM
    vm-create         Create a VM for a specific user
    vm-delete         Delete a VM
    vm-info           Display VM information
    vm-list           List all VMs
    vm-metrics        Get runtime metrics of a given VM
    vm-modify         Upgrade Memory and CPU count of a VM.
    vm-restore        Recreate a VM from a snapshot
    vm-runtime-output Lists the files of the temporary output directory during run execution.
    vm-sandbox        Put VM into sandbox mode
    vm-screenshot     Take a screenshot of a specific VM and store it to /tmp
    vm-shutdown       Shuts down a given user's virtual machine via command line
    vm-snapshot       Take a snapshot of a specific VM
    vm-start          Start a VM
    vm-stop           Stop a VM
    vm-unsandbox      Take a VM out of sandbox mode
    vm-ssh            Open SSH session to vm
    vm-rdp            Open RDP session to vm
    test              Check all vm settings

Authors:
    Adrian Teschendorf
    Steve Göring"
    exit 1
}

#
#    Printout help screen of subscript.
#
#    \params $1 name of subscript (see usage)
#    \params $2 general script path
#    Example call:
#        local_script_help_screen "host-list" "$_SCRIPT_PATH"
#
local_script_help_screen() {
    script="$1"
    _SCRIPT_PATH="$2"

    # Manipulate local help screen that it fits with tira "super" script,
    # just replace "tira-" with "tira " in helpscreen.
    "$_SCRIPT_PATH/tira-$script.sh" -h  2>&1 \
        | sed "s|tira-|$(basename "$0" ".sh") |g"\
        | sed "s|$script.sh|$script|g"
}

#
#    TIRA main script which parses all the command line inputs.
#    Remote control will log in as the tira user.
#
main() {
    _SCRIPT_PATH="$scriptPath"
    # 1. case:  help or no arguments
    # tira.sh |--help| -h

    # 2. case: help for a specific sub command
    # tira.sh <command> --help| -h

    # 3. case: remote accessing
    # tira.sh <command> -r HOST ARGS

    # 4. case: local usage
    # tira.sh <comnmand> ARGS

    # 5. case:any other not valid arguments
    logCall "unchecked $(basename "$0") $@"  # write call to log file
    logInfo "tira version: $_TIRA_VERSION"

    parsed_args=$("$_SCRIPT_PATH"/tira-args.py "$@")

    eval "$parsed_args"
    logDebug "Parsed arguments: \n$parsed_args\n"

    if [ "$no_arguments" = "true" ]; then
        logError "No arguments, see"
        usage
    fi

    if [ "$error" != "" ]; then
        logError "$error"
        usage
    fi

    #   This early exit is required in case users run the k8s command
    if [ "$script" = "k8s" ]; then
        "$_SCRIPT_PATH/tira-$script.sh" $args  # Note: Don't doubleqoute $args.
        exit $?
    fi

    if [ "$help" = "true" ]; then
        logInfo "Tira help:"
        usage
    fi

    if [ "$local_help" = "true" ]; then
        logDebug "Get help screen of $script:"
        local_script_help_screen "$script" "$_SCRIPT_PATH"
        exit 1
    fi

    # Check needed min arguments for subscript.
    if [ "$has_minarg_count" != "true" ]; then
        logError "Command $script need at least $minarg_count parameters, see:\n"
        local_script_help_screen "$script" "$_SCRIPT_PATH"
        exit 1
    fi

    # Now everything is ok, that means:
    #   $cmd stores a valid command
    #   $args stores all relevant arguments for subscript (without -r HOST)
    #   $remote is true if -r was set and hostname is store in $host.
    if [ "$remote" = "true" ]; then
        logInfo "Remote call @ $host."

        hostname="$host"
        userathost="$_CONFIG_tira_username@$hostname"

        if [ "$(host_alive "$hostname")" = "false" ]; then
            logError "Host $hostname is not available or wrong, check network settings, "\
                "ping $hostname should run!"
        fi
        remote_script="tira $script $args"
        logInfo "Start $remote_script via ssh."
        # This connection may have to last for a very long time, so we set alive intervals.
        ssh "$userathost" -o UserKnownHostsFile=/dev/null \
            -o StrictHostKeyChecking=no -o TCPKeepAlive=yes -o ServerAliveInterval=60 \
            -o LogLevel=error \
            -t -t "$remote_script; exit" 2> /dev/null

        if [ "$script" = "vm-create" ]; then
            "$_SCRIPT_PATH/discourse-create-vm-group.py" $args 2>/dev/null # Note: Don't doubleqoute $args.
        fi

        exit 0
    fi

    logCall "$(basename "$0") $@"  # write call to log file

    if [ "$USER" != "$_CONFIG_tira_username" ]; then
        logWarn "Better use tira as $_CONFIG_tira_username instead as $USER."
        remote_script="tira $script $args"
        # This connection may have to last for a very long time, so we set alive intervals.
        ssh "$_CONFIG_tira_username@localhost" -X -o UserKnownHostsFile=/dev/null \
            -o StrictHostKeyChecking=no -o TCPKeepAlive=yes -o ServerAliveInterval=60 \
            -o LogLevel=error \
            -t -t "$remote_script; exit" 2> /dev/null
        exit 0
    fi

    # Now do the job local:
    "$_SCRIPT_PATH/tira-$script.sh" $args  # Note: Don't doubleqoute $args.
}

#
#    Start programm with parameters.
#
main "$@"
