import time
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
