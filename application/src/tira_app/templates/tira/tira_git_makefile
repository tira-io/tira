VENV_NAME?=.venv

.DEFAULT: help
help:
	@echo "make .venv"
	@echo "       setup virtual environment"
	@echo "make jupyterlab"
	@echo "       start a jupyterlab server"

clean:
	@rm -Rf ${VENV_NAME}

# Requirements are in requirements.txt, so whenever requirements.txt is changed, re-run installation of dependencies.
.venv:
	@test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	@sh -c ". $(VENV_NAME)/bin/activate && \
		python3 -m pip install --upgrade pip && \
		python3 -m pip install wheel && \
		python3 -m pip install -r requirements.txt"

jupyterlab: .venv
	.venv/bin/jupyter-lab --ip 0.0.0.0

