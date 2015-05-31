# -*- coding: utf-8 -*-
import os
import uuid
import json
import fnmatch
import itertools
import time
from datetime import datetime

from flask import Flask, request, abort, jsonify, Response
from flask.ext.cors import CORS
from poliglo import get_connection, add_data_to_next_worker
from poliglo import REDIS_KEY_INSTANCE_WORKER_DISCARDED, REDIS_KEY_INSTANCE_WORKER_JOBS, REDIS_KEY_INSTANCE_WORKER_ERRORS
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


app = Flask(__name__)
cors = CORS(app)

def load_config(path):
    if path and os.path.exists(path):
        return json.load(open(path))
    return {}

def load_scripts(path):
    scripts = []
    if path and os.path.exists(path):
        for root, _, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, 'script_*'):
                script = json.load(open(os.path.join(root, filename)))
                scripts.append(script)
    return scripts

CONFIG = load_config(os.environ.get('CONFIG_PATH'))
SCRIPTS = load_scripts(os.environ.get('SCRIPTS_PATH'))

def _get_script(script_id):
    script_found = [script for script in SCRIPTS if script.get('id') == script_id]
    if len(script_found) == 0:
        abort(404)
    return script_found[0]

def _get_process(connection, process_id):
    processes_keys = connection.keys(
        'scripts:*:processes:%s' % process_id
    )
    found_something = False
    if len(processes_keys) > 0:
        process_data = connection.hgetall(processes_keys[0])
        if process_data:
            script_type = processes_keys[0].split('scripts:')[1].split(':')[0]
            process_data['type'] = script_type
            process_data['id'] = process_id
            found_something = True
    if found_something:
        return process_data
    else:
        abort(404, "No such with id: %s" % process_id)

def _redis_mget(redis_con, keys_wild):
    workers_keys = redis_con.keys(keys_wild)
    if len(workers_keys) == 0:
        return [], []
    return workers_keys, redis_con.mget(workers_keys)

def _workers_dict_data(key_prefix, workers_keys, workers_data):
    workers = [worker_key.split(key_prefix)[1].split(':')[0] for worker_key in workers_keys]
    return dict(zip(workers, workers_data))


@app.route('/worker_types', methods=['GET'])
def get_workers():
    workers_list = [
        worker.get('worker_type')
        for script in SCRIPTS
        for worker in script.get('workers')
    ]
    return Response(
        json.dumps(
            list(set(workers_list))
        ), mimetype='application/json'
    )

@app.route('/worker_types/<worker_type>/config', methods=['GET'])
def get_worker_config(worker_type):
    config = CONFIG.get('all', {})
    config.update(CONFIG.get(worker_type, {}))
    return jsonify(config)

@app.route('/worker_types/<worker_type>/scripts', methods=['GET'])
def get_worker_plan(worker_type):
    return_data = {}
    for script in SCRIPTS:
        workers = [
            worker for worker in script.get('workers', [])
            if worker.get('worker_type') == worker_type
        ]
        for worker in workers:
            if not return_data.get(script.get('id')):
                return_data[script.get('id')] = {}
            return_data[script.get('id')][worker.get('id')] = worker
    return jsonify(return_data)


@app.route('/scripts', methods=['GET'])
def get_all_scripts():
    scripts = []
    for script in SCRIPTS:
        scripts.append({
            'type': script.get('id'),
            'name': script.get('name'),
            'start_worker': script.get('start_worker'),
            'group': script.get('group') or 'No group'
        })
    if request.args.get('by_group') is not None:
        groups = {}
        for script in scripts:
            group = script.get('group')
            if not groups.get(group):
                groups[group] = []
            groups[group].append(script)
        scripts = groups
    return Response(json.dumps(scripts), mimetype='application/json')

@app.route('/scripts/<script_id>', methods=['GET'])
def get_script(script_id):
    script = _get_script(script_id)
    return jsonify(script)

@app.route('/scripts/<script_id>/processes', methods=['GET'])
def get_script_processes(script_id):
    redis_con = get_connection(CONFIG.get('all'))
    processes = redis_con.zrange('scripts:%s:processes' % script_id, -25, -1)
    return_data = [json.loads(process) for process in processes]
    return Response(json.dumps(return_data), mimetype='application/json')

@app.route('/processes/<process_id>', methods=['GET'])
def get_process(process_id):
    connection = get_connection(CONFIG.get('all'))
    script = _get_process(connection, process_id)
    return jsonify(script)

