IMAGE_VERSION=0.0.28

publish-tira-git-docker:
	docker push webis/tira-git-pipelines:${IMAGE_VERSION}

dev-environment:
	docker run --rm -ti -w=/app-in-progress -v ${PWD}/src:/app-in-progress webis/tira-git-pipelines:${IMAGE_VERSION}

