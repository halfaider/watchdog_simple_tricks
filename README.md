watchdog_simple_tricks
======================

[watchdog](https://github.com/gorakhargosh/watchdog)을 이용해서 파일 시스템 이벤트를 모니터링하는 python 스크립트

폴더 구조
--------
```
watchdog_simple_tricks
├── bin
│   └── watcher.sh
├── conduits.py
├── __init__.py
├── instance
│   ├── my_log_config.yaml
│   ├── my_tricks.yaml
│   └── my_watcher.sh
├── log_config.yaml
├── README.md
├── simple_tricks.py
├── tricks.yaml
├── utils.py
└── watcher.py
```

설치
----

원하는 폴더에서 이 저장소를 `clone`하세요.

```
$ git clone https://github.com/halfaider/watchdog_simple_tricks.git
```

`watchdog_simple_tricks` 경로로 이동한 후 `bin/watcher.sh`을 실행해서 설정 파일을 `instance` 폴더에 복사하세요.

```
$ cd watchdog_simple_tricks
$ ./bin/watcher.sh copy
```

혹은 직접 `instance`폴더에 `log_config.yaml` `bin/watcher.sh` `tricks.yaml` 파일을 복사하세요.

```
$ cp tricks.yaml instance/my_tricks.yaml
$ cp log_config.yaml instance/my_log_config.yaml
$ cp bin/watcher.sh instance/my_watcher.sh
$ chmox +x instance/my_watcher.sh
```

설정
----

### my_watcher.sh

`my_watcher.sh`의 아래 값을 본인의 환경에 맞게 수정해 주세요.

```
WATCHER_CMD="python3 /나의/경로/watchdog_simple_tricks/watcher.py"
TRICKS="/나의/경로/watchdog_simple_tricks/instance/my_tricks.yaml"
LOG_CONFIG_FILE="/나의/경로/watchdog_simple_tricks/instance/my_logging.yaml"
DAEMON=true
MAX_WAIT_COUNT=60
```

### my_tricks.yaml

감시할 경로를 설정해 주세요.

```
tricks:
  dirs:
    - /감시할/경로
    - /감시할/경로
```

rclone과 flaskfarm 설정을 해주세요.

```
conduits:
  - name: 'my_rclone_refresh'
    rc_url: 'http://10.0.0.2:5275'
    rc_user: ''
    rc_pass: ''
    vfs: 'gds:'
    mappings: '/mnt/gds-metadata:'
  - name: 'my_plex_mate_scan'
    ff_url: 'http://flaskfarm:9999'
    ff_apikey: '1234567890'
    mappings: '/mnt/gds-metadata:/mnt/gds'
```

실행
----

`my_watcher.sh`에서 `daemon`을 `true`로 설정한 경우 `nohup`을 통해 백그라운드에서 실행됩니다.

```
$ instance/my_watcher.sh
```

중지할 경우 `stop`을 입력하세요.

```
$ instance/my_watcher.sh stop
```

실행중 상태 확인은 `status`입니다.

```
$ instance/my_watcher.sh status
```

재시작은 `restart` 입니다.

```
$ instance/my_watcher.sh restart
```
