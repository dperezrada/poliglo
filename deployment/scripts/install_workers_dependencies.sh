CURR_DIR="$(cd "$(dirname "$0")"; pwd)/"

IFS=$'\t'

OUT="$(mktemp /tmp/output.XXXXXXXXXX)"
WORKERS_PATHS=$WORKERS_PATHS python ${CURR_DIR}/find_dependencies.py > $OUT

while read EXTENSION WORKER_DEP; do
    if [[ "$EXTENSION" == "py" ]]; then
        ${PY_BIN_PATH}pip install $WORKER_DEP
    fi
    if [[ "$EXTENSION" == "js" ]]; then
        ${JS_BIN_PATH}npm install -g $WORKER_DEP
    fi
    if [[ "$EXTENSION" == "rb" ]]; then
        ${RB_BIN_PATH}gem install $WORKER_DEP
    fi
done < $OUT
rm $OUT
