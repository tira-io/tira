#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Martin Potthast, Adrian Teschendorf, Martin Tippmann, Steve Göring
#    TODO: Consider replacing dnsmasq with the tools provided by VirtualBox.

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="apt-get sudo wget service"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <nfs-server-name> <eth>

Description:
    Creates a TIRA host on a local machine.

    This script installs the following packages:
    - nfs-common
    - rdesktop
    - sshpass
    - openssh-server
    - dnsmasq
    - iptables
    - ufw
    - virtualbox-4.3
    - dkms
    - tree

    This script creates the following directories:
    - ~/.tira/              Creates local TIRA directory.

    This script creates or modifies the following system configuration files:
    - /etc/apt/sources.list Adds Oracle VirtualBox contrib, if necessary.
    - /etc/fstab            Adds a mount point for the TIRA NFS share.
    - /etc/dnsmasq.conf     Enables logging and adds a conf dir.
    - /etc/dnsmasq.d/tira   Creates this configuration file.
    - /etc/rc.local         Adds the tira-iptables.sh script for startup execution.

    This script reconfigures the following system softwares:
    - VBoxManage            Modifies 'vrdeauthlibrary' setting.
    - iptables              Adds TIRA-specific routing and firewall rules.

    Watch out for any side effects of these changes!

    Options:
        -h | --help           Display help documentation

Parameters:
    <nfs-server-name>     Name of the nfs-server logTodo should be hostname
    <eth>                 Specification of the network interface controller

Examples:
    $(basename "$0") webis16 eth0

Authors:
    Martin Potthast
    Adrian Teschendorf
    Steve Göring"
    exit 1
}

#
#    Install package with apt-get install.
#
#    \params $1 package name
#    Exanple call:
#        apt_get_install "mplayer"
#
apt_get_install() {
    if sudo apt-get -qq install "$1"; then
        logInfo "$1 installation was successful."
    else
        logError "Installing $1 failed. Aborting."
        exit 1
    fi
}

#
#    Define command line arguments and parse them.
#
FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Creates a TIRA host on a local machine or via remote control.
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -le 1 ]; then
        logError "Missing arguments see:"
        usage
    fi

    networkinterface="$2"
    if [ "$(network_interface_available "$networkinterface")" != "true" ]; then
        logError "$networkinterface does not exist. Aborting."
        exit 1
    fi

    # Host-create is a critical command so it prints a prompt.
    logInfo "This command turns this machine into a TIRA HOST."

