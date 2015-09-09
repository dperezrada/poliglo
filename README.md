Poliglo
=======
[![Build Status](https://travis-ci.org/dperezrada/poliglo.svg?branch=master)](https://travis-ci.org/dperezrada/poliglo)


WARNING: As this is likely to change a lot in the short term, is not recommended for production yet.

## Why poliglo?
Today there are a lot of programming languages, and some of them are pretty good for certain tasks.
But generally, use them together is painful, specially if you want they to talk one to another.
## What is Poliglo?
Is a simple way to create small piece of code (worker) in some programming language and connect it with another worker maybe in another language. So you could do something like this:

    worker(js) -> worker(py) -> worker(java)

## Features
+ Easily connect programming languages
+ Web interface to monitor what is happening

## Install Requirements
 * Redis
 * Python
 * npm (Node package manager)

## Install
    python backend/setup.py develop
    cd monitor
    npm install -d
    bower install -d
    cd ..


## Run the example
### Numbers
This example is located in
    examples/numbers

This workflow example user 3 workers:
+ create_random_number
+ find_even
+ write_numbers_to_file

#### Start the server
    CONFIG_PATH=./examples/numbers/config.json \
        WORKFLOWS_PATH=./examples/numbers/workflows \
        python backend/poliglo_server/__init__.py
#### Poliglo monitor
    cd monitor && grunt serve

#### Run the workers
    POLIGLO_SERVER_URL=localhost:9015 \
        WORKERS_PATHS=./examples/numbers/workers./deployment/scripts/ \
        SUPERVISOR_LOG_PATH="/tmp/poliglo_supervisor_logs" \
        start_workers.sh

If there is any problem checkout the logs in $SUPERVISOR_LOG_PATH

#### Start a workflow instance
    python examples/start_a_workflow_instance.py

And take a look to the monitor to see it running (http://localhost:9000).
If there is any error, press over the error column number. See the error, try to fix it, restart the server and the workers, and press the retry button.

If its done cat the file to see the result:
cat /tmp/poliglo_example_numbers.txt

Did you notice that in the file there was less numbers than the initials once. Thats because the find_even worker is filtering the numbers that are not even.






