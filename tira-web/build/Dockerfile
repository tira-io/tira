FROM tomcat:7.0-jdk8-openjdk

RUN mkdir /tira-src
WORKDIR /tira-src

RUN apt-get update && \
	apt-get install -y ant nmap supervisor tree sudo bsdmainutils bash-completion dnsmasq dnsutils nfs-common sshpass zip jq

COPY build /tira-src/build
COPY conf /tira-src/conf
COPY src-java /tira-src/src-java
COPY src-war /tira-src/src-war
COPY lib /tira-src/lib

RUN cd build && ant
RUN mkdir -p /mnt/nfs/tira
COPY build/initial-docker-tira-model /mnt/nfs/tira/

RUN rm -Rf /usr/local/tomcat/webapps/* && \
	cp build/tira9-client-web.war /usr/local/tomcat/webapps/ROOT.war

RUN groupadd -r -g 1010 tira && \
	useradd -u 1010 -g tira tira && \
	usermod -a -G root tira

RUN groupadd supervisor && \
	usermod -a -G supervisor tira && \
	cp /tira-src/conf/supervisord.conf /etc/supervisor/ && \
	mkdir /etc/supervisor/conf.d/tira && \
	chgrp supervisor /etc/supervisor/conf.d/tira && \
	chmod 775 /etc/supervisor/conf.d/tira && \
	chmod g+s /etc/supervisor/conf.d/tira && \
	mkdir /var/log/supervisor/tira && \
	chgrp supervisor /var/log/supervisor/tira && \
	chmod 775 /var/log/supervisor/tira && \
	chmod g+s /var/log/supervisor/tira && \
	chown -R tira:tira /usr/local && \
	chown -R tira:tira /var/log/supervisor && \
	chmod 777 /var/run/ && \
	echo "tira ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers &&\
	touch /var/log/tira_debug.txt &&\
	chown tira:tira /var/log/tira_debug.txt &&\
	mkdir -p /home/tira/.tira &&\
	mkdir /home/tira/.ssh &&\
	chown tira:tira -R /home/tira &&\
	echo "echo 'this is only a dummy vbox-manage!'; exit 1" > /usr/bin/VBoxManage &&\
	chmod +x /usr/bin/VBoxManage &&\
	ln -s /usr/local/share/tira/src/tira.sh /usr/bin/tira

#ENV JAVA_OPTS="-Djava.library.path=/usr/lib -Djna.library.path=/usr/lib -Djava.awt.headless=true -Xmx11264m -XX:+UseConcMarkSweepGC"
ENV JAVA_OPTS="-Djava.awt.headless=true -Xmx11264m -XX:+UseConcMarkSweepGC"

USER tira
ENV USER=tira

COPY build/start-tira.sh /tira-src/
COPY build/supervisord-daemon.sh /tira-src/

CMD ./start-tira.sh
