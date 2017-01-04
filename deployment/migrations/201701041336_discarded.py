# Get all job ids from the 'workflows:*:workflow_instances:*:workers:*:discarded' keys and
# write them as a set to 'workflows:*:workflow_instances:*:workers:*:jobs_ids:removed'.
# This migration only makes sense if there is already discarded jobs in the database.
# Run it inside the worker container.
import re
import json
from poliglo.preparation import get_config, get_connection
from poliglo.variables import REDIS_KEY_INSTANCE_WORKER_DISCARDED
from os import environ

def main():
    config = get_config(environ.get('POLIGLO_SERVER_URL'), 'all')
    connection = get_connection(config)
    keys = connection.keys(REDIS_KEY_INSTANCE_WORKER_DISCARDED % ('*', '*', '*'))
    for key in keys:
        discarded_job_key = re.sub(':discarded$', ':jobs_ids:removed', key)
        if connection.exists(discarded_job_key):
            continue

        job_ids = []
        data = connection.zrange(key, 0, -1)
        for row in data:
            data = json.loads(row)
            job_ids += data.get('jobs_ids', [])
        print "Base key: %s" % key
        print "Job ids: %s" % job_ids
        connection.sadd(discarded_job_key, *job_ids)
        print "New key: %s" % discarded_job_key

if __name__ == '__main__':
    main()
