#!/bin/bash

# Default Gunicorn settings
NUM_WSGI_WORKERS="${NUM_WSGI_WORKERS:-4}"
GUNICORN_CONF=$(python3 -c "import os, timesketch; print(os.path.join(os.path.dirname(timesketch.__file__), 'gunicorn.conf.py'))")

# Common Gunicorn Defaults
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-600}"
GUNICORN_LIMIT_REQUEST_LINE="${GUNICORN_LIMIT_REQUEST_LINE:-8190}"
GUNICORN_MAX_REQUESTS="${GUNICORN_MAX_REQUESTS:-1000}"
GUNICORN_MAX_REQUESTS_JITTER="${GUNICORN_MAX_REQUESTS_JITTER:-100}"
GUNICORN_LOG_LEVEL="${GUNICORN_LOG_LEVEL:-info}"
GUNICORN_EXTRA_ARGS="${GUNICORN_EXTRA_ARGS:-}"

# Common Worker Defaults
WORKER_LOG_LEVEL="${WORKER_LOG_LEVEL:-info}"
WORKER_LOG_FILE="${WORKER_LOG_FILE:-/var/log/timesketch/worker.log}"
CELERY_EXTRA_ARGS="${CELERY_EXTRA_ARGS:-}"

COMMAND=$1
if [ $# -gt 0 ]; then
  shift
fi

if [ "${COMMAND}" = "timesketch-web" ]; then
  export TIMESKETCH_UI_MODE="ng"
  GUNICORN_BIND="${GUNICORN_BIND:-0.0.0.0:5000}"
  GUNICORN_LOG_FILE="${GUNICORN_LOG_FILE:-/var/log/timesketch/wsgi.log}"
  GUNICORN_ERROR_LOG_FILE="${GUNICORN_ERROR_LOG_FILE:-/var/log/timesketch/wsgi_error.log}"

  exec gunicorn --bind "${GUNICORN_BIND}" --log-file "${GUNICORN_LOG_FILE}" \
           -c "${GUNICORN_CONF}" \
           --error-logfile "${GUNICORN_ERROR_LOG_FILE}" --log-level "${GUNICORN_LOG_LEVEL}" \
           --capture-output --timeout "${GUNICORN_TIMEOUT}" --limit-request-line "${GUNICORN_LIMIT_REQUEST_LINE}" \
           --workers "${NUM_WSGI_WORKERS}" \
           --max-requests "${GUNICORN_MAX_REQUESTS}" --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER}" \
           ${GUNICORN_EXTRA_ARGS} \
           "$@" \
           timesketch.wsgi:application

elif [ "${COMMAND}" = "timesketch-web-legacy" ]; then
  export TIMESKETCH_UI_MODE="legacy"
  GUNICORN_BIND="${GUNICORN_BIND:-0.0.0.0:5001}"
  GUNICORN_LOG_FILE="${GUNICORN_LOG_FILE:-/var/log/timesketch/wsgi_legacy.log}"
  GUNICORN_ERROR_LOG_FILE="${GUNICORN_ERROR_LOG_FILE:-/var/log/timesketch/wsgi_legacy_error.log}"

  exec gunicorn --bind "${GUNICORN_BIND}" --log-file "${GUNICORN_LOG_FILE}" \
           -c "${GUNICORN_CONF}" \
           --error-logfile "${GUNICORN_ERROR_LOG_FILE}" --log-level "${GUNICORN_LOG_LEVEL}" \
           --capture-output --timeout "${GUNICORN_TIMEOUT}" --limit-request-line "${GUNICORN_LIMIT_REQUEST_LINE}" \
           --workers "${NUM_WSGI_WORKERS}" \
           --max-requests "${GUNICORN_MAX_REQUESTS}" --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER}" \
           ${GUNICORN_EXTRA_ARGS} \
           "$@" \
           timesketch.wsgi:application

elif [ "${COMMAND}" = "timesketch-web-v3" ]; then
  export TIMESKETCH_UI_MODE="v3"
  GUNICORN_BIND="${GUNICORN_BIND:-0.0.0.0:5002}"
  GUNICORN_LOG_FILE="${GUNICORN_LOG_FILE:-/var/log/timesketch/wsgi_v3.log}"
  GUNICORN_ERROR_LOG_FILE="${GUNICORN_ERROR_LOG_FILE:-/var/log/timesketch/wsgi_v3_error.log}"

  exec gunicorn --bind "${GUNICORN_BIND}" --log-file "${GUNICORN_LOG_FILE}" \
           -c "${GUNICORN_CONF}" \
           --error-logfile "${GUNICORN_ERROR_LOG_FILE}" --log-level "${GUNICORN_LOG_LEVEL}" \
           --capture-output --timeout "${GUNICORN_TIMEOUT}" --limit-request-line "${GUNICORN_LIMIT_REQUEST_LINE}" \
           --workers "${NUM_WSGI_WORKERS}" \
           --max-requests "${GUNICORN_MAX_REQUESTS}" --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER}" \
           ${GUNICORN_EXTRA_ARGS} \
           "$@" \
           timesketch.wsgi:application

elif [ "${COMMAND}" = "timesketch-worker" ]; then
  exec celery -A timesketch.lib.tasks worker \
         --logfile="${WORKER_LOG_FILE}" \
         --loglevel="${WORKER_LOG_LEVEL}" \
         ${CELERY_EXTRA_ARGS} \
         "$@"
else
  exec "${COMMAND}" "$@"
fi
