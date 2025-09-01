#!/bin/bash

set -euo pipefail
trap 'echo "[ERROR] Command failed at line $LINENO: $BASH_COMMAND" >&2' ERR

# python manage.py runserver 0.0.0.0:8000

python manage.py collectstatic --noinput

exec uvicorn canopy.asgi:application --host 0.0.0.0 --port 8000 --reload
