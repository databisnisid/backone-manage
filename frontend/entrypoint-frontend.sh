#!/bin/sh
set -e

# Replace ${DJANGO_UPSTREAM} in nginx config with actual value
UPSTREAM="${DJANGO_UPSTREAM:-http://django:8008}"
sed -i 's|\${DJANGO_UPSTREAM}|'"${UPSTREAM}"'|g' /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
