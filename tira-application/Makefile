.PHONY: help prepare-dev

VENV_NAME?=venv
PYTHON=${VENV_NAME}/bin/python3
SRC_DIR=../tira-protocol/src
# This needs to be on python path
PYTHON_DEST=${VENV_NAME}/lib/python3.7/site-packages

.DEFAULT: help
help:
	@echo "make setup"
	@echo "       setup venv, compile protobuf, give permissions to tira, and make migrations"
	@echo "make run-dev"
	@echo "       run server as tira user"
	@echo "make clean"
	@echo "       remove setup files"

setup:
	chmod o+x src
	make venv
	make protobuf
	make django

# Requirements are in setup.py, so whenever setup.py is changed, re-run installation of dependencies.
venv:
	test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	${PYTHON} -m pip install -r requirements.txt
	. $(VENV_NAME)/bin/activate

protobuf:
	protoc -I=$(SRC_DIR) --python_out=$(PYTHON_DEST) $(SRC_DIR)/tira_to_web.proto
	protoc -I=$(SRC_DIR) --python_out=$(PYTHON_DEST) $(SRC_DIR)/tira_messages.proto
	protoc -I=$(SRC_DIR) --python_out=$(PYTHON_DEST) $(SRC_DIR)/TiraClientWebMessages.proto
	${PYTHON} -m grpc_tools.protoc -I=$(SRC_DIR) --grpc_python_out=$(PYTHON_DEST) tira_to_web.proto

django:
	. $(VENV_NAME)/bin/activate
	${PYTHON} src/manage.py migrate
	${PYTHON} src/manage.py makemigrations

run-dev:
	su tira -c". $(VENV_NAME)/bin/activate && \
	${PYTHON} src/manage.py runserver 8080"

clean:
	rm -r $(VENV_NAME)