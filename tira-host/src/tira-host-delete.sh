#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Martin Potthast, Adrian Teschendorf, Manuel Willem, Steve Göring
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
    $(basename "$0") [flags]

Description:
    Deletes a TIRA host on a local machine or via remote control.
    You can choose if you want to keep all the VMs on the host or
    delete them.

    This script DOES NOT uninstall any packages installed during host creation.

    This script deletes the following directories (if all VMs are deleted):
        - ~/.tira/              Deletes local TIRA directory.

    This script modifies or removes the following system configuration files:
        - /etc/fstab            Removes the mount point for the TIRA NFS share.
        - /etc/dnsmasq.conf     Disables logging and conf dir.
        - /etc/dnsmasq.d/tira   Deletes this configuration file.
        - /etc/rc.local         Removes the tira-iptables.sh script.

    This script reconfigures the following system softwares to their defaults:
        - VBoxManage            Resets 'vrdeauthlibrary' to default.
        - iptables              Removes TIRA-specific routing and firewall rules.
    Watch out for any side effects of these changes!

Options:
    -h | --help           Display help documentation

Examples:
    $(basename "$0")

Authors:
    Martin Potthast
    Adrian Teschendorf
    Manuel Willem
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
#    Deletes a TIRA host on a local machine or via remote control.
#
main() {

    # Host-delete is a critical command so it prints a prompt.
    logInfo "This command deletes your TIRA host."

    yes_no_promt "Do you want to continue?"

    logTodo "first check if this host is a tira host! (mounted tira nfs, ~/.tira and so on), maybe use check_config"

    # Remove host's entry in the hosts.txt file and create a log in hostlog.txt.
    if [ -e "$_CONFIG_FILE_tira_hosts" ]; then
        sed -i "\|$(hostname)|d" "$_CONFIG_FILE_tira_hosts"
        sed -i "\|^$(hostname)|d" "$_CONFIG_FILE_tira_vms"
    fi


    # Unmount the NFS directory, delete the mount point and remove fstab entry.
    IP=$(ifconfig | grep 'inet addr:'| grep -vE '(127.0.0.1|10.*)' | cut -d: -f2 | awk '{ print $1}')
    echo "$(hostname) $IP $(date +%Y-%m-%d) deleted" | tee -a "$_CONFIG_FILE_tira_hosts_log" > /dev/null
    sudo umount "$_CONFIG_tira_nfs"
    sudo rm -rf "$_CONFIG_tira_nfs"

    sudo sed -i "\|$_CONFIG_tira_nfs|d" /etc/fstab

    # Undo VirutalBox configurations.
    VBoxManage setproperty vrdeauthlibrary default

    # Remove the entry in rc.local.
    sudo sed -i "\|$scriptPath/tira-iptables.sh|d" /etc/rc.local

    # Reset iptables to default by enabling the default firewall.
    sudo ufw enable


    # Remove dnsmasq settings.
    sudo rm -r /etc/dnsmasq.d/tira
    sudo sed -i 's|log-queries|#log-queries|g' /etc/dnsmasq.conf
    sudo sed -i 's|log-dhcp|#log-dhcp|g' /etc/dnsmasq.conf
    sudo sed -i 's|conf-dir=/etc/dnsmasq.d|#conf-dir=/etc/dnsmasq.d|g' /etc/dnsmasq.conf
    # This is not undone for security reasons. See tira-host-creat.sh.
    # sudo sed -i 's|except-interface=|#except-interface=|g' /etc/dnsmasq.conf

    sudo service dnsmasq restart
    sleep 3

    # Ask if user wants to delete the VMs on the host, otherwise exit.
    yes_no_promt "Do you want to delete the virtual tira machines on this computer?" "Host deleted! All VMs were kept."

    # "yes" was choosen: delete all TIRA VMs.

    # Obtain a list of all TIRA VMs.
    get_tira_vms vms
    # Shutdown and delete all VMs.
    for vmname in $vms; do
        logInfo "poweroff $vmname..."
        tira_call vm-stop "$vmname"
        sleep 3

        logInfo "delete $vmname..."
        tira_call vm-delete "$vmname"
        logInfo "$vmname was deleted!"
    done

    sleep 2

    # Obtain a list of all VirtualBox hostonlyifs.
    vboxnets=$(VBoxManage list hostonlyifs | grep -e '^Name:.*vboxnet' | sed "s|Name: *||g")
    # Remove all VirtualBox hostonlyifs
    for vboxnet in $vboxnets; do
        VBoxManage hostonlyif remove "$vboxnet"
    done

    # Delete local TIRA directory.
    sudo rm -rf "/home/$_CONFIG_tira_username/.tira"

    logInfo "Host deleted!"
}

#
#    Start programm with parameters.
#
main "$@"