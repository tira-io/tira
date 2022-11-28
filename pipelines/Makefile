IMAGE_VERSION=0.0.5

build-tira-git-docker:
	cp -r ../host/src/tira_host src
	docker build -t webis/tira-git-pipelines:${IMAGE_VERSION} src

publish-tira-git-docker:
	docker push webis/tira-git-pipelines:${IMAGE_VERSION}

dev-environment:
	docker run --rm -ti -w=/app-in-progress -v ${PWD}/src:/app-in-progress webis/tira-git-pipelines:${IMAGE_VERSION}

