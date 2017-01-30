#!/usr/bin/env bash
set -o nounset
set -o errexit
NAME=poliglotest
docker-compose -f docker-compose.yml -f docker-compose.test.yml -p $NAME up -d
docker exec ${NAME}_worker_1 bash -c 'cd /src/workers/base && pip install requests && python -u -m unittest tests'
echo "Stop containers with:"
echo "docker-compose -p $NAME down"
