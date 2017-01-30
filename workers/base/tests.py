import unittest
import os
from time import sleep
import poliglo

import requests
import json
import random

def launch_instance(script_id, data={}):
    poliglo_server = "http://server:9015"

    all_data = {
        'name': 'Test ' + str(random.randint(0, 10000000)),
        'data': data
    }
    url = '%s/workflows/%s/workflow_instances' % (poliglo_server, script_id)
    res = requests.post(
        url,
        data=json.dumps(all_data),
        headers={'content-type': 'application/json'}
    )
    return res.json()['id']


class TestWaitJobs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._setup_master_mind_server()

    @classmethod
    def _setup_master_mind_server(cls):
        cls._setup_config()

    @classmethod
    def _setup_config(cls):
        cls.config = {
            "all": {
                "REDIS_HOST": os.environ.get("TEST_REDIS_HOST", "127.0.0.1"),
                "REDIS_PORT": 6379,
                "REDIS_DB": 5,
                "POLIGLO_SERVER_URL": "http://server:9015"
            }
        }
        # cls.config_path = "/tmp/config.json"
        # open(cls.config_path, 'w').write(poliglo.utils.to_json(cls.config))

    def setUp(self):
        self.connection = poliglo.preparation.get_connection(self.config.get('all'))
        self.connection.flushall()

    def test_wait_for_all_jobs(self):
        self.workflow_instance_id = launch_instance('test_wait_jobs')
        queues = [None]
        tries = 5
        while len(queues) > 0:
            tries -= 1
            if tries < 0:
                self.fail("Worker did not process the job")
            sleep(1)
            queues = self.connection.keys("queue:*")
        total_finalized = self.connection.zcard(
            "workflows:test_wait_jobs:workflow_instances:%s:workers:count_numbers_1:finalized" %
            self.workflow_instance_id
        )
        self.assertEqual(1, total_finalized)

    def test_last_message_are_filtered(self):
        self.workflow_instance_id = launch_instance('test_wait_jobs', {'numbers_range': [995, 1005]})
        queues = [None]
        tries = 5
        while len(queues) > 0:
            tries -= 1
            if tries < 0:
                self.fail("Worker did not process the job")
            sleep(1)
            queues = self.connection.keys("queue:*")
        total_finalized = self.connection.zcard(
            "workflows:test_wait_jobs:workflow_instances:%s:workers:count_numbers_1:finalized" %
            self.workflow_instance_id
        )
        self.assertEqual(1, total_finalized)
