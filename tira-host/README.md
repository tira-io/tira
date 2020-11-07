TIRA 9
======
  - [Installing a TIRA Host](#installing-a-tira-host)
  - [Installing a TIRA Server](#installing-a-tira-server)
  - [Running a dockerized TIRA Host](#running-a-dockeridzed-tira-host)
  - [TIRA project Wiki](https://github.com/tira-io/tira/wiki)

Installing a TIRA Host
---------------------

1. Install prerequisites
```bash
sudo apt-get update && sudo apt-get install -y ant nmap supervisor tree sudo bsdmainutils bash-completion dnsmasq dnsutils nfs-common sshpass zip
```

```bash
wget -q https://www.virtualbox.org/download/oracle_vbox_2016.asc -O- | sudo apt-key add - && \
echo "deb [arch=amd64] http://download.virtualbox.org/virtualbox/debian $(lsb_release -cs) contrib" | sudo tee /etc/apt/sources.list.d/virtualbox.list && \
sudo apt update && \
sudo apt -y install virtualbox-5.2

wget -q https://download.virtualbox.org/virtualbox/5.2.34/Oracle_VM_VirtualBox_Extension_Pack-5.2.34-133893.vbox-extpack -P /tmp && \
echo "y" | sudo VBoxManage extpack install --replace "/tmp/Oracle_VM_VirtualBox_Extension_Pack-5.2.34-133893.vbox-extpack"
```

2. Setup the tira command (from tira9-application2/src/):
```bash
sudo mkdir /usr/lib/tira
sudo cp -R * /usr/lib/tira/ && \
sudo chmod +x /usr/lib/tira/* && \
sudo chmod +x /usr/lib/tira/core/* && \
sudo chmod +x /usr/lib/tira/libs/* && \
sudo touch /usr/lib/tira/log.txt && \
sudo chmod -x /usr/lib/tira/log.txt && \
sudo chmod ugo+w /usr/lib/tira/log.txt && \
sudo /usr/lib/tira/tira-init.sh -i && \
sudo /usr/lib/tira/tira-autocomplete.sh -i
# [ERROR] /mnt/nfs/tira/data not found, stored in _CONFIG_FILE_tira_data!
```

4. Create tira user
```bash
sudo python tira-setup.py user -c [nfs host]
# TODO: running on the same host attemp to extract userid/groupid fails because there is not tira user so far
```

5. Setup the TIRA Host
```bash
sudo python tira-setup.py host-create [nfs host] [network interface]
# [ERROR] /mnt/nfs/tira/data not found, stored in _CONFIG_FILE_tira_data!
# [ERROR] Installing virtualbox-4.3 failed. Aborting.
```

6. Download VM archive file(-s)
```bash
scp tira@betaweb019:/mnt/nfs/tira/data/virtual-machine-templates/tira-ubuntu-18-04-desktop-64bit.ova /mnt/nfs/tira/data/virtual-machine-templates
```

7. Login as tira user and check installation
```bash
[ERROR] [chris-1-ubuntu-18-04-desktop-64bit] is not a valid username/vmname
```


Installing a TIRA server
---------------------

1. Install prerequisites
```bash
sudo apt-get update && sudo apt-get install -y curl iputils-ping net-tools bash-completion dnsmasq dnsutils nfs-common openssh-client openssh-server
```

2. Create tira user
```
# specify $TIRA_PASSWORD
groupadd -r -g 1010 tira && \
useradd -m -u 1010 -g tira tira && echo "tira:$TIRA_PASSWORD" | chpasswd && \
usermod -aG root tira && \
usermod -aG sudo tira
```

2. Setup the tira command (from tira9-application2/src/):
```bash
sudo mkdir /usr/lib/tira
sudo cp -R * /usr/lib/tira/ && \
sudo chmod +x /usr/lib/tira/* && \
sudo chmod +x /usr/lib/tira/core/* && \
sudo chmod +x /usr/lib/tira/libs/* && \
sudo touch /usr/lib/tira/log.txt && \
sudo chmod -x /usr/lib/tira/log.txt && \
sudo chmod ugo+w /usr/lib/tira/log.txt && \
sudo /usr/lib/tira/tira-init.sh -i && \
sudo /usr/lib/tira/tira-autocomplete.sh -i
# [ERROR] /mnt/nfs/tira/data not found, stored in _CONFIG_FILE_tira_data!
```

3. Setup the TIRA Storage:
```bash
sudo python tira-setup.py nfs-create && \
touch /srv/tira/model/users/users.prototext
# TODO: check why users.prototext missing
```

Running a dockeridzed TIRA Host
---------------------

## Non-betaweb deployment

In order to successfully run dockerized TIRA Host following requirements should be met by the host machine:

- VirtualBox 5.2.34 and extension pack (see https://github.com/tira-io/tira9-application2/tree/master#installing-a-tira-host or Dockerfile)
- Docker
- Permissions of TIRA model folder contents should be set to ```tira``` user/group: ```sudo chown -R 1010:1010 initial-docker-tira-model```
  - Folder ```initial-docker-tira-model``` in the current project is a sample TIRA data model including test Alpine Linux VM image.

### Build the image

```bash
# cd .../tira9-application2
docker build -t webis/tira9-application2:v1 --build-arg tira_password=tira -f build/Dockerfile .
```

### Run the container

```bash
# cd .../tira9-application2
docker run \
    -d \
    -v /dev/vboxdrv:/dev/vboxdrv \
    -v /dev/vboxnetflt:/dev/vboxnetflt \
    -v /dev/vboxnetadp:/dev/vboxnetadp \
    -v /dev/vboxpci:/dev/vboxpci \
    -v /dev/vboxnetctl:/dev/vboxnetctl \
    -v /mnt/nfs/tira:/mnt/nfs/tira \   # if necessary to use pre-mounted cehp/nfs storage
    -v $PWD/build/initial-docker-tira-model:/mnt/nfs/tira \   # or in case of local dev deployment
    --env TIRA_FQDN=$(hostname) \   # change to the host FQDN if necessary
    --name="tira" \
    --privileged \
    --cap-add=NET_ADMIN \
    --network host \
    --hostname=$(hostname) \
    webis/tira9-application2:v1 tail -f /dev/null
```

## Deployment on a betaweb machine

Certain simplifications were made regarding deployment of dockerized  TIRA host on a betaweb, as currently it is only used for development and testing: e.g. SSH server inside container is not exposed, instead all TIRA command calls executed on the host are passed into the container with "alias" in /usr/bin/tira script (see below).

The following steps should be done on the host machine:

- apply tira salt state:
  - iptables
  - virtualbox, extpack
  - mount /mnt/ceph/tira
  - tira user, ssh key
  - dnsmasq
  - ...
- install docker
- modify /usr/bin/tira to execute tira commands inside the container:

  ```bash
    #!/bin/bash
    docker exec -it tira tira "$@"
  ```

- add tira user to docker group: ```sudo usermod -aG docker tira```
- /home/tira/.ssh/* should be copied to the container /home/tira/.ssh/ (This is done in docker run command)
- change ```tira_password``` in ```docker build``` command

### Build the image

```bash
# cd .../tira9-application2
docker build -t webis/tira9-application2:v1 --build-arg tira_password=tira -f build/Dockerfile .
```

### Run the container

```bash
# cd .../tira9-application2
docker run \
    -d \
    -v /dev/vboxdrv:/dev/vboxdrv \
    -v /dev/vboxnetflt:/dev/vboxnetflt \
    -v /dev/vboxnetadp:/dev/vboxnetadp \
    -v /dev/vboxpci:/dev/vboxpci \
    -v /dev/vboxnetctl:/dev/vboxnetctl \
    -v /mnt/nfs/tira:/mnt/nfs/tira \   # if necessary to use pre-mounted cehp/nfs storage
    -v /home/tira/.ssh:/home/tira/.ssh \
    --name="tira" \
    --privileged \
    --cap-add=NET_ADMIN \
    --network host \
    --hostname=$(hostname) \
    webis/tira9-application2:v1 tail -f /dev/null
```
