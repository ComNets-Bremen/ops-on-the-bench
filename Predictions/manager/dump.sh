#!/bin/bash
#
# Bash script for loading dumped data into empty django DB
#
set -o errexit
echo "making migrations into empty django DB"
python manage.py makemigrations

set -o errexit
echo "migrating data data into django DB ..."
python manage.py migrate

set -o errexit
echo "loading dumped data into django DB"
python manage.py loaddata db.json

set -o errexit
echo "process complete, data migrated"
