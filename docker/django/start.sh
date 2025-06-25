#!/bin/bash

set -euo pipefail
trap 'echo "[ERROR] Command failed at line $LINENO: $BASH_COMMAND" >&2' ERR

nginx

python manage.py runserver 0.0.0.0:8000