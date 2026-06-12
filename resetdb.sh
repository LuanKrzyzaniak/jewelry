#!/usr/bin/env bash
set -e

rm -f db.sqlite3
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_dev
