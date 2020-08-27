#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Bashhelper functions.
#
#    Project TIRA/general
#    Author: Steve Göring, Martin Potthast
#

#
#    Read config file.
#
thisscriptpath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. $thisscriptpath/config.sh

#
#    Debug infos and checks.
#
debug() {
    if [[ $_DEBUG = true ]]; then
        return 0
    else
        return 1
    fi
}

#
#    Unittests.
#
unittest() {
    if [[ $_UNITTEST = true ]]; then
        return 0
    else
        return 1
    fi
}

#
#    Logging macros,
#        e.g. for errors, warnings, information, debug, ...
#

#
#    Printout error to stderr.
#
logError() {
    echo -e "\033[91m[ERROR]\033[0m $@ "
}

#
#    Printout info message.
#
logInfo() {
    echo -e "\033[92m[INFO]\033[0m  $@"
}

#
#    Printout debug info if debug enabled.
#
logDebug() {
    if debug; then
        echo -e "\033[94m[DEBUG]\033[0m $@"
    fi
}

#
#    Printout warning.
#
logWarn() {
    echo -e "\033[96m[WARN]\033[0m  $@"
}

#
#    Printout todo things.
#
logTodo() {
    echo -e "\033[35m[TODO]\033[0m  $@"
}

#
#    Printout OK message.
#
logOK() {
    echo -e "\033[92m[ OK ]\033[0m  $@ "
}

#
#    Printout FAIL message.
#
logFail() {
    echo -e "\033[91m[FAIL]\033[0m  $@ "
}

logCall() {
    echo "$(date) : $@" >> "$_LOG_FILE"
}

disable_log_level() {
    for level in $@; do
        eval "log$level() {
            return
        }"
    done
}


#
#    Checks if needed tools are available.
#
#    \params $@ list of tools
#    Example call:
#        checktools "bash nano"
#
check_tools() {
    for tool in $@; do
        which $tool > /dev/null

        if [[ "$?" -ne 0 ]]; then
            logError "$tool is not installed."
            exit 1
        fi
    done
    logDebug "Each needed tool ($@) is installed."
}

#
#    Check config files/dirs, that are declared in config.sh.
#
check_config() {
    for var_name in ${!_CONFIG_FILE_*}; do
        eval "conf_file=\$$var_name"
        if [ ! -f "$conf_file" ] && [ ! -d "$conf_file" ]; then
            logError "$conf_file not found, stored in $var_name!"
            return
        fi
    done
    logDebug "Configuration paths/files are ok."
}

#
#    Reads a password from stdin.
#
#    \params $1 promt message
#    \params $2 name of result variable
#    Example call:
#        read_password "Please insert your secret password ;)" passwordvar
#
read_password() {
    __resultvar="$2"
    logInfo "$1"
    read -s pw
    eval "$__resultvar=\"$pw\""
}

#
#    Reads (y)es or (n) from stdin, exit if 'y' was not choosen.
#
#    \params $1 promt message
#    \params $2 message for "no" case
#    Example call:
#        yes_no_promt "Is bash not wunderful?"
#
yes_no_promt() {
    logInfo "$1 [y|n]: "
    read yesno

    if [ "$yesno" = n ]; then
        logInfo "$2"
        exit 1
    fi

    if [ "$yesno" != n ] && [ "$yesno" != y ]; then
        logError "Error, usage: [y|n]"
        exit 1
    fi
}

#
#    SSH key exchange.
#
#    \params $1 user at host
#    \params $2 user password
#    Example call:
#        ssh_key_exchange "myuser@mypc" "mysecretpassword"
#
ssh_key_exchange() {
    userathost="$1"
    pw="$2"
    # create a ssh key if there is no one
    if [ ! -f ~/.ssh/id_rsa ]; then
        logInfo "Rsa key does not exist, create one."
        ssh-keygen -N "" -f ~/.ssh/id_rsa
    fi
    logTodo "whoever are debugging this script, check the permissions of .ssh/authorized_keys. 'It never happened' -- Yar to Data (The Naked Now) " 
    cat ~/.ssh/id_rsa.pub | sshpass -p "$pw" ssh "$userathost" \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no \
        -o LogLevel=error \
        "(cat > tmp.pubkey ; \
          mkdir -p .ssh ; \
          touch .ssh/authorized_keys ; \
          sed -i.bak -e '/$(awk '{print $NF}' ~/.ssh/id_rsa.pub)/d' .ssh/authorized_keys; \
          cat tmp.pubkey >> .ssh/authorized_keys ; \
          rm tmp.pubkey)"
}

#
#    Check that host is alive.
#
#    \params $1 hostname
#    \return true if host is alive, false otherwhise.
#    Example call:
#        host_alive "mypc"
#
host_alive() {
    host="$1"

    if ping -c 1 "$host" &> /dev/null; then
        echo "true"
    else
        echo "false"
    fi
}

#    Check that network interface is valid.
#
#    \params $1 interface name
#    \return true if interface is available, false otherwhise.
#    Example call:
#        network_interface_available "eth0"
#
network_interface_available() {
    found=$(grep "$1" /proc/net/dev)

    if  [ -n "$found" ] ; then
        echo "true"
    else
        echo "false"
    fi
}

