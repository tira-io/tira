#!/bin/sh

export PYTHONPATH=/tira/application/src

python3 /tira/application/src/manage.py ir_datasets_loader_cli ${@}

