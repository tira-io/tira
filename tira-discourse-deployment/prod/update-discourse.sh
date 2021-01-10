#!/bin/bash

_D="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BASE_DIRECTORY="$( cd "$( dirname "${_D}" )" >/dev/null 2>&1 && pwd )"

usage(){
    cat <<EOM
Usage: $(basename $0) -u USER -n IMAGENAME -t TAG -s SERVICE
Build new IMAGENAME:TAG and push it to Dockerhub at USER

Example: $(basename $0) -u webis -n tira -t 0.1.7 -s tira

Mandatory arguments:
    -u, --user                  Dockerhub username
    -i, --image                 Dockerhub imagename
    -t, --tag                   Tag for the image
    -s, --service-name          Name of the service for which the image will be updated


EOM
}

function docker_tag_exists() {
    docker login
    curl --silent -f --head -lL https://hub.docker.com/v2/repositories/$1/tags/$2/ > /dev/null
}


while [ "$1" != "" ]; do
    case $1 in
        -u | --user )           shift
                                DOCKERHUB_USER="$1"
                                ;;
        -i | --image )           shift
                                DOCKERHUB_IMAGENAME="$1"
                                ;;
        -t | --tag )            shift
                                DOCKERHUB_TAG="$1"
                                ;;
        -s | --service-name )   shift
                                SERVICE_NAME="$1"
                                ;;

        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

# Test if all mandatory variables were set
[ -z $DOCKERHUB_USER ] && usage &&  exit 1
[ -z $DOCKERHUB_IMAGENAME ] && usage && exit 1
[ -z $DOCKERHUB_TAG ] && usage && exit 1
[ -z $SERVICE_NAME ] && usage && exit 1

# Test if imagename:tag already exists on Dockerhub
if docker_tag_exists $DOCKERHUB_USER/$DOCKERHUB_IMAGENAME $DOCKERHUB_TAG; then
    echo "Combination $DOCKERHUB_IMAGENAME:$DOCKERHUB_TAG already exists for user $DOCKERHUB_USER"
    exit 1
fi

# update discourse_docker repository
git -C /var/discourse pull

# rebuild image
cd /var/discourse
./launcher rebuild $SERVICE_NAME
docker stop $SERVICE_NAME
# docker rm $SERVICE_NAME

# push image to
# imagename:tag and
# imagename:latest
docker tag local_discourse/$SERVICE_NAME:latest $DOCKERHUB_USER/$DOCKERHUB_IMAGENAME:$DOCKERHUB_TAG
docker push $DOCKERHUB_USER/$DOCKERHUB_IMAGENAME:$DOCKERHUB_TAG
docker tag local_discourse/$SERVICE_NAME:latest $DOCKERHUB_USER/$DOCKERHUB_IMAGENAME:latest
docker push $DOCKERHUB_USER/$DOCKERHUB_IMAGENAME:latest

cd $BASE_DIRECTORY

# not sure if needed
# mount -t ceph -o name=webis,secretfile=/etc/ceph/ceph.client.webis.secret ceph.dw.webis.de:/storage /mnt/ceph/storage
# cp /var/discourse/shared/standalone /mnt/ceph/storage/data-in-production/disraptor/boot/resource
# cp prod/setup /mnt/ceph/storage/data-in-production/disraptor/boot/setup

# redeploy
prod/k8s-undeploy-discourse-prod.sh
prod/k8s-deploy-discourse-prod.sh

