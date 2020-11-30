.PHONY: help setup run-dev clean

VENV_NAME?=venv
PYTHON=${VENV_NAME}/bin/python3
SRC_DIR=../tira-protocol/src
#PYTHON_DEST=${VENV_NAME}/lib/python3.7/site-packages
BUILD_PATH=src/tira/proto


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
	mkdir -p $(BUILD_PATH)
	make venv
	make protobuf
	make django

# Requirements are in setup.py, so whenever setup.py is changed, re-run installation of dependencies.
venv:
	test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	${PYTHON} -m pip install -r requirements.txt

protobuf:
	protoc -I=$(SRC_DIR) --python_out=$(BUILD_PATH) $(SRC_DIR)/tira_to_web.proto
	protoc -I=$(SRC_DIR) --python_out=$(BUILD_PATH) $(SRC_DIR)/tira_messages.proto
	protoc -I=$(SRC_DIR) --python_out=$(BUILD_PATH) $(SRC_DIR)/TiraClientWebMessages.proto
	${PYTHON} -m grpc_tools.protoc -I=$(SRC_DIR) --grpc_python_out=$(BUILD_PATH) tira_to_web.proto
	touch $(BUILD_PATH)/__init__.py

django:
	sh -c ". $(VENV_NAME)/bin/activate && \
	python3 src/manage.py migrate && \
	python3 src/manage.py makemigrations"

run-dev:
	su tira -c". $(VENV_NAME)/bin/activate && \
	python3 src/manage.py runserver 8080"

run-wsgi:
	su tira -c". $(VENV_NAME)/bin/activate && \
	uwsgi --ini src/uwsgi.ini"

clean:
	rm -r $(VENV_NAME)
	rm -r $(BUILD_PATH)