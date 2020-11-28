#!/bin/bash

sudo cat /etc/ssh-key/id_rsa > /home/tira/.ssh/id_rsa
sudo chown tira:tira ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa
nohup ./supervisord-daemon.sh &

/usr/local/tomcat/bin/catalina.sh run
