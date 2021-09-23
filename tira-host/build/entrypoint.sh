#!/bin/bash

#=== vbox_network_setup.sh
vboxmanage setproperty vrdeauthlibrary VBoxAuthSimple
vboxmanage list -l hostonlyifs | grep -q vboxnet0 || vboxmanage hostonlyif create
#=== vbox_network_setup.sh

# Configure dnsmasq
sudo sed -i 's|#log-queries|log-queries|g' /etc/dnsmasq.conf
sudo sed -i 's|#log-dhcp|log-dhcp|g' /etc/dnsmasq.conf
sudo sed -i 's|#conf-dir=/etc/dnsmasq.d|conf-dir=/etc/dnsmasq.d|g' /etc/dnsmasq.conf
# Make sure the dnsmasq service cannot be accessed from outside the machine.
# This is important in order to avoid this machine to be involuntarily used in
# DDOS attacks. This setting will not be undone by tira-host-delete.sh for
# security reasons.
sudo sed -i 's|#except-interface=|except-interface=eth0\nexcept-interface=eth1\nexcept-interface=eth2\nexcept-interface=eth3|g' /etc/dnsmasq.conf

#hostnumber=$(hostname -s | awk 'sub("betaweb","",$0)' | sed 's/^0*//' )
#if [ "$hostnumber" = "" ]; then
hostnumber="0"
#fi
# Create the virtualbox file needed for the IP tables.
tmp_file=$(tempfile)
echo "" > "$tmp_file"

for id in $(seq 1 50); do
    echo "dhcp-range=interface:vboxnet${id},10.${hostnumber}.${id}.100,10.${hostnumber}.${id}.100,255.255.255.0,5m" >> "$tmp_file"
done
sudo mv "$tmp_file" /etc/dnsmasq.d/tira

# Make sure dnsmasq has proper DNS configuration
# TODO: make dnsmasq cooperate with resolvconf properly
sudo ln -vsf /etc/resolv.conf /var/run/dnsmasq/resolv.conf

# Checking if port 53 is blocked, if so consider dnsmasq is running on the host
if [ "$(sudo netstat -plntu | grep ':53')" ]; then
  echo  'Port 53 is blocked, stopping dnsmasq.'
  sudo service dnsmasq stop
else
  sudo service dnsmasq restart
fi

if [ "$(sudo netstat -plntu | grep ':22')" ]; then
  echo  'Port 22 is blocked, changing sshd to 2222.'
  sudo sed -i 's|#Port 22|Port 2222|g' /etc/ssh/sshd_config
fi

sudo ssh-keygen -A -v
sudo service ssh start

# Don't start grpc service if started as local dev environment
if [ "$DEV" = "true" ];
then
  tail -f /dev/null
  # Start grpc service with code change tracking: when the code is changed, reload the service
  #watchmedo auto-restart --recursive --pattern="*.py" --ignore-patterns="grpc_client_test.py" --directory="/tira/tira_host" python3 -- -m grpc_service
else
  python3 grpc_service.py
fi
