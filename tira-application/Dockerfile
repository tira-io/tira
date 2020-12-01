FROM nginx:1.18-alpine
# 1. setup user and system software

RUN apk update &&\
    apk add --no-cache --virtual .build-deps gcc linux-headers make musl-dev g++ python3-dev &&\
    apk add --update --no-cache python3 zip py3-virtualenv

RUN addgroup --gid 1010 tira && \
	adduser --disabled-password --uid 1010 --ingroup tira tira && \
	adduser tira root

# 2. copy sources
RUN mkdir /tira
RUN mkdir -p /mnt/ceph/tira
RUN mkdir /etc/nginx/logs

COPY tira-application /tira/tira-application
COPY tira-protocol/build/python/* /tira/tira-application/src/tira/proto/
COPY tira-model/src/* /mnt/ceph/tira/model/
COPY tira-application/src/tira_nginx.conf /etc/nginx/nginx.conf
COPY tira-application/config/settings-deploy.yml /tira/tira-application/src/config/

RUN chown -R tira:tira /usr/local && \
	chmod 777 /var/run/ && \
	echo "tira ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers &&\
	touch /var/log/tira_debug.txt &&\
	chown tira:tira /var/log/tira_debug.txt &&\
	mkdir -p /home/tira/.tira &&\
	mkdir /home/tira/.ssh &&\
	chown tira:tira -R /home/tira &&\
	chown tira:tira -R /tira

# 4. make the sources
WORKDIR /tira/tira-application
RUN python3 -m pip install --no-cache-dir -r requirements.txt
RUN python3 src/manage.py migrate && \
	python3 src/manage.py makemigrations&& \
	python3 src/manage.py collectstatic

RUN apk del .build-deps

CMD sh -c "nginx && uwsgi --uid 1010 --ini /tira/tira-application/src/uwsgi.ini"
