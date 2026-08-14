#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements/prod.txt

python manage.py collectstatic --no-input --settings=config.settings.prod
python manage.py migrate --no-input --settings=config.settings.prod