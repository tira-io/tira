build-pypi-package: run-tests
	python3 -m build --sdist .
	python3 -m build --wheel .
	twine upload dist/tira-0.0.75-py3-none-any.whl dist/tira-0.0.75.tar.gz

run-tests:
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v ${PWD}:/app -w /app --entrypoint pytest webis/tira:python-client-dev-0.0.2

run-tests-legacy:
	../application/venv/bin/coverage run --data-file=tests/test-coverage/.coverage ../application/venv/bin/pytest \
	&& ../application/venv/bin/coverage report --data-file=tests/test-coverage/.coverage > tests/test-coverage/coverage-report \
	&& cd tests/test-coverage \
	&& ../../../application/venv/bin/coverage-badge -o coverage.svg

