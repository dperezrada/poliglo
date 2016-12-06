#!/usr/bin/env python
# -*- coding: utf-8 -*-
from random import randint
from time import sleep

import poliglo

def process(specific_info, data, *args):
    inputs = poliglo.inputs.get_inputs(data, specific_info)

    numbers_range = inputs.get('numbers_range')
    how_many_to_create = inputs.get('how_many_to_create')

    for _ in range(1, how_many_to_create + 1):
        sleep(0.05)  # Sleep for visualization purpose
        yield {'number': randint(numbers_range[0], numbers_range[1])}
