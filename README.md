Poliglo
=======
[![Build Status](https://travis-ci.org/dperezrada/poliglo.svg?branch=master)](https://travis-ci.org/dperezrada/poliglo)


WARNING: As this is likely to change a lot in the short term, it's not recommended for production yet.

## Why poliglo?
Today there are a lot of programming languages, and some of them are pretty good for certain tasks.
But generally, using them together is painful, specially if you want them to talk to each other.
## What is Poliglo?
It's a simple way to create a small piece of code (worker) in some programming language, and connect it to another worker, maybe in another language. So you could do something like this:

    worker(js) -> worker(py) -> worker(java)

## Features
+ Easily connect programming languages
+ Web interface to monitor what is happening
+ Supported programming languages:
    * [Python](https://github.com/dperezrada/poliglo-py "Poliglo-py")
    * [Node.js](https://github.com/dperezrada/poliglo-js "Poliglo-js")
    * More coming soon

## Limitations
+ Not safe fail of workers, may lose some jobs if a worker dies.
    * The solution is designed, but haven't been implemented yet

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

This workflow example uses 3 workers:
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
        WORKERS_PATHS=./examples/numbers/workers/ \
        SUPERVISOR_LOG_PATH="/tmp/poliglo_supervisor_logs" \
        deployment/scripts/start_workers.sh

If there is any problem check out the logs in $SUPERVISOR_LOG_PATH

#### Start a workflow instance
    python examples/start_a_workflow_instance.py

And take a look at the monitor to see it running (http://localhost:9000).
If there is any error, press over the error column number. See the error, try to fix it, restart the server and the workers and press the retry button.

When it's done, cat the file to see the result:
cat /tmp/poliglo_example_numbers.txt

Did you notice that in the file there were less numbers than the initial ones? That's because the find_even worker is filtering the numbers that are not even.

### Numbers (using Docker)

Start the containers (server, monitor & worker):

    docker-compose up

#### Start a workflow instance (execute in HOST machine)

    python examples/start_a_workflow_instance.py

#### Go to url

    http://0.0.0.0:9000

#### Screenshot

    ![Example screenshot](example_screenshot.png?raw=true)
