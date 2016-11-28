#!/usr/bin/env bash

parse_workers_json(){
    curl -s "$POLIGLO_SERVER_URL/meta_workers" | ${exec_paths_py} -c 'import json,sys;workers=json.load(sys.stdin);print " ".join(workers)'
}

parse_workers_config_json(){
    local worker="$1"
    curl -s "$POLIGLO_SERVER_URL/meta_workers/$worker/config" | ${exec_paths_py} -c "import json,sys;config=json.load(sys.stdin);print '${CONFIG_SEPARATOR}'.join([str(key)+'=\"'+str(value)+'\"' for key, value in config.iteritems()])"
}

EXCLUDE_WORKERS=
ONLY_WORKER=
HELP=

for i in "$@"
do
case $i in
    -e=*|--exclude=*)
    EXCLUDE_WORKERS="${i#*=}"
    EXCLUDE_WORKERS=`echo $EXCLUDE_WORKERS|tr "," "\n"`
    shift # past argument=value
    ;;
    -w=*|--worker=*)
    ONLY_WORKER="${i#*=}"
    shift # past argument=value
    ;;
    -h|--help)
    HELP=1
    shift # past argument with no value
    ;;
    *)
            # unknown option
    ;;
esac
done

if [[ $HELP == 1 ]]; then
    echo "Usage: $0 [options]";
    echo "";
    echo "[-e=|--exclude=] = Exclude a worker from start (separete them by comma)";
    echo "[-w=|--worker=] = Start one worker";
    echo "[-h|--help] = Show help";
    echo "";
    exit 0;
fi

if [[ -z "${POLIGLO_SERVER_URL}" ]]; then
    echo "Global variable POLIGLO_SERVER_URL must be defined"
    exit 1;
fi

VALID_EXTENSIONS="(js|py|rb)"

if [[ -z "$exec_paths_py" ]]; then
    # By default Python does not automatically flush output to STDOUT.
    # If you want 'print' statements to work, use unbuffered mode (python -u).
    exec_paths_py="python"
fi
if [[ -z "$exec_paths_js" ]]; then
    exec_paths_js="node"
fi
if [[ -z "$exec_paths_rb" ]]; then
    exec_paths_rb="ruby"
fi

ALL_POSIBLE_WORKERS=""

for worker_path in ${WORKERS_PATHS//:/ }; do
    abs_worker_path=$(cd $(dirname "$worker_path") && pwd -P)/$(basename "$worker_path");
    posible_workers=`find $abs_worker_path -type f|grep -E "$VALID_EXTENSIONS\$"`
    ALL_POSIBLE_WORKERS="${ALL_POSIBLE_WORKERS}\n${posible_workers}"
done
if [[ -n "$SUPERVISOR_FILE" ]]; then
    supervisor_file="$SUPERVISOR_FILE"
else
    supervisor_file=`mktemp /tmp/supervisor.XXXXXXXXXX`
fi

if [[ -z "$SUPERVISOR_LOG_PATH" ]]; then
    SUPERVISOR_LOG_PATH="/tmp/poliglo_supervisor_logs"
    `mkdir -p $SUPERVISOR_LOG_PATH`
    echo "SUPERVISOR_LOG_PATH set to: ${supervisor_file}"
fi

if [ ! -d "$SUPERVISOR_LOG_PATH" ]; then
    `mkdir -p $SUPERVISOR_LOG_PATH`
fi

echo "[unix_http_server]
file=/tmp/supervisor.sock
chmod=0700
[supervisord]
logfile = ${SUPERVISOR_LOG_PATH}/supervisord.log
logfile_maxbytes = 50MB
logfile_backups=10
loglevel = info
pidfile = /tmp/supervisord.pid
nodaemon = False
minfds = 1024
minprocs = 200
umask = 022
identifier = supervisor
directory = ${SUPERVISOR_LOG_PATH}
nocleanup = true
childlogdir = ${SUPERVISOR_LOG_PATH}

[supervisorctl]
serverurl = unix:///tmp/supervisor.sock

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

" > $supervisor_file
WORKERS=$(parse_workers_json)

for worker in $WORKERS; do
    IS_EXCLUDED=`echo "${EXCLUDE_WORKERS}"|grep "^${worker}$"`
    CONFIG_SEPARATOR=","
    if [[ $IS_EXCLUDED ]]; then
        continue
    fi
    if [[ $ONLY_WORKER ]]; then
        if [[ $ONLY_WORKER != $worker ]]; then
            continue
        else
            CONFIG_SEPARATOR=" "
        fi

    fi

    worker_path=`echo -e "${ALL_POSIBLE_WORKERS}" | grep "\/$worker\."|head -n 1`
    extension="${worker_path##*.}"
    exec_variable="exec_paths_$extension"
    exec_path=${!exec_variable}

    if [[ -z "${extension}" ]]; then
        echo "WARNING: Worker ${worker}.${VALID_EXTENSIONS} definition file not found, ignoring"
        continue
    fi

    worker_config=$(parse_workers_config_json $worker)
    if [[ $ONLY_WORKER ]]; then
        RUN_COMMAND="${worker_config} bash -c '${exec_path} ${worker_path}'"
    else
        user_text="";
        if [[ -n "$DEPLOY_USER" ]]; then
            user_text="user=${DEPLOY_USER}"
        fi
        if [[ "$DEPLOY_USER" == "test_user" ]]; then
            user_text="";
        fi
        echo "[program:${worker}]
command=${exec_path} ${worker_path}
environment=${worker_config}
${user_text}
" >> $supervisor_file
    fi
done

if [[ -n "$SUPERVISOR_FILE" ]]; then
    echo "${supervisor_file}"
else
    if [[ $ONLY_WORKER ]]; then
        eval "${RUN_COMMAND}"
    else
        supervisord -n -c "${supervisor_file}"
    fi
fi
