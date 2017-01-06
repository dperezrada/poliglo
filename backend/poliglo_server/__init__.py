# -*- coding: utf-8 -*-
import os
import re
import uuid
import json
import fnmatch
import time
import socket
import xmlrpclib
from datetime import datetime
from copy import copy

from flask import Flask, request, abort, jsonify, make_response, Response
from flask.ext.cors import CORS
from poliglo.preparation import get_connection
from poliglo.start import start_workflow_instance
from poliglo.outputs import add_data_to_next_worker
from poliglo.variables import REDIS_KEY_INSTANCE_WORKER_FINALIZED_JOBS, \
    REDIS_KEY_INSTANCE_WORKER_DISCARDED, REDIS_KEY_INSTANCE_WORKER_JOBS, \
    REDIS_KEY_INSTANCE_WORKER_ERRORS
from poliglo.utils import to_json, json_loads

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


app = Flask(__name__)
cors = CORS(app)

WORKERS_TYPES = {}

def load_config(path):
    if path and os.path.exists(path):
        return json.load(open(path))
    return {}

def _replace_sub_on_element(re_matched, worker_id):
    config_variable = re_matched.groups()[0]
    return CONFIG.get('all', {}).get(config_variable) or \
                CONFIG.get(worker_id, {}).get(config_variable)

def _replace_config_variables(workflow):
    for worker_id, worker in copy(workflow.get('workers', {})).iteritems():
        worker_raw_data = json.dumps(worker)
        worker_raw_data = re.sub(
            r'{{config\.([^}]+)}}',
            lambda match: _replace_sub_on_element(match, worker_id),
            worker_raw_data
        )
        workflow['workers'][worker_id] = json.loads(worker_raw_data)
    return workflow


def load_workflows(path):
    workflows = []
    if path and os.path.exists(path):
        for root, _, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, '*.json'):
                workflow = json.load(open(os.path.join(root, filename)))
                workflow = _replace_config_variables(workflow)
                for worker_id, worker in workflow.get('workers', {}).iteritems():
                    WORKERS_TYPES[worker_id] = worker.get('meta_worker')
                workflows.append(workflow)

    return workflows


CONFIG = load_config(os.environ.get('CONFIG_PATH'))
WORKFLOWS = load_workflows(os.environ.get('WORKFLOWS_PATH'))

def _get_workflow(workflow_id):
    workflow_found = [workflow for workflow in WORKFLOWS if workflow.get('id') == workflow_id]
    if len(workflow_found) == 0:
        abort(404)
    return workflow_found[0]

def _get_workflow_instance(connection, workflow_instance_id):
    workflow_instances_keys = connection.keys(
        'workflows:*:workflow_instances:%s' % workflow_instance_id
    )
    found_something = False
    if len(workflow_instances_keys) > 0:
        workflow_instance_data = connection.hgetall(workflow_instances_keys[0])
        if workflow_instance_data:
            workflow_type = workflow_instances_keys[0].split('workflows:')[1].split(':')[0]
            workflow_instance_data['type'] = workflow_type
            workflow_instance_data['id'] = workflow_instance_id
            found_something = True
    if found_something:
        return workflow_instance_data
    else:
        abort(404, "No such with id: %s" % workflow_instance_id)

def _redis_mget(redis_con, keys_wild):
    workers_keys = redis_con.keys(keys_wild)
    if len(workers_keys) == 0:
        return [], []
    return workers_keys, redis_con.mget(workers_keys)

def _workers_dict_data(key_prefix, workers_keys, workers_data):
    workers = [worker_key.split(key_prefix)[1].split(':')[0] for worker_key in workers_keys]
    return dict(zip(workers, workers_data))

# ---------------
# Error handling
# ---------------
@app.errorhandler(404)
def page_not_found(e):
    return make_response(jsonify({'error': 'Page not found'}), 404)

@app.errorhandler(500)  # Doesn't work in debug mode
@app.errorhandler(socket.gaierror)  # When supervisor is down
def internal_server_error(e):
    return make_response(jsonify({'error': 'Internal server error'}), 500)

