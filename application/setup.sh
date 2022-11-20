#!/bin/bash
# setup.sh does steps in the tira setup.

exit_with () {
  echo $1
  echo "Exiting setup.sh; Please install the required software.";
  exit 1
}

which mysql_config > '\dev\null' || exit_with "Please install the sql driver before the tira-application setup:
  sudo apt install libmysqlclient-dev
  sudo apk add mariadb-dev"

which npm > '\dev\null' || exit_with "Please install npm to build the vue frontend
  https://nodejs.org/en/download/"
