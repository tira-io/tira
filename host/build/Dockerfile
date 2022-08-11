FROM phusion/baseimage:bionic-1.0.0

ARG TIRA_PASSWORD
ARG VBOXVERSION
ARG PYCHARM_VERSION

# install prerequisite packages and virtualbox
RUN apt-get update && apt-get install -y iputils-ping net-tools ca-certificates wget tree sudo bash-completion \
    openssh-client openssh-server sshpass iptables dkms ufw iproute2 module-init-tools supervisor \
		curl dnsmasq lsb-release rdesktop python2.7 python-pip python3 python3-pip bsdmainutils rdesktop dnsutils

RUN wget https://download.virtualbox.org/virtualbox/6.1.18/virtualbox-6.1_6.1.18-142142~Ubuntu~bionic_amd64.deb -O /tmp/virtualbox-6.1_6.1.18-142142~Ubuntu~bionic_amd64.deb
RUN sudo apt-get install -y --no-install-recommends --allow-unauthenticated /tmp/virtualbox-6.1_6.1.18-142142~Ubuntu~bionic_amd64.deb

RUN wget https://download.virtualbox.org/virtualbox/6.1.18/Oracle_VM_VirtualBox_Extension_Pack-6.1.18-142142.vbox-extpack -O /tmp/Oracle_VM_VirtualBox_Extension_Pack-6.1.18-142142.vbox-extpack
RUN echo "y" | sudo VBoxManage extpack install /tmp/Oracle_VM_VirtualBox_Extension_Pack-6.1.18-142142.vbox-extpack
RUN rm /tmp/Oracle_VM_VirtualBox_Extension_Pack-6.1.18-142142.vbox-extpack && rm /tmp/virtualbox-6.1_6.1.18-142142~Ubuntu~bionic_amd64.deb

RUN python3 -m pip install --upgrade pip && python3 -m pip install grpcio==1.36.1 grpcio-tools==1.36.1 watchdog[watchmedo] pydevd-pycharm~=$PYCHARM_VERSION

RUN mkdir -m 777 mnt/input && \
    mkdir -m 777 mnt/output && \
    mkdir -m 777 /docker

# copy default tira model
RUN mkdir -p /mnt/nfs/tira

# setup tira command line tools
# todo: mount host folder directly to /usr/lib - this way we don't have to restart the container after changes
RUN mkdir /tira
RUN mkdir /usr/lib/tira
COPY src/tira_scripts /usr/lib/tira/
COPY src /tira/
COPY src/tira_host/conf/grpc_service-prod.ini /tira/tira_host/conf/grpc_service.ini
RUN sudo touch /usr/lib/tira/log.txt && \
    sudo chmod -x /usr/lib/tira/log.txt && \
    sudo chmod ugo+w /usr/lib/tira/log.txt && \
    sudo /usr/lib/tira/tira-init.sh -i && \
    sudo /usr/lib/tira/tira-autocomplete.sh -i
WORKDIR /usr/lib/tira

# create tira user
# RUN sudo python tira-setup.py user -c localhost
RUN groupadd -r -g 1010 tira && \
    useradd -m -u 1010 -g tira tira && usermod -p '$TIRA_PASSWORD' tira && \
    usermod -aG root tira && \
    usermod -aG vboxusers tira && \
    usermod -aG sudo tira

RUN echo "tira ALL=(ALL) NOPASSWD: ALL\n%tira ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

RUN	chown -R tira:tira /usr/local && \
	chmod 777 /var/run/ && \
	touch /var/log/tira_debug.txt &&\
	chown tira:tira /var/log/tira_debug.txt &&\
	mkdir -p /home/tira/.tira &&\
	mkdir "/home/tira/VirtualBox VMs" &&\
    echo "host-pc vmname=vmid-os tiraport sshport rdpport admin admin-pw user user-pw" >> /home/tira/.tira/vms.txt &&\
	mkdir /home/tira/.ssh &&\
	chown tira:tira -R /home/tira && \
    ssh-keygen -q -N '' -f /home/tira/.ssh/id_rsa
	# ln -s /usr/local/share/tira/src/tira.sh /usr/bin/tira

RUN chown -R tira:tira /mnt/nfs/tira

#COPY src/tira_host/* /home/tira/tira_host/

# RUN echo "# Allow tira to execute iptables without password entry #TIRABhv0S" | sudo tee -a /etc/sudoers > /dev/null && \
#     echo "# do not modify: #TIRABhv0S" | sudo tee -a /etc/sudoers > /dev/null && \
#     echo "Defaults:%tira  umask = 0002 #TIRABhv0S" | sudo tee -a /etc/sudoers > /dev/null && \
#     echo "Defaults:%tira  umask_override #TIRABhv0S" | sudo tee -a /etc/sudoers > /dev/null && \
#     echo "tira ALL=NOPASSWD: /sbin/iptables #TIRABhv0S" | sudo tee -a /etc/sudoers > /dev/null && \
#     echo "%tira ALL=(tira) NOPASSWD: /usr/bin/tira, /bin/touch, /bin/mkdir #TIRABhv0S" | sudo tee -a /etc/sudoers > /dev/null

USER tira
ENV USER=tira

COPY build/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sudo chmod 755 /usr/local/bin/entrypoint.sh
RUN sudo ln -s /usr/local/bin/entrypoint.sh / # backwards compat
WORKDIR /tira/tira_host
ENTRYPOINT ["/usr/local/bin/entrypoint.sh", ""]

# CMD ""
