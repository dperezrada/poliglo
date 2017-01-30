import poliglo
import os

POLIGLO_SERVER_URL = os.environ.get('POLIGLO_SERVER_URL')
META_WORKER = 'filter'

def process(specific_info, data, *args):
    inputs = poliglo.inputs.get_inputs(data, specific_info)
    min_value = inputs.get("min")
    if inputs['number'] < min_value:
        return [inputs, ]
    return []