#    yes_no_promt "Do you wish to continue?" "Process aborted."

    # Create local TIRA directory.
    logInfo "Creating TIRA directory. ($_CONFIG_tira_username password needed)"
    su "$_CONFIG_tira_username" -c "mkdir -p \"$_CONFIG_FILE_tira_local_home\""
    su "$_CONFIG_tira_username" -c "echo \"$_CONFIG_tira_local_home_log_file_header\" > \"$_CONFIG_FILE_tira_local_home/vms.txt\""


    # SETTING UP THE NFS CLIENT
    # Install nfs-common
    # logInfo "Installing packages."
    # sudo apt-get update
    # apt_get_install "nfs-common"


    hostname="$1"
    host="$hostname"
    #logTodo "webis specific and why?, host create should run just local!"
    #if [ "$hostname" != "localhost" ]; then
    #    host="$hostname.medien.uni-weimar.de"
    #fi

    # Create the mount point, mount the TIRA directory of the NFS server and make
    # the mounting persistent.
    # if [ ! -d "$_CONFIG_tira_nfs" ]; then
    #     sudo mkdir -p "$_CONFIG_tira_nfs"
    #     sudo mount "$host:/srv/tira" "$_CONFIG_tira_nfs"
    #     echo "$host:/srv/tira $_CONFIG_tira_nfs nfs rw 0 0" | sudo tee -a /etc/fstab > /dev/null
    # else
    #     logError "default TIRA NFS mount point already exists. Aborting."
    #     exit 1
    # fi

    # # Test if mounting was successful. If yes, create logs, if no, exit the script.
    # if [ "$(ls -A "$_CONFIG_tira_nfs")" ]; then

    #     if [ ! -e "$_CONFIG_FILE_tira_hosts" ] || [ "$(grep -c "$(hostname)" "$_CONFIG_FILE_tira_hosts")" -eq 0 ]; then
    #         su "$_CONFIG_tira_username" -c "hostname >> \"$_CONFIG_FILE_tira_hosts\""
    #     fi

    #     IP=$(ifconfig  | grep 'inet addr:'| grep -vE '(127.0.0.1|10.*)' | cut -d: -f2 | awk '{ print $1}')
    #     # probs
    #     su "$_CONFIG_tira_username" -c "echo \"$(hostname) $IP $(date +%Y-%m-%d) created\" >> \"$_CONFIG_FILE_tira_hosts_log\""
    #     logInfo "Mounting was successful."

    # else
    #     logError "Directory cannot be read."
    #     exit 1
    # fi


    # # Install required packages.
    # if [ "$(grep -c "virtualbox" /etc/apt/sources.list)" -eq 0 ]; then
    #     echo "deb http://download.virtualbox.org/virtualbox/debian precise contrib" | sudo tee -a /etc/apt/sources.list
    #     wget -q http://download.virtualbox.org/virtualbox/debian/oracle_vbox.asc -O- | sudo apt-key add -
    #     sudo apt-get update
    # fi

    # Check if network-manager is running.
    if [ "$(sudo service network-manager status | grep "start/running")" != "" ]; then
        logInfo "Patch network-manager for compatibility with dnsmasq."
        sudo sed -i "s|dns=dnsmasq|#dns=dnsmasq|g" /etc/NetworkManager/NetworkManager.conf
        sudo service network-manager restart
	    sleep 10 # because it change something with the network configuration therefore a sleep is necessary
    else
        logInfo "There is not network-manager service on this host."
    fi

    # apt_get_install "rdesktop"
    # apt_get_install "virtualbox-4.3"
    # apt_get_install "dkms"
    # apt_get_install "tree"
    # apt_get_install "sshpass"
    # apt_get_install "openssh-server"
    # apt_get_install "dnsmasq"
    # apt_get_install "iptables"
    # apt_get_install "ufw"
    # sleep 10 # just wait if everything is complete started


    # # Install VirtualBox extension pack.
    # version=$(VBoxManage -v | awk -F'r' '{print $1}')
    # build=$(VBoxManage -v | awk -F'r' '{print $2}')
    # wget "http://download.virtualbox.org/virtualbox/$version/Oracle_VM_VirtualBox_Extension_Pack-$version-$build.vbox-extpack" -P /tmp
    # sudo VBoxManage extpack install --replace "/tmp/Oracle_VM_VirtualBox_Extension_Pack-$version-$build.vbox-extpack"


    # Configuration of Virtual Box
    logInfo "Configuring Virtual Box for user $_CONFIG_tira_username"
    logInfo "Please input tira user password:"
    su "$_CONFIG_tira_username" -c "VBoxManage setproperty vrdeauthlibrary \"VBoxAuthSimple\""
    # Create first virtualbox network interface (vboxnet0)
    VBoxManage hostonlyif create

    # Configure dnsmasq
    sudo sed -i 's|#log-queries|log-queries|g' /etc/dnsmasq.conf
    sudo sed -i 's|#log-dhcp|log-dhcp|g' /etc/dnsmasq.conf
    sudo sed -i 's|#conf-dir=/etc/dnsmasq.d|conf-dir=/etc/dnsmasq.d|g' /etc/dnsmasq.conf
    # Make sure the dnsmasq service cannot be accessed from outside the machine.
    # This is important in order to avoid this machine to be involuntarily used in
    # DDOS attacks. This setting will not be undone by tira-host-delete.sh for
    # security reasons.
    sudo sed -i 's|#except-interface=|except-interface=eth0\nexcept-interface=eth1|g' /etc/dnsmasq.conf

    # logTodo "webis specific"
    # hostnumber=$(hostname -s | awk 'sub("webis","",$0)')
    # if [ "$hostnumber" = "" ]; then
    #     hostnumber="0"
    # fi
    # Create the virtualbox file needed for the IP tables.

    tmp_file=$(tempfile)
    echo "" > "$tmp_file"

    logTodo "50 interfaces?"
    for id in $(seq 1 50); do
        echo "dhcp-range=interface:vboxnet${id},10.${hostnumber}.${id}.100,10.${hostnumber}.${id}.100,255.255.255.0,5m" >> "$tmp_file"
    done
    sudo mv "$tmp_file" /etc/dnsmasq.d/tira

    logTodo "check if dnsmasq can be started!"
    sudo service dnsmasq restart
    sleep 3

    # Execute iptables script.
    # logInfo "Creating IP tables."
    # Disabling the default firewall.
    sudo ufw disable
    # sudo bash "$scriptPath/tira-iptables.sh" "$networkinterface"

    # sudo sed -i "s|^exit 0$|bash $scriptPath/tira-iptables.sh $networkinterface|g" /etc/rc.local
    # echo "exit 0" | sudo tee -a /etc/rc.local > /dev/null

    # # SSH Key exchanging.
    # logInfo "SSH key exchange"
    # # read_password "Please enter $_CONFIG_tira_username user password:" tirapw

    # logInfo "SSH key exchange with nfs server: $host"
    # tira_call exchange-keys "$host" -p "$TIRA_PASSWORD"

    # tira_call exchange-keys -p "$TIRA_PASSWORD"

    logInfo "Tira host was successfuly created!"
}

#
#    Start programm with parameters.
#
main "$@"
