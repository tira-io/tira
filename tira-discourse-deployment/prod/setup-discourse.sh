#!/bin/bash

_D="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BASE_DIRECTORY="$( cd "$( dirname "${_D}" )" >/dev/null 2>&1 && pwd )"

usage(){
    cat <<EOM
Usage: $(basename $0) -u USER -n IMAGENAME -f FILE
Build new IMAGENAME:0.0.1 with information from FILE and push it to Dockerhub at USER

Example: $(basename $0) -u webis -n tira -f tira.yml
Mandatory arguments:
    -u, --user                  Dockerhub username
    -i, --image                 Dockerhub imagename
    -f, --file                  File to read data from

EOM
}

# checks if docker tag exists
# needs login but credentials may be read from file later
function docker_tag_exists() {
    docker login
    curl --silent -f --head -lL https://hub.docker.com/v2/repositories/$1/tags/$2/ > /dev/null
}


while [ "$1" != "" ]; do
    case $1 in
        -u | --user )           shift
                                DOCKERHUB_USER="$1"
                                ;;
        -i | --image )          shift
                                DOCKERHUB_IMAGENAME="$1"
                                ;;
        -f | --file )           shift
                                DATA_FILENAME="$1"
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
[ -z $DATA_FILENAME ] && usage && exit 1
DOCKERHUB_TAG="0.0.1"

# Test if imagename:tag already exists on Dockerhub
if docker_tag_exists $DOCKERHUB_USER/$DOCKERHUB_IMAGENAME $DOCKERHUB_TAG; then
    echo "Combination $DOCKERHUB_IMAGENAME:$DOCKERHUB_TAG already exists for user $DOCKERHUB_USER"
    exit 1
fi

parse_yaml() {
   local prefix=$2
   local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
   sed -ne "s|^\($s\)\($w\)$s:$s\"\(.*\)\"$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  $1 |
   awk -F$fs '{
      indent = length($1)/2;
      vname[indent] = $2;
      for (i in vname) {if (i > indent) {delete vname[i]}}
      if (length($3) > 0) {
         vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
         printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
      }
   }'
}

eval $(parse_yaml $DATA_FILENAME "data_")

# setup YAML for secret
echo "apiVersion: v1
kind: Secret
metadata:
  name: discourse-prod-secret
type: Opaque
stringData:
  discourse_developer_emails: \"$data_developer_emails\"
  discourse_smtp_address: \"$data_smtp_address\"
  discourse_smtp_user_name: \"$data_smtp_username\"
  discourse_smtp_password: \"$data_smtp_password\"" > discourse-$data_service_name-secret.yml

kubectl apply -f discourse_secret.yml

# clone dicourse_docker repo to build image
sudo -s
git clone https://github.com/discourse/discourse_docker.git /var/discourse
cd /var/discourse/

echo "Waiting 5 seconds for command to reach input."
./discourse-setup & sleep 5 ; kill $!

# rebuild with given information
sed -i s/"\'discourse.example.com\'"/"\'$data_hostname\'"/g containers/app.yml
sed -i s/"\'me@example.com,you@example.com\'"/"\'$data_developer_emails\'"/g containers/app.yml
sed -i s/"smtp.example.com"/"$data_smtp_address"/g containers/app.yml
sed -i s/"user@example.com"/"$data_smtp_username"/g containers/app.yml
sed -i s/"pa\$\$word"/"$data_smtp_password"/g containers/app.yml
sed -i s/"#DISCOURSE_SMTP_PORT"/"DISCOURSE_SMTP_PORT"/g containers/app.yml

./launcher rebuild app

# make changes before rebuilding with Disraptor Plugin
mv containers/app.yml containers/$data_service_name.yml
sed -i 'docker_manager.git a\
    - git clone https://github.com/disraptor/disraptor.git' containers/$data_service_name.yml

# rebuild again
docker stop app && docker rm app
./launcher rebuild $data_service_name

# Push to Dockerhub
docker tag local_discourse/$data_service_name:latest $DOCKERHUB_USER/$DOCKERHUB_IMAGENAME:$DOCKERHUB_TAG
docker push $DOCKERHUB_USER/$DOCKERHUB_IMAGENAME:$DOCKERHUB_TAG

# setup files in Ceph to be present in container later
echo "Mounting ceph with secret 'webis'"
mount -t ceph -o name=webis,secretfile=/etc/ceph/ceph.client.webis.secret ceph.dw.webis.de:/storage /mnt/ceph/storage

cd $BASE_DIRECTORY
cp /var/discourse/shared/standalone /mnt/ceph/storage/data-in-production/disraptor/boot/resource
cp prod/setup /mnt/ceph/storage/data-in-production/disraptor/boot/setup

# deploy
prod/k8s-deploy-discourse-prod.sh
