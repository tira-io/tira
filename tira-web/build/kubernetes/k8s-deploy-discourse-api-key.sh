#!/bin/bash -e

if [ "$#" -ne 1 ]; then
    echo "Usage: pass the API-Key to this script."
    exit 1
fi


BASE_64_ENCODED_API_KEY=$(echo "${1}"|base64 -w 0)
API_KEY_SECRET_DEFINITION="{\"apiVersion\": \"v1\", \"kind\": \"Secret\", \"metadata\": {\"name\": \"tira-discourse-api-key\"}, \"data\": {\"key\": \"${BASE_64_ENCODED_API_KEY}\"}}"

echo "Create tira-ceph-secret in kubernetes."
echo ${API_KEY_SECRET_DEFINITION}|kubectl -n webisservices apply -f -

