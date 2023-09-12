build-pypi-package: run-tests
	python3 -m build --sdist .
	python3 -m build --wheel .
	twine upload dist/tira-0.0.46-py3-none-any.whl dist/tira-0.0.47.tar.gz

run-tests:
	../application/venv/bin/coverage run --data-file=tests/test-coverage/.coverage ../application/venv/bin/pytest \
	&& ../application/venv/bin/coverage report --data-file=tests/test-coverage/.coverage > tests/test-coverage/coverage-report \
	&& cd tests/test-coverage \
	&& ../../../application/venv/bin/coverage-badge -o coverage.svg

