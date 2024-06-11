watchdog_simple_tricks
======================

[watchdog](https://github.com/gorakhargosh/watchdog)을 이용해서 파일 시스템 이벤트를 모니터링하는 python 스크립트

폴더 구조
--------
```
watchdog_simple_tricks
├── example
│   ├── conduits.py
│   ├── log_config.yaml
│   ├── tricks.py
│   ├── tricks.yaml
│   └── watcher.sh
├── instance
│   ├── __init__.py
│   ├── your_conduits.py
│   ├── your_log_config.yaml
│   ├── your_tricks.py
│   ├── your_tricks.yaml
│   └── your_watcher.sh
├── __init__.py
├── .gitignore
├── conduits.py
├── observers.py
├── README.md
├── tricks.py
├── utils.py
└── watcher.py
```

설치
----

원하는 폴더에서 이 저장소를 `clone`하세요.

```
$ git clone https://github.com/halfaider/watchdog_simple_tricks.git
```

`watchdog_simple_tricks` 경로로 이동한 후 `watcher.sh`을 실행해서 `example` 파일들을 `instance` 폴더에 복사하세요.

```
$ cd watchdog_simple_tricks
$ ./example/watcher.sh copy
```

설정
----

### watcher.sh

`instance/watcher.sh`의 아래 값을 본인의 환경에 맞게 수정해 주세요.

```
WATCHER_CMD="python3 /your/path/watchdog_simple_tricks/watcher.py"
LOG_CONFIG_FILE="/your/path/watchdog_simple_tricks/instance/log_config.yaml"
TRICKS="/your/path/watchdog_simple_tricks/instance/tricks.yaml"
DAEMON=true
TERMINATION_TIME_OUT=30
```

### tricks.yaml

감시할 경로를 설정해 주세요.

```
tricks:
  dirs:
    - /path/to/be/observed1
    - /path/to/be/observed2
```

원하는 `conduit`을 설정하세요.

```
conduits:
  - name: 'my_rclone_vfs_refresh'
    rc_url: 'http://10.0.0.2:5275'
    rc_user: ''
    rc_pass: ''
    vfs: 'gds:'
    mappings: '/mnt/gds-metadata:'
  - name: 'my_plex_web_scan'
    plex_url: 'http://plex:32400'
    plex_token: '12345678901234567890'
    mappings: '/mnt/gds-metadata:/mnt/gds'
```

실행
----

`watcher.sh`에서 `DAEMON`을 `true`로 설정한 경우 `nohup`을 통해 백그라운드에서 실행됩니다.

```
$ ./instance/my_watcher.sh
```

중지할 경우 `stop`을 입력하세요.

```
$ ./instance/my_watcher.sh stop
```

실행중 상태 확인은 `status`입니다.

```
$ ./instance/my_watcher.sh status
```

재시작은 `restart` 입니다.

```
$ ./instance/my_watcher.sh restart
```
