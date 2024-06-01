#!/usr/bin/env bash

# 이 파일을 instnace 폴더(업데이트 제외 폴더)나 다른 폴더에 복사해서 사용
# 실행: ./watcher.sh
# 정지: .watcher.sh stop
WATCHER_CMD="python3 /나의/경로/watchdog_simple_tricks/watcher.py"
LOG_CONFIG_FILE="/나의/경로/watchdog_simple_tricks/instance/log_config.yaml"
TRICKS="/나의/경로/watchdog_simple_tricks/instance/tricks.yaml"
#TRICKS=(
#    "/path/my_tricks1.yaml"
#    "/path/my_tricks2.yaml"
#    "/path/my_tricks3.yaml"
#)
DAEMON=false # true일 경우 nohup으로 실행
TERMINATION_TIME_OUT=30


get_pid() {
    echo $(ps -ef | grep "${WATCHER_CMD}" | grep -v grep | awk '{print $2}')
}


is_running() {
    pid=$(get_pid)
    [[ -z "${pid}" ]] && return 1 || return 0
}


start() {
    if is_running; then
        echo "Already running: $(get_pid)"
    else
        echo "Starting ${WATCHER_CMD}..."
        command=(${WATCHER_CMD} tricks "${TRICKS[@]}")
        [[ ! -z "${LOG_CONFIG_FILE}" ]] && command+=(--log-config="${LOG_CONFIG_FILE}")
        echo "command: ${command[@]}"
        if [[ ${DAEMON} == true ]]; then
            nohup ${command[@]} >/dev/null 2>&1 &
        else
            ${command[@]}
        fi
    fi
}


stop() {
    if is_running; then
        echo "Stopping ${WATCHER_CMD}..."
        kill -15 $(get_pid)
    fi
    counter=0
    while is_running; do
        if [[ ${counter} -ge ${TERMINATION_TIME_OUT} ]]; then
            echo "Could not terminate this process..."
            echo "Send signal 9..."
            kill -9 $(get_pid)
        fi
        counter=$((${counter} + 1))
        sleep 1
    done
}


copy() {
    conduits_file="conduits.py"
    log_config="log_config.yaml"
    tricks_file="tricks.py"
    tricks_yaml_file="tricks.yaml"
    watcher_file="watcher.sh"

    files=("${conduits_file}" "${log_config}" "${tricks_file}" "${tricks_yaml_file}" "${watcher_file}")

    echo "Current working directory: ${PWD}"
    sample="${PWD}/example"

    for file in ${files[@]}; do
        echo "example: ${sample}/${file}"
        [[ ! -e "${sample}/${file}" ]] && {
            echo "Not exists: ${file}"
            exit 1
        }
    done

    instance="${PWD}/instance"
    [[ -d "${instance}" ]] || mkdir "${instance}"
    [[ -e "${instance}/__init__.py" ]] || touch "${instance}/__init__.py"

    for file in ${files[@]}; do
        if [[ ! -e "${instance}/${file}" ]]; then
            cp --backup=numbered "${sample}/${file}" "${instance}/${file}"
        else
            echo "File exists: ${instance}/${file}"
        fi
    done
}


case "${1}" in
    stop)
        stop
        ;;
    status)
        pid=$(get_pid)
        if [[ -z "${pid}" ]]; then
            echo "Dead"
        else
            echo "Running: ${pid}"
        fi
        ;;
    copy)
        copy
        ;;
    restart)
        stop
        start
        ;;
    *)
        start
        ;;
esac
