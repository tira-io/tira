#!/bin/bash

python3 src/manage.py grpc_server &
nginx && uwsgi --uid 1010 --ini /tira/tira-application/src/uwsgi.ini &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?