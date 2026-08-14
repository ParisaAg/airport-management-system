#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements/prod.txt

python manage.py collectstatic --no-input --settings=config.settings.prod
python manage.py migrate --no-input --settings=config.settings.prod

if [[ -n "${DEMO_SEED_PASSWORD:-}" ]]; then
    python manage.py seed_demo \
        --settings=config.settings.prod \
        --password "$DEMO_SEED_PASSWORD"
fi