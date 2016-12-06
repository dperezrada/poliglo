#!/usr/bin/env python
# -*- coding: utf-8 -*-

import poliglo

def process(specific_info, data, *args):
    inputs = poliglo.inputs.get_inputs(data, specific_info)
    numbers_file = inputs.get('numbers_filepath')
    with open(numbers_file, 'a') as _file:
        _file.write("%s\n" % inputs.get('number'))
    return [inputs]
