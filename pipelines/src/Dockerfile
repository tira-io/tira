FROM registry.webis.de/code-lib/public-images/tira-application:0.0.12

RUN apk add bash git curl openssh-client tree coreutils

RUN pip3 install python-gitlab GitPython

COPY python/tira-persist-software-result.py \
	bash/tira-test-runner-is-trustworthy.sh \
	bash/tira-persist-evaluation-result.sh \
	python/tira-specify-task-to-run.py \
	/usr/local/bin/

ENV DJANGO_SETTINGS_MODULE=django_tira_git.settings
ENV PYTHONPATH=/tira/application/src/

COPY python/tira/git_integration /tira/application/src/tira/git_integration
COPY django_tira_git /tira/application/src/django_tira_git
COPY config/config.yml /tira/application/src/config/tira-git-config.yml
COPY . /tira-git/src

ENTRYPOINT bash

