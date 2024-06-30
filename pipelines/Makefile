IMAGE_VERSION=0.0.34

publish-tira-git-docker:
	docker push webis/tira-git-pipelines:${IMAGE_VERSION}

build-docker:
	docker build -t webis/tira-git-pipelines:${IMAGE_VERSION} -f src/f .

dev-environment:
	docker run --rm -ti -w=/app-in-progress -v ${PWD}/src:/app-in-progress webis/tira-git-pipelines:${IMAGE_VERSION}

