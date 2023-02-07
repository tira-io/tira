build-pypi-package:
	python3 -m build --sdist .
	python3 -m build --wheel .
	twine upload dist/tira-0.0.5-py3-none-any.whl dist/tira-0.0.5.tar.gz
