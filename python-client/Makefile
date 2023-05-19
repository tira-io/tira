build-pypi-package: run-tests
	python3 -m build --sdist .
	python3 -m build --wheel .
	twine upload dist/tira-0.0.34-py3-none-any.whl dist/tira-0.0.34.tar.gz

run-tests:
	../application/venv/bin/pytest

