.PHONY: help setup compile clean build

VENV_NAME?=venv
PYTHON=${VENV_NAME}/bin/python3
SRC_DIR=src
#PYTHON_DEST=${VENV_NAME}/lib/python3.7/site-packages
BUILD_PATH=build


.DEFAULT: help
help:
	@echo "make setup"
	@echo "       install protobuf from the included distribution"
	@echo "make build"
	@echo "       compile tira's protobufs"
	@echo "make build-python"
	@echo "       compile tira's protobufs"
	@echo "make clean"
	@echo "       remove files"

setup:
	unzip protoc/protoc-3.14.0-linux-x86_64.zip -d protoc
	chmod +x protoc/*
	mv protoc/bin/protoc /usr/local/bin
	mv protoc/include/* /usr/local/include
	chmod +x /usr/local/bin/protoc
	chmod -R +rx /usr/local/include


# Requires that protobuf was installed
build:
    # TODO check if virtualenv is installed
	! command -v protoc > /dev/null 2>&1 || make setup
	make venv
	make build-python

# Requirements are in setup.py, so whenever setup.py is changed, re-run installation of dependencies.
venv:
	test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	sh -c ". $(VENV_NAME)/bin/activate && \
		python3 -m pip install -r requirements.txt"

build-python:
	test -d $(VENV_NAME) || make venv
	mkdir -p $(BUILD_PATH)/python
	protoc -I=$(SRC_DIR) --python_out=$(BUILD_PATH)/python $(SRC_DIR)/tira_to_web.proto
	protoc -I=$(SRC_DIR) --python_out=$(BUILD_PATH)/python $(SRC_DIR)/tira_messages.proto
	protoc -I=$(SRC_DIR) --python_out=$(BUILD_PATH)/python $(SRC_DIR)/TiraClientWebMessages.proto
	${PYTHON} -m grpc_tools.protoc -I=$(SRC_DIR) --grpc_python_out=$(BUILD_PATH)/python tira_to_web.proto
	${PYTHON} -m grpc_tools.protoc -I=$(SRC_DIR) --python_out=$(BUILD_PATH)/python --grpc_python_out=$(BUILD_PATH)/python tira_host.proto
	sed -i 's/import tira_host_pb2 as tira__host__pb2/from . import tira_host_pb2 as tira__host__pb2/g' $(BUILD_PATH)/python/tira_host_pb2_grpc.py
	touch $(BUILD_PATH)/python/__init__.py

clean:
	rm -r $(VENV_NAME)
	rm -r $(BUILD_PATH)

