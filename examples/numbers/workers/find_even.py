#!/usr/bin/env python
# -*- coding: utf-8 -*-

import poliglo

def process(specific_info, data, *args):
    inputs = poliglo.inputs.get_inputs(data, specific_info)

    if inputs.get('number') % 2 == 0:
        return [inputs]  # is even
    return []  # is odd
