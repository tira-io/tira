#!/usr/bin/bash

docker run \
	-v ${PWD}:/repo \
	-v /mnt/ceph/tira/:/mnt/ceph/tira/:ro \
	-v ${HOME}/.ssh/id_rsa:${HOME}/.ssh/id_rsa:ro \
	-v ${HOME}/.ssh/config:${HOME}/.ssh/config:ro \
	-v ${HOME}/.ssh/id_rsa.pub:${HOME}/.ssh/id_rsa.pub:ro \
	-v ${HOME}/.gitconfig:${HOME}/.gitconfig:ro \
	-v /etc/tira-git-credentials:/etc/tira-git-credentials:ro \
	-v ${SSH_AUTH_SOCK}:${SSH_AUTH_SOCK} \
	-e SSH_AUTH_SOCK=${SSH_AUTH_SOCK} \
	-v /etc/passwd:/etc/passwd:ro \
	-w /repo \
	-u $(id -u ${USER}):$(id -g ${USER}) \
	-e CI_SERVER_HOST={{ ci_server_host }} \
	-e CI_PROJECT_ID={{ project_id }} \
	--entrypoint ./src/tira_git.py \
	--rm -ti webis/tira-git:0.0.16 ${@}

