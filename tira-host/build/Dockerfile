FROM phusion/baseimage:bionic-1.0.0

ARG TIRA_PASSWORD=tira
ENV TIRA_PASSWORD=$TIRA_PASSWORD

# install prerequisite packages and virtualbox
RUN apt-get update && apt-get install -y iputils-ping net-tools ca-certificates wget tree sudo bash-completion \
    openssh-client openssh-server sshpass iptables dkms ufw iproute2 module-init-tools \
		curl dnsmasq lsb-release rdesktop python2.7 python-pip bsdmainutils rdesktop dnsutils

RUN echo "deb http://download.virtualbox.org/virtualbox/debian $(lsb_release -cs) contrib" \
         >> /etc/apt/sources.list.d/virtualbox.list
RUN wget -q https://www.virtualbox.org/download/oracle_vbox_2016.asc -O- | sudo apt-key add -

RUN apt-get update && apt-get install -y --no-install-recommends --allow-unauthenticated virtualbox-5.2
RUN wget http://download.virtualbox.org/virtualbox/5.2.34/Oracle_VM_VirtualBox_Extension_Pack-5.2.34-133893.vbox-extpack

RUN echo "y" | vboxmanage extpack install \
    Oracle_VM_VirtualBox_Extension_Pack-5.2.34-133893.vbox-extpack

RUN	rm Oracle_VM_VirtualBox_Extension_Pack-5.2.34-133893.vbox-extpack
RUN echo "y" | apt-get install sudo virtualbox-dkms

RUN mkdir -m 777 mnt/input && \
    mkdir -m 777 mnt/output && \
    mkdir -m 777 /docker

# copy default tira model
RUN mkdir -p /mnt/nfs/tira
COPY build/initial-docker-tira-model /mnt/nfs/tira/

# setup tira command line tools
# mount host folder directly to /usr/lib - this way we don't have to restart the container after changes
RUN mkdir /usr/lib/tira
COPY src /usr/lib/tira/
RUN sudo touch /usr/lib/tira/log.txt && \
    sudo chmod -x /usr/lib/tira/log.txt && \
    sudo chmod ugo+w /usr/lib/tira/log.txt && \
    sudo /usr/lib/tira/tira-init.sh -i && \
    sudo /usr/lib/tira/tira-autocomplete.sh -i
WORKDIR /usr/lib/tira

# create tira user
# RUN sudo python tira-setup.py user -c localhost
RUN groupadd -r -g 1010 tira && \
    useradd -m -u 1010 -g tira tira && echo "tira:$TIRA_PASSWORD" | chpasswd && \
    usermod -aG root tira && \
    usermod -aG vboxusers tira && \
    usermod -aG sudo tira

RUN echo "tira ALL=(ALL) NOPASSWD: ALL\n%tira ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

RUN	chown -R tira:tira /usr/local && \
	chmod 777 /var/run/ && \
	touch /var/log/tira_debug.txt &&\
	chown tira:tira /var/log/tira_debug.txt &&\
	mkdir -p /home/tira/.tira &&\
    touch /home/tira/.tira/vms.txt &&\
	mkdir /home/tira/.ssh &&\
	chown tira:tira -R /home/tira && \
    ssh-keygen -q -N '' -f /home/tira/.ssh/id_rsa
	# ln -s /usr/local/share/tira/src/tira.sh /usr/bin/tira

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
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# CMD ""