@app.route('/processes/<process_id>/status', methods=['GET'])
def get_process_status(process_id):
    # TODO: refactor this code
    # TODO: support discarded
    connection = get_connection(CONFIG.get('all'))
    process_data = _get_process(connection, process_id)

    errors_keys = connection.keys(
        REDIS_KEY_INSTANCE_WORKER_ERRORS % (
            process_data.get('type'), process_id, '*'
        )
    )
    if len(errors_keys) > 0:
        return jsonify({'status': 'errors'})

    total_jobs_keys = connection.keys(
        REDIS_KEY_INSTANCE_WORKER_JOBS % (
            process_data.get('type'), process_id, '*', 'total'
        )
    )

    done_jobs_keys = connection.keys(
        REDIS_KEY_INSTANCE_WORKER_JOBS % (
            process_data.get('type'), process_id, '*', 'done'
        )
    )

    pipe = connection.pipeline()
    temp_union = 'temp:%s:%s' % (datetime.now().isoformat().split('T')[0], str(uuid.uuid4()))
    pipe.sunionstore(temp_union, *total_jobs_keys)

    temp_diff = 'temp:%s:%s' % (datetime.now().isoformat().split('T')[0], str(uuid.uuid4()))
    pipe.sdiffstore(temp_diff, temp_union, *done_jobs_keys)
    pipe.delete(temp_diff)
    pipe.delete(temp_union)
    execute_result = pipe.execute()
    pending_jobs = execute_result[1]

    if pending_jobs > 0:
        status = 'running'
    else:
        status = 'done'
    return jsonify({'status': status})

@app.route('/processes/<process_id>/workers/<worker_id>/<string:option>', methods=['GET'])
def get_process_worker_jobs_type(process_id, worker_id, option):
    connection = get_connection(CONFIG.get('all'))
    process_data = _get_process(connection, process_id)
    jobs = connection.zrange(
        "scripts:%s:processes:%s:workers:%s:%s" % (
            process_data.get('type'), process_id, worker_id, option
        ),
        -20, -1, withscores=True
    )
    for i, data in enumerate(jobs):
        raw_data, score = data
        jobs[i] = json.loads(raw_data)
        jobs[i]['redis_score'] = score
    return Response(
        json.dumps(jobs), mimetype='application/json'
    )

@app.route('/processes/<process_id>/workers/<worker_id>/errors/<redis_score>/<option>', methods=['GET'])
def action_over_worker_job_type(process_id, worker_id, redis_score, option):
    connection = get_connection(CONFIG.get('all'))
    process_data = _get_process(connection, process_id)
    redis_key = "scripts:%s:processes:%s:workers:%s:errors" % (
        process_data.get('type'), process_id, worker_id
    )
    errors_list = connection.zrangebyscore(redis_key, redis_score, redis_score)
    if len(errors_list) > 0:
        raw_data = errors_list[0]
        if option == 'retry':
            add_data_to_next_worker(connection, worker_id, raw_data)
        else:
            # discard
            connection.zadd(
                REDIS_KEY_INSTANCE_WORKER_DISCARDED % (process_data.get('type'), process_id, worker_id),
                time.time(),
                raw_data
            )
        connection.zremrangebyscore(redis_key, redis_score, redis_score)
    else:
        abort(404, "No such error id: %s" % redis_score)
    return jsonify({})

@app.route('/processes/<process_id>/stats', methods=['GET'])
def get_process_stats(process_id):
    # TODO: Refactor this code
    connection = get_connection(CONFIG.get('all'))
    process_data = _get_process(connection, process_id)

    workers_prefix = "scripts:%s:processes:%s:workers:" % (
        process_data.get('type'), process_id
    )
    workers_data = {}

    for status_type in ('done', 'total'):
        pipe = connection.pipeline()
        workers_keys = connection.keys(REDIS_KEY_INSTANCE_WORKER_JOBS % (process_data.get('type'), process_id, '*', status_type))
        for key in workers_keys:
            pipe.scard(key)
        workers_data[status_type] = _workers_dict_data(workers_prefix, workers_keys, pipe.execute())

    for status_type in ('errors', 'discarded', 'finalized'):
        pipe = connection.pipeline()
        workers_keys = connection.keys(workers_prefix+"*:"+status_type)
        for key in workers_keys:
            pipe.zcard(key)
        workers_data[status_type] = _workers_dict_data(workers_prefix, workers_keys, pipe.execute())

    workers_stats = {}
    for status_type, data in workers_data.iteritems():
        for worker, worker_num in data.iteritems():
            if not workers_stats.get(worker):
                workers_stats[worker] = {}
            if status_type == 'jobs_ids':
                workers_stats[worker]['total'] = worker_num
            else:
                workers_stats[worker][status_type] = worker_num

    for worker, values in workers_stats.iteritems():
        workers_stats[worker]['pending'] = int(values.get('total', 0)) - int(values.get('done', 0)) - int(values.get('errors', 0)) - int(values.get('discarded', 0))
    return jsonify({'workers': workers_stats})

if __name__ == '__main__':
  http_server = HTTPServer(WSGIContainer(app))
  http_server.listen(9015)
  IOLoop.instance().start()

