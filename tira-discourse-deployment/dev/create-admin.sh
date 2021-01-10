#!/bin/bash -e

POD=$(kubectl get pods | grep tira-discourse | sed "s/\s/\n/g" | head -n 1)

kubectl exec -it $POD -- sudo -u discourse /bin/bash -c "cd /src && USER=discourse RUBY_GLOBAL_METHOD_CACHE_SIZE=131072 LD_PRELOAD=/usr/lib/libjemalloc.so RAILS_ENV=development bundle exec rake admin:create"
