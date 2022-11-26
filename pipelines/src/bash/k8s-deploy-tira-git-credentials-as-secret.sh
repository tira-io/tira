#!/bin/bash -e

if [ "$#" -ne 2 ]; then
    echo "Usage: <GITCREDENTIALPASSWORD> <GITCREDENTIALPRIVATETOKEN>."
    exit 1
fi


BASE_64_ENCODED_TOKEN=$(echo "${1}"|base64 -w 0)
BASE_64_ENCODED_PRIVATE_TOKEN=$(echo "${2}"|base64 -w 0)
BASE_64_ENCODED_USER=$(echo "tira-automation-bot"|base64 -w 0)
API_KEY_SECRET_DEFINITION="{\"apiVersion\": \"v1\", \"kind\": \"Secret\", \"metadata\": {\"name\": \"tira-git-credentials\"}, \"data\": {\"GITCREDENTIALPASSWORD\": \"${BASE_64_ENCODED_TOKEN}\", \"GITCREDENTIALUSERNAME\": \"${BASE_64_ENCODED_USER}\", \"GITCREDENTIALPRIVATETOKEN\": \"${BASE_64_ENCODED_PRIVATE_TOKEN}\"}}"

echo "Create tira-git-credentials in kubernetes."
echo ${API_KEY_SECRET_DEFINITION}|kubectl -n kibi9872 apply -f -

