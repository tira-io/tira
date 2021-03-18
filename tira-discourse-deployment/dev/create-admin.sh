#!/bin/bash -e

if [[ $1 = "-n" ]]
then
    POD=$(kubectl get pods -n $2 | grep tira-discourse | sed "s/\s/\n/g" | head -n 1)
    kubectl -n $2 exec -it $POD -- sudo -u discourse /bin/bash -c "cd /src && USER=discourse RUBY_GLOBAL_METHOD_CACHE_SIZE=131072 LD_PRELOAD=/usr/lib/libjemalloc.so RAILS_ENV=development bundle exec rake admin:create"
else
    echo "USAGE: create-admin.sh -n NAMESPACE"
fi