# -------
# Routes
# -------
@app.route('/meta_workers', methods=['GET'])
def get_workers():
    meta_workers_list = [
        worker.get('meta_worker')
        for workflow in WORKFLOWS
        for _, worker in workflow.get('workers', {}).iteritems()
    ]
    return Response(
        json.dumps(
            list(set(meta_workers_list))
        ), mimetype='application/json'
    )

@app.route('/meta_workers/<meta_worker>/config', methods=['GET'])
def get_worker_config(meta_worker):
    config = CONFIG.get('all', {})
    config.update(CONFIG.get(meta_worker, {}))
    return jsonify(config)

@app.route('/meta_workers/<meta_worker>/workflows', methods=['GET'])
def get_worker_plan(meta_worker):
    return_data = {}
    for workflow in WORKFLOWS:
        workers = {
            worker_id: worker for worker_id, worker in workflow.get('workers', {}).iteritems()
            if worker.get('meta_worker') == meta_worker
        }
        for worker_id, worker in workers.iteritems():
            if not return_data.get(workflow.get('id')):
                return_data[workflow.get('id')] = {}
            worker['__next_workers_types'] = [
                WORKERS_TYPES.get(output_worker_id) for output_worker_id in worker.get('next_workers', [])
            ]
            return_data[workflow.get('id')][worker_id] = worker
    return jsonify(return_data)


@app.route('/workflows', methods=['GET'])
def get_all_workflows():
    workflows = []
    for workflow in WORKFLOWS:
        workflows.append({
            'type': workflow.get('id'),
            'name': workflow.get('name'),
            'start_worker_id': workflow.get('start_worker_id'),
            'group': workflow.get('group') or 'No group'
        })
    if request.args.get('by_group') is not None:
        groups = {}
        for workflow in workflows:
            group = workflow.get('group')
            if not groups.get(group):
                groups[group] = []
            groups[group].append(workflow)
        workflows = groups
    return Response(json.dumps(workflows), mimetype='application/json')

