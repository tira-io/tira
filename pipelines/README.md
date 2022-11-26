# TIRA Pipelines with GIT CI/CD Workflows

```
docker run \
	-v ${PWD}/src/python/tira-persist-software-result.py:/usr/local/bin/tira-persist-software-result.py \
	-v ${PWD}/src/:/tira/application/src/tira-git:ro \
	-v /mnt/ceph/tira/:/mnt/ceph/tira/:ro \
	-w /tira/application/src/tira-git \
	--rm -ti webis/tira-git-pipelines:0.0.1
```

