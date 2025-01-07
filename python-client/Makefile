.PHONY:docs

build-pypi-package: run-tests
	python3 -m build --sdist .
	python3 -m build --wheel .
	twine upload dist/tira-0.0.142-py3-none-any.whl dist/tira-0.0.142.tar.gz

run-tests:
	docker run -u root --rm -v /var/run/docker.sock:/var/run/docker.sock -v ${PWD}:/app -w /app --entrypoint pytest webis/tira:python-client-dev-0.0.5
	docker run -u root --rm -v /var/run/docker.sock:/var/run/docker.sock -v ${PWD}:/app -w /app --entrypoint pytest webis/tira:python-client-dev-0.0.5-python3.7
	docker run -u root --rm -v /var/run/docker.sock:/run/user/0/podman/podman.sock -v ${PWD}:/app -w /app --entrypoint pytest webis/tira:python-client-dev-0.0.5-python3.7
