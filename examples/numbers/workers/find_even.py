#!/usr/bin/env python
# -*- coding: utf-8 -*-

from poliglo import default_main, get_inputs

def process(specific_info, data, *args):
    inputs = get_inputs(data, specific_info)

    if inputs.get('number') % 2 == 0:
        return [inputs,] #is even
    return [] #is odd

if __name__ == '__main__':
    from os import environ as env, path
    default_main(env.get('POLIGLO_SERVER_URL'), path.splitext(path.basename(__file__))[0], process)
