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
        total += 1
    return [{'total': total}]
