#!/bin/bash

set -euo pipefail
trap 'echo "[ERROR] Command failed at line $LINENO: $BASH_COMMAND" >&2' ERR

celery -A canopy worker --loglevel=debug