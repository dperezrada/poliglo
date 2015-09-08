Poliglo
=======

WARNING: As this is likely to change a lot, is not recommended for been use in production yet.

## Why poliglo?
Coming soon

## Install Requirements
 * Redis
 * Python

## Install
### Poliglo backend
    python backend/setup.py develop

### Poliglo Monitor
    cd monitor
    npm install -d
    bower install -d
    cd ..


## Run the example
### Poliglo backend
    CONFIG_PATH=./examples/numbers/config.json \
        WORKFLOWS_PATH=./examples/numbers/workflows \
        python backend/poliglo_server/__init__.py
### Poliglo monitor
    cd monitor && grunt serve

### Run the workers
    POLIGLO_SERVER_URL=localhost:9015 \
        WORKERS_PATHS=./examples/numbers/workers./deployment/scripts/ \
        SUPERVISOR_LOG_PATH="/tmp/poliglo_supervisor_logs" \
        start_workers.sh

If there is any problem checkout the logs in $SUPERVISOR_LOG_PATH

### Start a workflow instance
    python examples/start_a_workflow_instance.py

And take a look to the monitor to see it running.
If there is any error, press over the error column number. See the error, try to fix it, restart the server and the workers, and press the retry button.

If its done cat the file to see the result:
cat /tmp/poliglo_example_numbers.txt

Did you notice that in the file there was less numbers than the initials once. Thats because the find_even worker is filtering the numbers that are not even.






