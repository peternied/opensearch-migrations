#!/bin/bash
set -e

# if [[ -f /root/loadServicesFromParameterStore.sh ]]; then
#   /root/loadServicesFromParameterStore.sh
# fi

echo "Starting API server..."
mkdir -p /var/log

cd /root/lib/console_link
export FASTAPI_ROOT_PATH=/api
pipenv run gunicorn console_link.api.main:app \
    -k uvicorn.workers.UvicornWorker \
    -w 4 \
    -b 0.0.0.0:8000 \
    --access-logfile /var/log/gunicorn-access.log \
    --error-logfile /var/log/gunicorn-error.log &

sleep 2

tail /var/log/gunicorn-access.log
tail /var/log/gunicorn-error.log

cd /root

# Switch to $SHARED_LOGS_DIR_PATH/api/logs/access.log
#           $SHARED_LOGS_DIR_PATH/api/logs/error.log

# Keep container running and interactive
exec tail -f /dev/null
