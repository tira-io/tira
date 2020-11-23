.PHONY: help prepare-dev

VENV_NAME?=venv
PYTHON=${VENV_NAME}/bin/python3
SRC_DIR=../tira-protocol/src
# This needs to be on python path
PYTHON_DEST=${VENV_NAME}/lib/python3.7/site-packages

.DEFAULT: help
help:
	@echo "make prepare-dev"
	@echo "       prepare development environment, use only once"

prepare-dev:
	make venv
	make protobuf

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

clean:
	rm -r $(VENV_NAME)