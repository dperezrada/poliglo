# INTEGRATION TEST
import os
import signal
import subprocess
from unittest import TestCase
from shutil import copyfile
from time import sleep

import poliglo

class TestWaitJobs(TestCase):
    @classmethod
    def _setup_config(cls):
        cls.config = {
            "all": {
                "REDIS_HOST": "127.0.0.1",
                "REDIS_PORT": 6379,
                "REDIS_DB": 5,
                "POLIGLO_SERVER_URL": "http://localhost:9016"
            }
        }
        cls.config_path = "/tmp/config.json"
        open(cls.config_path, 'w').write(poliglo.utils.to_json(cls.config))

    @classmethod
    def _setup_workflow(cls):
        workflow = {
            "id": "test_wait_jobs",
            "name": "test_wait_jobs",
            "start_worker_id": "generate_numbers_1",
            "workers": {
                "generate_numbers_1": {
                    "meta_worker": "generate_numbers",
                    "default_inputs": {
                        "numbers_range": [0, 10],
                        "sleep": 0
                    },
                    "next_workers": ["filter_1"]
                },
                "filter_1": {
                    "meta_worker": "filter",
                    "default_inputs": {
                        "min": 1000
                    },
                    "next_workers": ["wait_jobs_1"]
                },
                "wait_jobs_1": {
                    "meta_worker": "wait_jobs",
                    "default_inputs": {
                        "wait_jobs_from": ["generate_numbers_1", "filter_1", "wait_jobs_1"]
                    },
                    "next_workers": ["count_numbers_1"]
                },
                "count_numbers_1": {
                    "meta_worker": "count_numbers",
                    "next_workers": []
                }
            }
        }

        cls.workflow_path = "/tmp/wait_jobs_test_workflows"
        if not os.path.exists(cls.workflow_path):
            os.makedirs(cls.workflow_path)
        open(cls.workflow_path+"/workflow_test_wait_jobs.json", 'w').write(
            poliglo.utils.to_json(workflow)
        )


    @classmethod
    def _setup_master_mind_server(cls):
        cls._setup_config()
        cls._setup_workflow()

        isolated_env = os.environ.copy()
        isolated_env['CONFIG_PATH'] = cls.config_path
        isolated_env['WORKFLOWS_PATH'] = cls.workflow_path
        isolated_env['POLIGLO_SERVER_PORT'] = "9016"
        cmd = ["poliglo_server",]
        cls.server_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, shell=False, env=isolated_env, preexec_fn=os.setsid
        )

    @classmethod
    def _setup_workers_files(cls):
        cls.workers_path = "/tmp/wait_jobs_test_workers"
        if not os.path.exists(cls.workers_path):
            os.makedirs(cls.workers_path)

        #WORKER generate_numbers
        open(cls.workers_path+"/generate_numbers.py", 'w').write("""import time
import poliglo
import os

POLIGLO_SERVER_URL = os.environ.get('POLIGLO_SERVER_URL')
META_WORKER = 'generate_numbers'

def process(specific_info, data, *args):
    inputs = poliglo.inputs.get_inputs(data, specific_info)
    numbers_range = inputs.get('numbers_range')
    sleep_time = inputs.get('sleep')

    for i in range(numbers_range[0], numbers_range[1]):
        time.sleep(sleep_time)
        yield {'number': i}

poliglo.runner.default_main(POLIGLO_SERVER_URL, META_WORKER, process)
""")

        #WORKER filter
        open(cls.workers_path+"/filter.py", 'w').write("""import time
import poliglo
import os

POLIGLO_SERVER_URL = os.environ.get('POLIGLO_SERVER_URL')
META_WORKER = 'filter'

def process(specific_info, data, *args):
    inputs = poliglo.inputs.get_inputs(data, specific_info)
    min_value = inputs.get("min")
    if inputs['number'] < min_value:
        return [inputs,]
    return []

poliglo.runner.default_main(POLIGLO_SERVER_URL, META_WORKER, process)
""")

        #WORKER wait_jobs
        copyfile(os.path.abspath(__file__), cls.workers_path+'/wait_jobs.py')

        #WORKER count_numbers
        open(cls.workers_path+"/count_numbers.py", 'w').write("""import time
import poliglo
import os

POLIGLO_SERVER_URL = os.environ.get('POLIGLO_SERVER_URL')
META_WORKER = 'count_numbers'

def process(specific_info, data, *args):
    connection = args[0].get('connection')

    inputs = poliglo.inputs.get_inputs(data, specific_info)
    queue = inputs.get('__read_from_queue')

    total = 0
    for queue_data in connection.zrange(queue, 0, -1):
        total +=1
    return [{'total': total}]

config = poliglo.preparation.get_config(POLIGLO_SERVER_URL, 'all')
connection = poliglo.preparation.get_connection(config)
poliglo.runner.default_main(POLIGLO_SERVER_URL, META_WORKER, process, {'connection': connection})
""")

    @classmethod
    def _setup_workers(cls):
        cls._setup_workers_files()
        isolated_env = os.environ.copy()
        isolated_env['WORKERS_PATHS'] = cls.workers_path
        isolated_env['POLIGLO_SERVER_URL'] = cls.config.get('all').get('POLIGLO_SERVER_URL')
        isolated_env['DEPLOY_USER'] = 'test_user'
        scripts_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                'deployment',
                'scripts'
            )
        )
        start_workers_path = os.path.join(scripts_dir, "start_workers.sh")

        cmd = [
            "/bin/bash",
            start_workers_path
        ]
        cls.workers_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, shell=False, env=isolated_env, preexec_fn=os.setsid
        )

    @classmethod
    def setUpClass(cls):
        cls._setup_master_mind_server()
        sleep(1)
        cls._setup_workers()

    def setUp(self):
        self.connection = poliglo.preparation.get_connection(self.config.get('all'))
        self.connection.flushall()

    @classmethod
    def tearDownClass(cls):
        os.killpg(cls.server_process.pid, signal.SIGTERM)
        os.killpg(cls.workers_process.pid, signal.SIGTERM)

    def test_wait_for_all_jobs(self):
        self.workflow_instance_id = poliglo.start.start_workflow_instance(
            self.connection,
            'test_wait_jobs', 'generate_numbers', 'generate_numbers_1', 'instance1', {}
        )
        queues = [None]
        while len(queues) > 0:
            sleep(1)
            queues = self.connection.keys("queue:*")
        total_finalized = self.connection.zcard(
            "workflows:test_wait_jobs:workflow_instances:%s:workers:count_numbers_1:finalized" % \
            self.workflow_instance_id
        )
        self.assertEqual(1, total_finalized)

    def test_last_message_are_filtered(self):
        self.workflow_instance_id = poliglo.start.start_workflow_instance(
            self.connection, 'test_wait_jobs',
            'generate_numbers', 'generate_numbers_1', 'instance1', {
                'numbers_range': [995, 1005]
            }
        )
        queues = [None]
        while len(queues) > 0:
            sleep(1)
            queues = self.connection.keys("queue:*")
        total_finalized = self.connection.zcard(
            "workflows:test_wait_jobs:workflow_instances:%s:workers:count_numbers_1:finalized" % \
            self.workflow_instance_id
        )
        self.assertEqual(1, total_finalized)
