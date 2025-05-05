#FROM registry.webis.de/code-lib/public-images/tira-application:0.0.12
#
#RUN apk add bash git curl openssh-client tree coreutils
#
#RUN pip3 install python-gitlab GitPython pyfailsafe
#
#RUN pip3 install pytest
#
#COPY python/tira-persist-software-result.py \
#	bash/tira-test-runner-is-trustworthy.sh \
#	bash/tira-persist-evaluation-result.sh \
#	python/tira-specify-task-to-run.py \
#	python/test_tira_integration.py \
#	/usr/local/bin/
#
#ENV DJANGO_SETTINGS_MODULE=django_tira_git.settings
#ENV PYTHONPATH=/tira/application/src/
#
#COPY python/tira/git_integration /tira/application/src/tira/git_integration
#COPY django_tira_git /tira/application/src/django_tira_git
#COPY config/config.yml /tira/application/src/config/tira-git-config.yml
#COPY . /tira-git/src
#
#RUN cd /usr/local/bin/ \
#	&& pytest \
#	&& rm test_tira_integration.py \
#	&& rm -R /tmp/test-in-progress
#
#ENTRYPOINT bash

# docker build -t webis/tira-git-pipelines:0.0.38 .
FROM webis/tira-git-pipelines:0.0.37

COPY python/tira/git_integration/gitlab_integration.py /tira/application/src/tira/git_integration/gitlab_integration.py

