#!/usr/bin/bash -e

rm -Rf tira-root/
mkdir -p tira-root/model/virtual-machines/
mkdir -p tira-root/model/virtual-machine-hosts
mkdir -p tira-root/model/tasks/
mkdir -p tira-root/model/users/
mkdir -p tira-root/data/runs/dataset-1/example_participant/run-1
touch tira-root/model/virtual-machines/virtual-machines.txt
touch tira-root/model/virtual-machine-hosts/virtual-machine-hosts.txt
touch tira-root/model/users/users.prototext

PYTHONPATH=':../src:.' ../venv/bin/python3 ../src/manage.py test --settings=settings_test

