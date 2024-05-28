#!/usr/bin/env bash

# 이 파일을 instnace 폴더(업데이트 제외 폴더)나 다른 폴더에 복사해서 사용
# 실행: ./watcher.sh
# 정지: .watcher.sh stop
WATCHER_CMD="python3 /나의/경로/watchdog_simple_tricks/watcher.py"
TRICKS="/나의/경로/watchdog_simple_tricks/instance/my_tricks.yaml"
LOG_LEVEL="-vv" # default: warning | error(-q) | info(-v) | debug(-vv)
LOG_FILE="/나의/경로/watcher.log"
LOG_CONFIG_FILE="/나의/경로/watchdog_simple_tricks/instance/my_log_config.yaml"
MAX_RETRIES=60


get_pid() {
    echo $(ps -ef | grep "${WATCHER_CMD}" | grep -v grep | awk '{print $2}')
}

is_running() {
    pid=$(get_pid)
    [[ -z "${pid}" ]] && return 1 || return 0
}


start() {
    stop
    echo "Starting ${WATCHER_CMD}..."
    command=(nohup ${WATCHER_CMD} tricks "${TRICKS}" ${LOG_LEVEL})
    [[ ! -z "${LOG_FILE}" ]] && command+=(--log-file="${LOG_FILE}")
    [[ ! -z "${LOG_CONFIG_FILE}" ]] && command+=(--log-config="${LOG_CONFIG_FILE}")
    echo "command: ${command[@]}"
    ${command[@]} 2>&1 &
}


stop() {
    echo "Stopping ${WATCHER_CMD}..."
    pid=$(get_pid)
    if is_running; then
        kill -15 ${pid}
    fi
    counter=0
    while is_running; do
        if [[ ${counter} -ge ${MAX_RETRIES} ]]; then
            echo "Could not terminate this process..."
            echo "Send signal 9..."
            kill -9 ${pid}
            exit 1
        fi
        counter=$((${counter} + 1))
        sleep 5
    done
}


copy() {
    echo ${PWD}
    instance="${PWD}/instance"
    [[ -d "${instance}" ]] || mkdir "${instance}"

    tricks_file="${instance}/my_tricks.yaml"
    tricks_file_source="${PWD}/tricks.yaml"
    log_config_file="${instance}/my_log_config.yaml"
    log_config_file_source="${PWD}/log_config.yaml"
    watcher_file="${instance}/my_watcher.sh"
    watcher_file_source="${PWD}/bin/watcher.sh"

    if [[ ! -e "${watcher_file}" ]] && [[ -e "${watcher_file_source}" ]]; then
        cp "${watcher_file_source}" "${watcher_file}"
        chmod +x "${watcher_file}"
    fi
    if [[ ! -e "${log_config_file}" ]] && [[ -e "${log_config_file_source}" ]]; then
        cp "${log_config_file_source}" "${log_config_file}"
    fi
    if [[ ! -e "${tricks_file}" ]] && [[ -e "${tricks_file_source}" ]]; then
        cp "${tricks_file_source}" "${tricks_file}"
    fi
}

case "${1}" in
    "stop")
        stop
        ;;
    "status")
        result="$(pidof -o %PPID -x ${WATCHER_CMD})"
        if [[ -z "${result}" ]]; then
            echo "Dead"
        else
            echo "Running: ${result}"
        fi
        ;;
    "copy")
        copy
        ;;
    *)
        start
        ;;
esac
