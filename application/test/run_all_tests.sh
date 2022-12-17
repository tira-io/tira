#!/usr/bin/sh
cd test

export PYTHONPATH=':../src:.'
export DJANGO_SETTINGS_MODULE=settings_test

rm -Rf test-database
mkdir test-database

python3 ../src/manage.py reset_db --no-input
python3 ../src/manage.py makemigrations tira

python3 ../src/manage.py migrate tira

python3 ../src/manage.py test --settings=settings_test --failfast

