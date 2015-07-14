import os, errno
import unittest
import tempfile

import poliglo_server
import poliglo
from poliglo.utils import to_json, json_loads

CONFIG = {
    "all": {
        "REDIS_HOST": "127.0.0.1",
        "REDIS_PORT": 6379,
        "REDIS_DB": 1,
        "POLIGLO_SERVER_URL": "http://localhost:9015"
    },
    'filter': {
        'SOMETHING': 1
    }
}

SCRIPTS = [
    {
        "id": "script_1",
        "name": "Script 1",
        "start_worker_id": "filter_1",
        "workers": [
            {
                "id": "filter_1",
                "worker_type": "filter",
                "default_inputs": {
                    "include": ["price", ">=", 100]
                },
                "next_workers": ["write_1"]
            },
            {
                "id": "write_1",
                "worker_type": "write",
                "default_inputs": {
                    "target": "/tmp/example"
                }
            }
        ]
    },
    {
        "id": "script_2",
        "name": "Script 2",
        "start_worker_id    ": "filter_1",
        "workers": [
            {
                "id": "filter_1",
                "worker_type": "filter",
                "default_inputs": {
                    "include": ["price", ">=", 100]
                },
                "next_workers": ["add_one_1"]
            },
            {
                "id": "add_one_1",
                "worker_type": "add_one",
                "default_inputs": {
                    "target_fields": ["price"]
                },
                "next_workers": ["filter_2"]
            },
            {
                "id": "filter_2",
                "worker_type": "filter",
                "default_inputs": {
                    "include": ["price", ">=", 101]
                },
                "next_workers": ["send_to_s3_1"]
            },
            {
                "id": "send_to_s3_1",
                "worker_type": "send_to_s3",
                "default_inputs": {
                    "read_file": "/tmp/example"
                }
            }
        ]
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
        cls.scripts_path = os.path.join(cls.test_base_path, 'scripts')

        for script in SCRIPTS:
            _write_file(
                cls.scripts_path,
                'script_'+script.get('id')+'.json',
                to_json(script)
            )

        poliglo_server.CONFIG = poliglo_server.load_config(cls.config_path)
        poliglo_server.DEBUG = True

        poliglo_server.SCRIPTS = poliglo_server.load_scripts(
            cls.scripts_path
        )
        cls.app = poliglo_server.app.test_client()

    def setUp(self):
        self.connection = poliglo.get_connection(CONFIG.get('all'))
        self.connection.flushall()

    def tearDown(self):
        pass

    def test_get_worker_types(self):
        response = self.app.get('/worker_types')
        expected_worker_types = ["filter", "write", "send_to_s3", "add_one"]
        worker_types = json_loads(response.data)
        self.assertEqual(sorted(expected_worker_types), sorted(worker_types))

    def test_get_worker_type_config(self):
        response = self.app.get('/worker_types/filter/config')
        config = json_loads(response.data)
        expected_config = CONFIG.get('all')
        expected_config.update(CONFIG.get('filter'))
        self.assertEqual(expected_config, config)

    def test_get_worker_type_scripts(self):
        response = self.app.get('/worker_types/filter/scripts')
        worker_type_scripts = json_loads(response.data)
        self.assertEqual(
            ['filter_1'],
            worker_type_scripts['script_1'].keys()
        )
        self.assertEqual(
            sorted(['filter_1', 'filter_2']),
            sorted(worker_type_scripts['script_2'].keys())
        )

        self.assertEqual(
            SCRIPTS[1]['workers'][0]['default_inputs'],
            worker_type_scripts['script_2']['filter_1']['default_inputs']
        )

    def test_get_worker_type_script_set_outputs_type(self):
        response = self.app.get('/worker_types/filter/scripts')
        worker_type_scripts = json_loads(response.data)
        self.assertEqual(
            ['write'],
            worker_type_scripts['script_1']['filter_1'].get('__next_workers_types')
        )

    def test_get_all_scripts(self):
        response = self.app.get('/scripts')
        scripts = json_loads(response.data)
        self.assertEqual(2, len(scripts))
        script_names = [script.get('name') for script in scripts]
        self.assertEqual(sorted(['Script 1', 'Script 2']), sorted(script_names))

    def test_get_all_scripts_grouped(self):
        response = self.app.get('/scripts?by_group=1')
        scripts = json_loads(response.data)
        self.assertEqual(['No group'], scripts.keys())
        self.assertEqual(2, len(scripts['No group']))

    def test_get_one_script(self):
        response = self.app.get('/scripts/script_1')
        script = json_loads(response.data)
        self.assertEqual('Script 1', script.get('name'))

    def test_get_one_script(self):
        response = self.app.get('/scripts/script_1')
        script = json_loads(response.data)
        self.assertEqual('Script 1', script.get('name'))

    def test_script_get_process_empty(self):
        response = self.app.get('/scripts/script_1/processes')
        processes = json_loads(response.data)
        self.assertEqual(0, len(processes))

    def test_script_get_process_one_exists(self):
        url = '/scripts/script_1/processes'
        self.app.post(
            url, data=to_json({'name': 'Script 1 - 1'}),
            headers={'content-type':'application/json'}
        )

        response = self.app.get(url)
        processes = json_loads(response.data)
        self.assertEqual(1, len(processes))
        self.assertEqual('Script 1 - 1', processes[0].get('name'))

    def test_get_one_process(self):
        response = self.app.post(
            '/scripts/script_1/processes', data=to_json({'name': 'Script 1 - 1'}),
            headers={'content-type':'application/json'}
        )
        process_id = json_loads(response.data).get('id')
        response = self.app.get('/processes/'+process_id)
        process = json_loads(response.data)
        self.assertEqual('Script 1 - 1', process.get('name'))

    def test_get_process_status_running(self):
        response = self.app.post(
            '/scripts/script_1/processes', data=to_json({'name': 'Script 1 - 1'}),
            headers={'content-type':'application/json'}
        )
        process_id = json_loads(response.data).get('id')
        response = self.app.get('/processes/'+process_id+'/status')
        process = json_loads(response.data)
        self.assertEqual('running', process.get('status'))

    @unittest.skip("Missing implementation")
    def test_get_process_status_done(self):
        pass

    @unittest.skip("Missing implementation")
    def test_get_process_status_errors(self):
        pass

    @unittest.skip("Missing implementation")
    def test_get_process_status_pending(self):
        pass

    @unittest.skip("Missing implementation")
    def test_get_process_worker_jobs_type(self):
        pass

    @unittest.skip("Missing implementation")
    def test_action_over_worker_job_type(self):
        pass

    @unittest.skip("Missing implementation")
    def test_get_process_stats(self):
        pass

if __name__ == '__main__':
    unittest.main()
