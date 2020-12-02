#!/bin/bash -e

echo "Extract ceph secret from standard location..."

BASE_64_ENCODED_CEPH_SECRET=$(cat /etc/ceph/ceph.client.tira.secret|base64)
TIRA_SECRET_DEFINITION="{\"apiVersion\": \"v1\", \"kind\": \"Secret\", \"metadata\": {\"name\": \"tira-ceph-secret\"}, \"data\": {\"key\": \"${BASE_64_ENCODED_CEPH_SECRET}\"}}"

echo "Create tira-ceph-secret in kubernetes"
echo ${TIRA_SECRET_DEFINITION}|kubectl -n webisservices apply -f -

