#!/usr/bin/bash -e

PYTHONPATH=':../src:.' ../venv/bin/python3 ../src/manage.py test --settings=settings_test

