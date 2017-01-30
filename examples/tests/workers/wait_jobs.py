#!/usr/bin/env python
# -*- coding: utf-8 -*-

#req:
#end req

# TODO: this should have a finalized queue that takes into account the waiting ellements for this instance only

import os
import uuid
from datetime import datetime
import json
import hashlib
from time import time

import poliglo

def check_if_waiting_is_done(connection, workflow_id, workflow_instance_id, waiting_workers_ids):
    total_jobs_keys = [
        poliglo.variables.REDIS_KEY_INSTANCE_WORKER_JOBS % (
            workflow_id, workflow_instance_id, wait_jobs_from, 'total'
        )
        for wait_jobs_from in waiting_workers_ids
    ]

    done_jobs_keys = [
        poliglo.variables.REDIS_KEY_INSTANCE_WORKER_JOBS % (
            workflow_id, workflow_instance_id, wait_jobs_from, 'done'
        )
        for wait_jobs_from in waiting_workers_ids
    ]

    pipe = connection.pipeline()
    temp_union = 'temp:%s:%s' % (datetime.now().isoformat().split('T')[0], str(uuid.uuid4()))
    pipe.sunionstore(temp_union, *total_jobs_keys)

    temp_diff = 'temp:%s:%s' % (datetime.now().isoformat().split('T')[0], str(uuid.uuid4()))
    pipe.sdiffstore(temp_diff, temp_union, *done_jobs_keys)
    pipe.delete(temp_diff)
    pipe.delete(temp_union)
    execute_result = pipe.execute()
    diff_count = execute_result[1]
    done_signature = hashlib.sha1(workflow_id+"_"+workflow_instance_id+"_".join([str(x) for x in execute_result])).hexdigest()

    if  diff_count == 0:
        return (True, done_signature)
    return (False, done_signature)

def get_waiting_queue_name(workflow_instance_id, worker_id, wait_jobs_from):
    wait_jobs_from_text = "_".join(sorted(list(set(wait_jobs_from))))
    return "wait_jobs:%s_%s_%s" % (
        workflow_instance_id,
        worker_id,
        wait_jobs_from_text
    )

def process(specific_info, data, *args):
    inputs = poliglo.inputs.get_inputs(data, specific_info)
    connection = args[0].get('connection')

    waiting_queue_name = get_waiting_queue_name(
        data['workflow_instance']['id'], data['workflow_instance']['worker_id'], inputs['wait_jobs_from']
    )
    connection.zadd(waiting_queue_name, time(), poliglo.utils.to_json(data))
    return []

def get_waiting_workers(worker_workflows):
    all_waiting_workers = []
    workflows_workers_waiting = {}
    for workflow_id, workflow_values in worker_workflows.iteritems():
        if not workflows_workers_waiting.get(workflow_id):
            workflows_workers_waiting[workflow_id] = {}
        for worker_id, worker_values in workflow_values.iteritems():
            if not workflows_workers_waiting[workflow_id].get(worker_id):
                workflows_workers_waiting[workflow_id][worker_id] = [worker_id,]
            for worker_id2 in worker_values.get('default_inputs', {}).get('wait_jobs_from', []):
                workflows_workers_waiting[workflow_id][worker_id].append(worker_id2)
                all_waiting_workers.append(worker_id2)
    return workflows_workers_waiting, list(set(all_waiting_workers))

def wait_is_done(connection, worker_workflows, workflow_id, workflow_instance_id, workflow_instance_name, worker_id, waiting_workers_ids):
    waiting_queue_name = get_waiting_queue_name(
        workflow_instance_id, worker_id, waiting_workers_ids
    )
    worker = worker_workflows.get(workflow_id, {}).get(worker_id, {})
    for i, output_worker_id in enumerate(worker.get('next_workers', [])):
        output_worker_type = worker.get('__next_workers_types', [])[i]
        data = {'__read_from_queue': waiting_queue_name}
        poliglo.start.start_workflow_instance(
            connection, workflow_id, output_worker_type,
            output_worker_id, workflow_instance_name, data
        )

def main():
    meta_worker = os.path.splitext(os.path.basename(__file__))[0]
    worker_workflows, connection = poliglo.preparation.prepare_worker(
        os.environ['POLIGLO_SERVER_URL'], meta_worker
    )
    workflow_waiting_workers, all_waiting_workers = get_waiting_workers(worker_workflows)
    # TODO: Move to redis
    already_done_signatures = []
    found_finalized = False
    found_wait = False
    timeout_wait = 1
    timeout_finalized = 1
    while True:
        if not found_wait:
            review_instances = {}
            queue_message = connection.brpop(
                [poliglo.variables.REDIS_KEY_QUEUE_FINALIZED,], timeout_finalized
            )


            if queue_message is not None:
                queue_message_llen = connection.llen(
                    poliglo.variables.REDIS_KEY_QUEUE_FINALIZED
                )
                while True:
                    if queue_message:
                        finalized_data = json.loads(queue_message[1])
                        workflow_instance_id = finalized_data['workflow_instance_id']
                        if not review_instances.get(workflow_instance_id):
                            review_instances[workflow_instance_id] = {
                                'workflow_id': finalized_data['workflow'],
                                'workflow_instance_name': finalized_data['workflow_instance_name']
                            }
                        queue_message = None
                    if queue_message_llen > 2:
                        queue_message = [
                            poliglo.variables.REDIS_KEY_QUEUE_FINALIZED,
                            connection.rpop(poliglo.variables.REDIS_KEY_QUEUE_FINALIZED)
                        ]
                        queue_message_llen -= 1
                    else:
                        queue_message_llen = connection.llen(
                            poliglo.variables.REDIS_KEY_QUEUE_FINALIZED
                        )
                        if queue_message_llen <= 2:
                            break

                found_finalized = True
                if finalized_data['worker_id'] not in all_waiting_workers:
                    queue_message = None
                    continue
                for workflow_instance_id, review_instance_data in review_instances.iteritems():
                    workflow_id = review_instance_data['workflow_id']
                    workflow_instance_name = review_instance_data['workflow_instance_name']
                    for worker_id, waiting_workers_ids in workflow_waiting_workers[workflow_id].iteritems():
                        status_done, done_signature = check_if_waiting_is_done(
                            connection, workflow_id, workflow_instance_id, waiting_workers_ids
                        )
                        if status_done:
                            if done_signature not in already_done_signatures:
                                already_done_signatures.append(done_signature)
                                wait_is_done(
                                    connection, worker_workflows, workflow_id, workflow_instance_id,
                                    workflow_instance_name, worker_id, waiting_workers_ids
                                )
            else:
                found_finalized = False
        if not found_finalized:
            queue_message = connection.brpop([poliglo.variables.REDIS_KEY_QUEUE % meta_worker,], timeout_wait)
            if queue_message is not None:
                poliglo.runner.default_main_inside(
                    connection, worker_workflows, queue_message, process, {'connection': connection}
                )
                found_wait = True
            else:
                found_wait = False
        queue_message = None


if __name__ == '__main__':
    main()