@app.route('/workflows/<workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    workflow = _get_workflow(workflow_id)
    return jsonify(workflow)

@app.route('/workflows/<workflow_id>/workflow_instances', methods=['GET'])
def get_workflow_workflow_instances(workflow_id):
    redis_con = get_connection(CONFIG.get('all'))
    workflow_instances = redis_con.zrange('workflows:%s:workflow_instances' % workflow_id, -25, -1)
    return_data = [json.loads(workflow_instance) for workflow_instance in workflow_instances]
    return Response(json.dumps(return_data), mimetype='application/json')

@app.route('/workflows/<workflow_id>/workflow_instances', methods=['POST'])
def create_workflow_workflow_instance(workflow_id):
    redis_con = get_connection(CONFIG.get('all'))
    workflow = _get_workflow(workflow_id)
    data = request.get_json()
    start_worker_id = workflow.get('start_worker_id')
    meta_worker = ([
        worker.get('meta_worker') for worker_id, worker in workflow.get('workers', {}).iteritems()
        if worker_id == start_worker_id
    ] or [None])[0]
    if meta_worker:
        workflow_instance_id = start_workflow_instance(
            redis_con, workflow_id, meta_worker, workflow.get('start_worker_id'),
            data.get('name'), data.get('data', {})
        )
        return Response(json.dumps({'id': workflow_instance_id}), status=201)
    return Response(status=404)

@app.route('/workflow_instances/<workflow_instance_id>', methods=['GET'])
def get_workflow_instance(workflow_instance_id):
    connection = get_connection(CONFIG.get('all'))
    workflow = _get_workflow_instance(connection, workflow_instance_id)
    return jsonify(workflow)

@app.route('/workflow_instances/<workflow_instance_id>/status', methods=['GET'])
def get_workflow_instance_status(workflow_instance_id):
    # TODO: refactor this code
    connection = get_connection(CONFIG.get('all'))
    workflow_instance_data = _get_workflow_instance(connection, workflow_instance_id)
    if not workflow_instance_data.get('start_time'):
        return jsonify({'status': 'pending'})

    errors_keys = connection.keys(
        REDIS_KEY_INSTANCE_WORKER_ERRORS % (
            workflow_instance_data.get('type'), workflow_instance_id, '*'
        )
    )
    if len(errors_keys) > 0:
        return jsonify({'status': 'errors'})

    total_jobs_keys = connection.keys(
        REDIS_KEY_INSTANCE_WORKER_JOBS % (
            workflow_instance_data.get('type'), workflow_instance_id, '*', 'total'
        )
    )

    done_jobs_keys = connection.keys(
        REDIS_KEY_INSTANCE_WORKER_JOBS % (
            workflow_instance_data.get('type'), workflow_instance_id, '*', 'done'
        )
    )

    discarded_jobs_keys = connection.keys(
        REDIS_KEY_INSTANCE_WORKER_JOBS % (
            workflow_instance_data.get('type'), workflow_instance_id, '*', 'removed'
        )
    )

    pipe = connection.pipeline()
    temp_union = 'temp:%s:%s' % (datetime.now().isoformat().split('T')[0], str(uuid.uuid4()))
    pipe.sunionstore(temp_union, *total_jobs_keys)

    temp_diff = 'temp:%s:%s' % (datetime.now().isoformat().split('T')[0], str(uuid.uuid4()))
    pipe.sdiffstore(temp_diff, temp_union, *(done_jobs_keys + discarded_jobs_keys))
    pipe.delete(temp_diff)
    pipe.delete(temp_union)
    execute_result = pipe.execute()
    pending_jobs = execute_result[1]

    if pending_jobs > 0:
        status = 'running'
    else:
        status = 'done'
    runned_for = ''
    if workflow_instance_data.get('start_time') and workflow_instance_data.get('update_time'):
        try:
            runned_for = float(workflow_instance_data.get('update_time')) - \
                float(workflow_instance_data.get('start_time'))
        except:
            pass
    return jsonify({'status': status, 'runned_for': runned_for})

@app.route('/workflow_instances/<workflow_instance_id>/workers/<worker_id>/<string:option>', methods=['GET'])
def get_workflow_instance_worker_jobs_type(workflow_instance_id, worker_id, option):
    connection = get_connection(CONFIG.get('all'))
    workflow_instance_data = _get_workflow_instance(connection, workflow_instance_id)
    jobs = connection.zrange(
        "workflows:%s:workflow_instances:%s:workers:%s:%s" % (
            workflow_instance_data.get('type'), workflow_instance_id, worker_id, option
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

# options: retry, discard
@app.route('/workflow_instances/<workflow_instance_id>/workers/<worker_id>/errors/<option>/<redis_score>', methods=['GET'])
def action_over_worker_job_type(workflow_instance_id, worker_id, option, redis_score):
    connection = get_connection(CONFIG.get('all'))
    workflow_instance_data = _get_workflow_instance(connection, workflow_instance_id)
    workflow_id = workflow_instance_data.get('type')
    workflow = _get_workflow(workflow_id)
    redis_key = "workflows:%s:workflow_instances:%s:workers:%s:errors" % (
        workflow_instance_data.get('type'), workflow_instance_id, worker_id
    )
    if redis_score == 'all':
        errors_list = connection.zrange(redis_key, 0, -1, withscores=True)
    else:
        errors_list = connection.zrangebyscore(redis_key, redis_score, redis_score, withscores=True)
    if len(errors_list) > 0:
        for raw_data, redis_score in errors_list:
            if option == 'retry':
                meta_worker = [
                    worker.get('meta_worker') for it_worker_id, worker in workflow.get('workers', {}).iteritems()
                    if it_worker_id == worker_id
                ]
                add_data_to_next_worker(connection, meta_worker[0], raw_data)
            else:
                # discard
                connection.zadd(
                    REDIS_KEY_INSTANCE_WORKER_DISCARDED % (workflow_instance_data.get('type'), workflow_instance_id, worker_id),
                    time.time(),
                    raw_data
                )
                discarded_jobs_ids = json.loads(raw_data).get('jobs_ids', [])
                if discarded_jobs_ids:
                    discarded_jobs_key = REDIS_KEY_INSTANCE_WORKER_JOBS % (workflow_instance_data.get('type'), workflow_instance_id, worker_id, 'removed')
                    connection.sadd(discarded_jobs_key, *discarded_jobs_ids)
            connection.zremrangebyscore(redis_key, redis_score, redis_score)
    else:
        abort(404, "No such error id: %s" % redis_score)
    return jsonify({})

@app.route('/workflow_instances/<workflow_instance_id>/stats', methods=['GET'])
def get_workflow_instance_stats(workflow_instance_id):
    connection = get_connection(CONFIG.get('all'))
    workflow_instance_data = _get_workflow_instance(connection, workflow_instance_id)

    workers_prefix = "workflows:%s:workflow_instances:%s:workers:" % (
        workflow_instance_data.get('type'), workflow_instance_id
    )
    workers_data = {}

    for status_type in ('done', 'total'):
        pipe = connection.pipeline()
        workers_keys = connection.keys(REDIS_KEY_INSTANCE_WORKER_JOBS % (workflow_instance_data.get('type'), workflow_instance_id, '*', status_type))
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

    for key in connection.keys(workers_prefix+'*:timing'):
        worker = key.split(workers_prefix)[1].split(':')[0]
        key_values = [float(x) for x in connection.lrange(key, 0, -1)]
        workers_stats[worker]['total_time'] = sum(key_values)
        workers_stats[worker]['average_time'] = workers_stats[worker]['total_time']/len(key_values)

    for worker, values in workers_stats.iteritems():
        workers_stats[worker]['pending'] = int(values.get('total', 0)) - int(
            values.get('done', 0)) - int(values.get('errors', 0)) - int(values.get('discarded', 0))
    return jsonify({
        'workers': workers_stats,
        'start_time': workflow_instance_data.get('start_time'),
        'creation_time': workflow_instance_data.get('creation_time'),
        'update_time': workflow_instance_data.get('update_time')
    })


def _find_last_worker_id(workflow, next_worker_id):
    next_workers_ids = workflow.get('workers', {}).get(next_worker_id, {}).get('next_workers', [])
    if len(next_workers_ids) == 0:
        return [next_worker_id, ]
    else:
        final_workers = []
        for worker_id in next_workers_ids:
            final_workers += _find_last_worker_id(workflow, worker_id)
        return final_workers



@app.route('/workflow_instances/<workflow_instance_id>/outputs', methods=['GET'])
def get_workflow_instance_outputs(workflow_instance_id):
    connection = get_connection(CONFIG.get('all'))
    workflow_instance_data = _get_workflow_instance(connection, workflow_instance_id)
    workflow_id = workflow_instance_data.get('type')
    workflow = _get_workflow(workflow_id)
    # TODO: Manage multiple final nodes
    worker_id = _find_last_worker_id(workflow, workflow.get('start_worker_id'))[0]
    target_key = REDIS_KEY_INSTANCE_WORKER_FINALIZED_JOBS % (workflow_id, workflow_instance_id, worker_id)
    return to_json([
        json_loads(data).get('workers_output', {}).get(worker_id) for data in connection.zrange(target_key, 0, -1)
    ])

@app.route('/supervisor/status', methods=['GET'])
def supervisor_status():
    server = get_supervisor_endpoint()
    return to_json(server.supervisor.getAllProcessInfo())

@app.route('/supervisor/<process_name>/start', methods=['POST'])
def supervisor_start_process(process_name):
    server = get_supervisor_endpoint()
    return to_json(server.supervisor.startProcess(process_name, False))

@app.route('/supervisor/<process_name>/stop', methods=['POST'])
def supervisor_stop_process(process_name):
    server = get_supervisor_endpoint()
    return to_json(server.supervisor.stopProcess(process_name, False))

def get_supervisor_endpoint():
    return xmlrpclib.Server('%s/RPC2' % os.environ.get('POLIGLO_WORKER_URL'))

def start_server():
    port = int(os.environ.get('POLIGLO_SERVER_PORT') or 9015)
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(port)
    IOLoop.instance().start()

if __name__ == '__main__':
    app.DEBUG = True
    start_server()
