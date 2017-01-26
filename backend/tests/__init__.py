import os
import errno
import unittest

import poliglo_server
import poliglo
from poliglo.utils import to_json, json_loads

CONFIG = {
    "all": {
        "REDIS_HOST": os.environ.get("TEST_REDIS_HOST", "localhost"),
        "REDIS_PORT": 6379,
        "REDIS_DB": 1,
        "POLIGLO_SERVER_URL": "http://localhost:9015"
    },
    'filter': {
        'SOMETHING': 1
    }
}

WORKFLOWS = [
    {
        "id": "workflow_1",
        "name": "Script 1",
        "start_worker_id": "filter_1",
        "workers": {
            "filter_1": {
                "meta_worker": "filter",
                "default_inputs": {
                    "include": ["price", ">=", 100]
                },
                "next_workers": ["write_1"]
            },
            "write_1": {
                "meta_worker": "write",
                "default_inputs": {
                    "target": "/tmp/example"
                }
            }
        }
    },
    {
        "id": "workflow_2",
        "name": "Script 2",
        "start_worker_id    ": "filter_1",
        "workers": {
            "filter_1": {
                "meta_worker": "filter",
                "default_inputs": {
                    "include": ["price", ">=", 100]
                },
                "next_workers": ["add_one_1"]
            },
            "add_one_1": {
                "meta_worker": "add_one",
                "default_inputs": {
                    "target_fields": ["price"]
                },
                "next_workers": ["filter_2"]
            },
            "filter_2": {
                "meta_worker": "filter",
                "default_inputs": {
                    "include": ["price", ">=", 101]
                },
                "next_workers": ["send_to_s3_1"]
            },
            "send_to_s3_1": {
                "meta_worker": "send_to_s3",
                "default_inputs": {
                    "read_file": "/tmp/example"
                }
            }
        }
    }
]

def _mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def _write_file(dirname, file_name, data):
    abs_dirname = os.path.abspath(dirname)
    _mkdir_p(abs_dirname)
    abs_file_name = os.path.join(abs_dirname, file_name)
    with open(abs_file_name, 'w') as _file:
        _file.write(data)
    return abs_file_name

class TestPoligloServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_base_path = '/tmp/tests_poliglo_server'
        cls.config_path = _write_file(
            cls.test_base_path,
            'config.json',
            to_json(CONFIG)
        )
        cls.workflows_path = os.path.join(cls.test_base_path, 'workflows')

        for workflow in WORKFLOWS:
            _write_file(
                cls.workflows_path,
                'workflow_'+workflow.get('id')+'.json',
                to_json(workflow)
            )

        poliglo_server.CONFIG = poliglo_server.load_config(cls.config_path)
        poliglo_server.DEBUG = True

        poliglo_server.WORKFLOWS = poliglo_server.load_workflows(
            cls.workflows_path
        )
        cls.app = poliglo_server.app.test_client()

    def setUp(self):
        self.connection = poliglo.preparation.get_connection(CONFIG.get('all'))
        self.connection.flushall()

    def tearDown(self):
        pass

    def test_get_meta_workers(self):
        response = self.app.get('/meta_workers')
        expected_meta_workers = ["filter", "write", "send_to_s3", "add_one"]
        meta_workers = json_loads(response.data)
        self.assertEqual(sorted(expected_meta_workers), sorted(meta_workers))

    def test_get_meta_worker_config(self):
        response = self.app.get('/meta_workers/filter/config')
        config = json_loads(response.data)
        expected_config = CONFIG.get('all')
        expected_config.update(CONFIG.get('filter'))
        self.assertEqual(expected_config, config)

    def test_get_meta_worker_workflows(self):
        response = self.app.get('/meta_workers/filter/workflows')
        meta_worker_workflows = json_loads(response.data)
        self.assertEqual(
            ['filter_1'],
            meta_worker_workflows['workflow_1'].keys()
        )
        self.assertEqual(
            sorted(['filter_1', 'filter_2']),
            sorted(meta_worker_workflows['workflow_2'].keys())
        )

        self.assertEqual(
            WORKFLOWS[1]['workers']['filter_1']['default_inputs'],
            meta_worker_workflows['workflow_2']['filter_1']['default_inputs']
        )

    def test_get_meta_worker_workflow_set_outputs_type(self):
        response = self.app.get('/meta_workers/filter/workflows')
        meta_worker_workflows = json_loads(response.data)
        self.assertEqual(
            ['write'],
            meta_worker_workflows['workflow_1']['filter_1'].get('__next_workers_types')
        )

    def test_get_all_workflows(self):
        response = self.app.get('/workflows')
        workflows = json_loads(response.data)
        self.assertEqual(2, len(workflows))
        workflow_names = [workflow.get('name') for workflow in workflows]
        self.assertEqual(sorted(['Script 1', 'Script 2']), sorted(workflow_names))

    def test_get_all_workflows_grouped(self):
        response = self.app.get('/workflows?by_group=1')
        workflows = json_loads(response.data)
        self.assertEqual(['No group'], workflows.keys())
        self.assertEqual(2, len(workflows['No group']))

    def test_get_one_workflow(self):
        response = self.app.get('/workflows/workflow_1')
        workflow = json_loads(response.data)
        self.assertEqual('Script 1', workflow.get('name'))

    def test_workflow_get_workflow_instance_empty(self):
        response = self.app.get('/workflows/workflow_1/workflow_instances')
        workflow_instances = json_loads(response.data)
        self.assertEqual(0, len(workflow_instances))

    def test_workflow_get_workflow_instance_one_exists(self):
        url = '/workflows/workflow_1/workflow_instances'
        self.app.post(
            url, data=to_json({'name': 'Script 1 - 1'}),
            headers={'content-type':'application/json'}
        )

        response = self.app.get(url)
        workflow_instances = json_loads(response.data)
        self.assertEqual(1, len(workflow_instances))
        self.assertEqual('Script 1 - 1', workflow_instances[0].get('name'))

    def test_get_one_workflow_instance(self):
        response = self.app.post(
            '/workflows/workflow_1/workflow_instances', data=to_json({'name': 'Script 1 - 1'}),
            headers={'content-type':'application/json'}
        )
        workflow_instance_id = json_loads(response.data).get('id')
        response = self.app.get('/workflow_instances/'+workflow_instance_id)
        workflow_instance = json_loads(response.data)
        self.assertEqual('Script 1 - 1', workflow_instance.get('name'))

    def test_get_workflow_instance_status_pending(self):
        response = self.app.post(
            '/workflows/workflow_1/workflow_instances', data=to_json({'name': 'Script 1 - 1'}),
            headers={'content-type':'application/json'}
        )
        workflow_instance_id = json_loads(response.data).get('id')
        response = self.app.get('/workflow_instances/'+workflow_instance_id+'/status')
        workflow_instance = json_loads(response.data)
        self.assertEqual('pending', workflow_instance.get('status'))

    @unittest.skip("Missing implementation")
    def test_get_workflow_instance_status_done(self):
        pass

    @unittest.skip("Missing implementation")
    def test_get_workflow_instance_status_errors(self):
        pass

    @unittest.skip("Missing implementation")
    def test_get_workflow_instance_worker_jobs_type(self):
        pass

    @unittest.skip("Missing implementation")
    def test_action_over_worker_job_type(self):
        pass

    @unittest.skip("Missing implementation")
    def test_get_workflow_instance_stats(self):
        pass

if __name__ == '__main__':
    unittest.main()