#
#    Call a tira command.
#
#    \params $@ tira parmeters.
#    Example call:
#        tira_call vm-start "vmname"
#
tira_call() {
    $thisscriptpath/../tira.sh "$@"
}

#
#    Create a temporary file.
#    Filename will be printed on stdout.
#
#    Note: Ubuntu12.04 has an own tempfile function,
#    but this is not general in all linux distributions.
tempfile() {
    filename=$(date +%s | sha256sum | base64 | head -c 32 ; echo)
    echo "/tmp/$filename"
}

#
#    Get a random free tcp port
#
#    \return random free port number on stdout
#    Example:
#        get_random_port
#
get_random_port() {
    python - <<END
import socket
import random

def random_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = random.randint(1024, 40000)
    result = sock.connect_ex(('127.0.0.1', port))
    if result != 0:
        return port
    return -1

port = random_port()
while port == -1:
    port = random_port()

print(port)
END
}

#
#    Get owner of a file or directory
#
#    \params $@ file/dir
#    \return on stdout
#    Example:
#        get_owner "/home/"
#
get_owner() {
    stat -c %U "$@"
}

#
#    Get owner of a file or directory
#
#    \params $@ file/dir
#    \return on stdout
#    Example:
#        get_group "/home/"
#
get_group() {
    stat -c %G "$@"
}

#
#    Get tira vm information from nfs
#
#    \params $@ vm name or username
#    \return all stored values of vm
#    Example:
#        get_vm_info_from_tira "username"
#    or
#        get_vm_info_from_tira "username-tira-ubuntu-server-14-04-1"
#
get_vm_info_from_tira() {
    python - <<END
import os
configFile = "$_CONFIG_FILE_tira_model_virtual_machines_dir/$@.prototext"

if not os.path.isfile(configFile):
    for cf in os.listdir("$_CONFIG_FILE_tira_model_virtual_machines_dir"):
        tmpf = open("$_CONFIG_FILE_tira_model_virtual_machines_dir/" + cf, "r")
        lines = tmpf.readlines()
        tmpf.close()
        for l in lines:
            if "vmName" in l and "$@" in l:
                configFile = "$_CONFIG_FILE_tira_model_virtual_machines_dir/" + cf

if os.path.isfile(configFile):
    f = open(configFile, "r")
    userBegin = False
    currentUser = {}
    for l in f:
        l = l.strip()
        tmp = l.split(":")
        if len(tmp) == 2:
            currentUser[tmp[0].strip()] = tmp[1].replace("\"","").strip()
    if currentUser.get("vmName", "") == "$@" or currentUser.get("userName", "") == "$@":
        for k in currentUser:
            print("{0}={1}".format(k, currentUser[k]))
    f.close()
END
}

#
#    Get allowed servers from tira task definition
#
#    \params $@ task definition file
#    \return allowed hosts
#    Example:
#        get_allowed_servers_from_tira_task_definition "/srv/nfs/tira/model/tasks/author-profiling.prototext"
#
get_allowed_servers_from_tira_task_definition() {
    python - <<END
f = open("$@", "r")
for l in f:
    l = l.strip()
    tmp = l.split(":")
    if tmp[0].strip() == "allowedServers":
        host = tmp[1].replace('"', '').strip()
        if host != "":
            print(host)
f.close()
END
}

#
#    Get data server from tira dataset definition
#
#    \params $@ dataset definition file
#    \return data server
#    Example:
#        get_data_server_from_tira_dataset_definition "/srv/nfs/tira/model/datasets/vandalism-detection/wsdmcup17-vandalism-detection-training-dataset-2016-09-01.prototext"
#
get_data_server_from_tira_dataset_definition() {
    python - <<END
f = open("$@", "r")
for l in f:
    l = l.strip()
    tmp = l.split(":")
    if tmp[0].strip() == "dataServer":
        dataServerHost = tmp[1].replace('"', '').strip()
        dataServerPort = tmp[2].replace('"', '').strip()
        dataServer = ":".join([dataServerHost, dataServerPort])
        if dataServer != "":
            print(dataServer)
f.close()
END
}

#
#    Get access token from tira run definition
#
#    \params $@ run definition file
#    \return access token
#    Example:
#        get_access_token_from_tira_run_definition "/srv/tira/data/runs/wsdmcup17-vandalism-detection-training-dataset-2016-09-01/loganberry/2016-10-04-06-00-44/run.prototext"
#
get_access_token_from_tira_run_definition() {
    python - <<END
f = open("$@", "r")
for l in f:
    l = l.strip()
    tmp = l.split(":")
    if tmp[0].strip() == "accessToken":
        accessToken = tmp[1].replace('"', '').strip()
        if accessToken != "":
            print(accessToken)
f.close()
END
}

#
#    Printout settings and check configuration.
#
main() {
    if [[ -z "$_BASHHELPER"  ]]; then
        _BASHHELPER="included"
        export _BASHHELPER

        check_config

        debug && logInfo "Settings: debug=$_DEBUG, unittests=$_UNITTEST"
    fi
}

#
#    Call main with arguments.
#
main "$@"
