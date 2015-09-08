#!/usr/bin/env python
# -*- coding: utf-8 -*-

from poliglo import default_main, get_inputs

def process(specific_info, data, *args):
    inputs = get_inputs(data, specific_info)
    numbers_file = inputs.get('numbers_filepath')
    with open(numbers_file, 'a') as _file:
        _file.write("%s\n" % inputs.get('number'))
    return [inputs,]

if __name__ == '__main__':
    from os import environ as env, path
    default_main(env.get('POLIGLO_SERVER_URL'), path.splitext(path.basename(__file__))[0], process)
