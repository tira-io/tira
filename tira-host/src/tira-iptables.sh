#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Martin Tippmann, Adrian Teschendorf, Steve Göring

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="iptables sudo sysctl"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") <eth>

Description:
    Sets up firewall rules for the system and the virtual machines.
    Portforwarding, NAT and filtering for the virtual machines is configured.

Parameters:
    <eth>   required    Specifies the network interface that is used to
                        do NAT from virtual machines to the wider network.

Examples:
    $(basename "$0") eth1

Further reading:
    http://www.frozentux.net/iptables-tutorial/iptables-tutorial.html (!)
    http://www.karlrupp.net/de/computer/nat_tutorial
    http://netfilter.org/documentation/HOWTO/
    http://www.linuxhomenetworking.com/wiki/index.php/Quick_HOWTO_:_Ch14_:_Linux_Firewalls_Using_iptables

Debug:
    Using these commands you can check if the script had success in setting up
    the iptable rules, or debug problems:
    Show the iptables filter table:
        iptables -L -v -n --line-numbers
    Show the iptables nat table:
        iptables -L -v -n -t nat --line-numbers

Authors:
    Martin Tippmann
    Adrian Teschendorf
    Steve Göring"
    exit 1
}

#
#    Creates a TIRA host on a local machine or via remote control.
#
main() {

    # Terminate if the interface is missing
    if [ -z "$1" ]; then
        logError "You need to specify the network interface controller."
        usage
    fi

    eth="$1"
#    if [[ $(hostname) = *"betaweb"* ]]; then
#        logTodo "for betaweb no ip table rules will be applied"
#        exit 0
#    fi

    # 0 PREPARE AND RESET IPTABLES RULES

    # Enables IP forwarding between different network interfaces.
    # Prerequisite for doing network address translation.
    sysctl -w net.ipv4.ip_forward=1

    if [ -z ${TIRA_IPTABLES_PRESERVE_EXISTING+x} ]; then
        # Reset iptables to defaults.
        #
        # Flush all rules in the filter table.
        iptables -F
        # Flush all rules in the nat table.
        iptables -F -t nat
        # Flush all rules in the mangle table.
        iptables -F -t mangle
        # Deletes all user defined chains.
        iptables -X
    fi


    # 1 SET UP PACKET FILTERING
    #
    # Read the links in the FURTHER READING section
    # if nothing here seems to makes sense!

    # 1.1 DEFAULT POLICY
    #
    # The default policy for iptables - every packet that matches no rule will be
    # subject to these defaults.

    # Drop everything in the INPUT chain
    # (Disallow incoming packets on each interface).
    iptables -P INPUT DROP

    # Drop everything in the FORWARD chain
    # (disallow forwarding packets between interfaces).
    iptables -P FORWARD DROP

    # Allow everything on the OUTPUT chain
    # (Allow outgoing data on all interfaces).
    iptables -P OUTPUT ACCEPT

    # 1.2 MINIMAL RULES

    # These rules make life easier without hampering security.

    # Allow all traffic on the loopback interface.
    iptables -A INPUT -i lo -j ACCEPT

    # Allow icmp (ping) on all interfaces.
    iptables -A INPUT -p icmp -j ACCEPT

    # Allow already established connections.
    # Any outgoing traffic won't work without allowing the answer back in.
    iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

    # 1.3 WEBIS FIREWALL RULES.

    # Allow all incoming connections from the university network.

    iptables -A INPUT -i eth+ -s 141.54.0.0/16 -j ACCEPT
    iptables -A INPUT -i em+ -s 141.54.0.0/16 -j ACCEPT

    # Allow SSH access from everywhere.
    iptables -A INPUT -i eth+ -p tcp --dport 22 -j ACCEPT
    iptables -A INPUT -i em+ -p tcp --dport 22 -j ACCEPT
    # 1.4 VIRTUAL MACHINE RULES

    # These rules control the allowed communications for the virtual machines.

    # Allow incoming connections for the vboxnet interfaces
    # NOTE: virtual machines are still not reachable from the outside, packets
    # must pass the FORWARD chain and are filtered there.
    iptables -I INPUT -i vboxnet+ -j ACCEPT

    # Allow forwarding packets to eth+ for all virtual machines
    # this rule allows outgoing traffic to reach the actual network interface (eth+)
    # NOTE: Don't confuse this with the OUTPUT rule, here we control if packets
    # are allowed to travel between interfaces. They are allowed to leave the interface
    # by default as per the default policy (see 1.1).
    iptables -A FORWARD -i vboxnet+ -o eth+ -j ACCEPT

    # Allow forwarding of SSH traffic to the virtual machines.
    iptables -A FORWARD -i vboxnet+ -p tcp --dport 22 -j ACCEPT

    # Allow connections from the network interface to reach the
    # virtual machines.
    iptables -A FORWARD -i eth+ -o vboxnet+ -j ACCEPT
    iptables -A FORWARD -i em+ -o vboxnet+ -j ACCEPT

    # Allow access to the forwarded (see 3) ports from outside.
    iptables -A INPUT -i eth+ -p tcp --dport 44400:44450 -j ACCEPT
    iptables -A INPUT -i em+ -p tcp --dport 44400:44450 -j ACCEPT

    # Allow access to the RDP ports for the virtual machines
    # these actually listen on the eth+ interfaces.
    iptables -A INPUT -i eth+ -p tcp --dport 55500:55550 -j ACCEPT
    iptables -A INPUT -i em+ -p tcp --dport 55500:55550 -j ACCEPT


    # 2 MASQUERADING

    # This sets up the physical network cards as router for outgoing packets
    # here the internal ip addresses are rewritten into the ip address of the
    # physical network card. Also called network address translation.

    # Use eth+ as router for outgoing packets and do network adress translation.
    iptables -A POSTROUTING -o eth+ -t nat -j MASQUERADE
    iptables -A POSTROUTING -o em+ -t nat -j MASQUERADE


    # 3 PORTFORWARDING

    # This sets up forwards from external ports to internal ip adresses
    # from virtual machines

    # Get the numerical part of the hostname e.g. 60 for webis60
    # the hostnumber is part of the ip-adress from the virtual machines
    # 10.<hostnumber>.<vm-interface>.100 is the adress of a machine.
    logTodo "duplicated code!, and webis specific"
    #hostnumber=$(hostname -s | awk 'sub("^[^1-9]+","",$0)')  ## remove leading word and leading zeroes from hostname
    #if [ "$hostnumber" = "" ]; then
        hostnumber="0"
    #fi

    # For the first 50 interfaces set up port forwarding to the virtual machine ssh port
    # we just use ports from 44401 to 44450 for ssh
    # this only applies to external connections as it happens in the PREROUTING TABLE.
    for i in $(seq 1 50); do
        iptables -t nat -A PREROUTING -i eth+ -p tcp --dport "$(printf "444%02d\n" "$i")" -j DNAT --to "10.$hostnumber.$i.100:22";
        iptables -t nat -A PREROUTING -i em+ -p tcp --dport "$(printf "444%02d\n" "$i")" -j DNAT --to "10.$hostnumber.$i.100:22";
    done

    # Get the ip adress of the specified network interface.
    ip_eth=$(ifconfig "$eth" | awk /"$eth"/'{next}//{split($0,a,":");split(a[2],a," ");print a[1];exit}')

    # The PREROUTING table is skipped for local packets (???) so we need to add the
    # portforwarding rules again in the nat OUTPUT table to be able to access virtual machines
    # on the forwarded ports on the local machine.
    # This allows connecting to the forwarded port 444xx locally!
    for i in $(seq 1 50); do
        iptables -t nat -A OUTPUT -d "$ip_eth" -p tcp --dport "$(printf "444%02d\n" "$i")" -j DNAT --to "10.$hostnumber.$i.100:22";
    done

    # 4 TIRA PORT CONFIGURATION FOR WEBIS60
    #
    # Forward port 33300 to the tira instance.
    logTodo "special for webis 60?"
    if [ "$hostnumber" -eq 60 ]; then
        iptables -t nat -A PREROUTING -i eth+ -p tcp --dport 33300 -j DNAT --to 10.60.0.100:2306
    fi


    # 5 LOGGING
    # We add a logging target at the end of the INPUT and FORWARD chains.
    # The packets will be dropped after reaching that point (see default policy 1.1).
    # Just before that happens we log them, to be able to debug problems.
    # Use tail -f /var/log/syslog to follow messages.
    iptables -A INPUT -j LOG --log-prefix "ipt-INPUT: "
    iptables -A FORWARD -j LOG --log-prefix "ipt-FORWARD: "

    # 6 MULTI-GATEWAY WORKAROUND
    #
    # Add local routes to our routing table because we use multiple gateways.
    #
    # some context:
    # http://wiki.ubuntuusers.de/Multiple_Uplink_Routing
    # http://www.tldp.org/HOWTO/Adv-Routing-HOWTO/lartc.rpdb.multiple-links.html
    # see /etc/network/interfaces for the current configuration.
    #
    # The network configuration on webis16-19,60,61 uses multiple gateways and a
    # special routing table to these interfaces. As this bypassing the system default
    # routingtable we need to add information about the virtual machine interfaces
    # and their networks to these special tables as the default one is not used here.
    if grep -q rt2 /etc/iproute2/rt_tables; then
        for i in $(seq 0 50); do
            ip route add "10.$hostnumber.$i.0/24" dev "vboxnet$i" table rt3 2> /dev/null;
            ip route add "10.$hostnumber.$i.0/24" dev "vboxnet$i" table rt2 2> /dev/null;
        done
        # Flush the cache.
        ip route flush cache
    fi
}

#
#    Start programm with parameters.
#
main "$@"



