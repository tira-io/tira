#!/usr/bin/bash -e

rm -Rf tira-root/ \
mkdir -p tira-root/model/virtual-machines/ \
mkdir -p tira-root/model/tasks/ \

PYTHONPATH=':../src:.' ../venv/bin/python3 ../src/manage.py test --settings=settings_test

