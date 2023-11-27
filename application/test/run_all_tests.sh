#!/bin/sh
cd test

export PYTHONPATH=':../src:.'
export DJANGO_SETTINGS_MODULE=settings_test

rm -Rf test-database
mkdir test-database

python3 ../src/manage.py reset_db --no-input
python3 ../src/manage.py makemigrations tira

python3 ../src/manage.py migrate tira

coverage run --data-file=test-coverage/.coverage ../src/manage.py test --settings=settings_test --failfast tirex_components_snippet_rendering_tests
#coverage report --data-file=test-coverage/.coverage > test-coverage/coverage-report
#cd test-coverage

#rm -Rf coverage.svg
#coverage-badge -o coverage.svg

