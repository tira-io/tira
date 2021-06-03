VERSION=9.0.38

publish-docker: build-tira-docker
	docker login &&\
	docker push mam10eks/tmp-tira-mam10eks:${VERSION}

run-tira-docker: build-tira-docker
	docker run --rm -ti -p 8080:8080 mam10eks/tmp-tira-mam10eks:${VERSION}

run-tira-docker-with-ceph-mount: build-tira-docker
	docker run --rm -ti -v /mnt/ceph/tira:/mnt/nfs/tira -p 8080:8080 mam10eks/tmp-tira-mam10eks:${VERSION}

k8s-deploy:
	cd build/kubernetes/ && ./k8s-deploy.sh

k8s-undeploy:
	cd build/kubernetes/ && ./k8s-undeploy.sh

build-tira-docker:
	docker build -f build/Dockerfile -t mam10eks/tmp-tira-mam10eks:${VERSION} .

