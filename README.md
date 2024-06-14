watchdog_simple_tricks
======================

[watchdog](https://github.com/gorakhargosh/watchdog)을 이용해서 파일 시스템 이벤트를 모니터링하는 python 스크립트

폴더 구조
--------
```
watchdog_simple_tricks
├── files
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

```bash
$ git clone https://github.com/halfaider/watchdog_simple_tricks.git
```

`watchdog_simple_tricks` 경로로 이동한 후 `watcher.sh`을 실행해서 `example` 파일들을 `instance` 폴더에 복사하세요.

```bash
$ cd watchdog_simple_tricks
$ ./files/watcher.sh copy
```

실행
----

파이썬으로 직접 실행
```bash
$ python3 watcher.py tricks instance/tricks.yaml --log-config=instance/log_config.yaml
```
스크립트로 실행. `watcher.sh`에서 `DAEMON`을 `true`로 설정한 경우 `nohup`을 통해 백그라운드에서 실행됩니다.
```bash
$ ./instance/watcher.sh
```
중지할 경우 `stop`을 입력하세요.
```bash
$ ./instance/watcher.sh stop
```
실행중 상태 확인은 `status`입니다.
```bash
$ ./instance/watcher.sh status
```
재시작은 `restart` 입니다.
```bash
$ ./instance/watcher.sh restart
```


## watcher.sh

`instance/watcher.sh`의 아래 값을 본인의 환경에 맞게 수정해 주세요.

```bash
BASE=$(dirname -- "${0}")
WATCHER_CMD="python3 ${BASE}/../watcher.py"
LOG_CONFIG_FILE="${BASE}/log_config.yaml"
TRICKS="${BASE}/tricks.yaml"
DAEMON=false
TERMINATION_TIME_OUT=30
```

`tricks.yaml` 파일이 여러개 인 경우는 아래처럼 배열로 지정해 주세요.
```bash
TRICKS=(
  "/path/my_tricks1.yaml"
  "/path/my_tricks2.yaml"
  "/path/my_tricks3.yaml"
)
```

## tricks.yaml

### observer
명시하지 않으면 플랫폼에 따라 자동으로 선택됩니다.

`polling`, `kqueue`, `winapi`, `fsevents`, `inotify`
```yaml
observer: polling
```
### timeout

옵저버가 파일 이벤트를 조사하는 간격(초)
```yaml
observer: polling
timeout: 60
```

### python_path

`observer`, `trick`, `conduit` 클래스가 위치한 경로를 입력합니다. 추가로 해당 경로의 파이썬 모듈을 불러옵니다. 세미콜론(;)으로 구분

이 저장소를 `/data/commands/watchdog_simple_tricks` 경로에 `clone` 했다면 아래처럼 입력합니다.
```yaml
observer: polling
timeout: 60
python_path: '/data/commands/watchdog_simple_tricks;/data/commands/watchdog_simple_tricks/instance'
```

### tricks

사용할 `trick` 클래스를 파이썬 주소로 명시합니다.

`/data/commands/watchdog_simple_tricks/tricks.py`의 `SimpleTrick` 클래스를 사용한다면 아래처럼 입력합니다.
```yaml
observer: polling
timeout: 60
python_path: '/data/commands/watchdog_simple_tricks;/data/commands/watchdog_simple_tricks/instance'
tricks:
  - tricks.SimpleTrick:
```
추가로 `/data/commands/watchdog_simple_tricks/instance/tricks.py`의 `MyTrick` 클래스를 사용한다면 아래처럼 입력합니다.

```yaml
observer: polling
timeout: 60
python_path: '/data/commands/watchdog_simple_tricks;/data/commands/watchdog_simple_tricks/instance'
tricks:
  - tricks.SimpleTrick:
  - instance.tricks.MyTrick:
```

감시할 경로를 설정해 주세요.

```yaml
observer: polling
timeout: 60
python_path: '/data/commands/watchdog_simple_tricks;/data/commands/watchdog_simple_tricks/instance'
tricks:
  - tricks.SimpleTrick:
      dirs:
        - '/data/commands/watchdog_simple_tricks/instance'
  - instance.tricks.MyTrick:
      dirs:
        - '/path/to/be/observed'
```
- `patterns`: 일치하는 경로만 이벤트를 알립니다. (pathlib.PurePath.match()로 판단)
- `ignore_patterns`: 일치하는 경로는 무시합니다. (pathlib.PurePath.match()로 판단)
- `ignore_directories`: 폴더의 변화도 포함할지 결정합니다. (true | false)
- `case_sensitive`: 대소문자 구분 여부를 결정합니다. (true | false)
- `recursive`: 하위 폴더까지 감시할지 결정합니다. (true | false)
- `event_interval`: 다수의 이벤트가 한번에 발생될 경우 이벤트 처리 간격입니다. 단위: 초

```yaml
observer: polling
timeout: 60
python_path: '/data/commands/watchdog_simple_tricks;/data/commands/watchdog_simple_tricks/instance'
tricks:
  - tricks.SimpleTrick:
      dirs:
        - '/data/commands/watchdog_simple_tricks/instance'
      patterns: ['*']
      ignore_patterns:
        - '*.json'
        - '*.yml'
      ignore_directories: false
      case_sensitive: true
      recursive: true
      event_interval: 2
  - instance.tricks.MyTrick:
      dirs:
        - '/path/to/be/observed'
```

### conduit
`conduit`은 파일 이벤트 발생시 특정 서비스에 해당 내용을 전달하는 역할을 합니다. 기본적으로 `../watchdog_simple_tricks/conduits.py`에는 다음의 기능을 하는 `conduit`이 정의되어 있어요.
  - `DummyConduit`: 단순 로그만 출력합니다.
  - `RcloneConduit`: Rrclone rc의 `vfs/refresh`를 요청합니다.
  - `PlexConduit`: plex 서버에 웹 스캔 요청을 합니다.
  - `PlexmateConduit`: plex_mate 플러그인에 스캔 요청을 합니다.
  - `GDSToolConduit`: gds_tool 플러그인에 변경사항 방송을 요청합니다.
  - `ShellCommandConduit`: 쉘 명령어를 실행합니다.
  - `DiscordConduit`: 디스코드 웹훅으로 변경 사항을 전송합니다.

추가적인 기능은 `instance` 폴더의 `conduits.py`에서 직접 구현할 수 있습니다.


`conduit`에서 기본적으로 사용하는 키워드는 아래와 같습니다. 지정된 `conduit` 클래스를 생성할 때 값이 인자로 전달됩니다. 기본값이 명시된 키워드는 생략시 기본값이 입력됩니다.

- `name`: 구분용 이름입니다.
- `class`: 사용할 `conduit` 클래스입니다.
- `priority`: 우선순위가 높을 수록 먼저 실행됩니다. (기본값: 0)
- `events`: 처리할 파일 이벤트 목록입니다. (기본값: `created`, `deleted`, `moved`, `modified`, `opened`, `closed`)
- `mappings`: 경로 변경 규칙 (변경대상:변경값) (기본값: None)

```yaml
observer: polling
timeout: 60
python_path: '/data/commands/watchdog_simple_tricks;/data/commands/watchdog_simple_tricks/instance'
tricks:
  - tricks.SimpleTrick:
      dirs:
        - '/data/commands/watchdog_simple_tricks/instance'
      patterns: ['*']
      ignore_patterns:
        - '*.json'
        - '*.yml'
      ignore_directories: false
      case_sensitive: true
      recursive: true
      event_interval: 2
      conduits:
        - name: 'rclone vfs/refresh'
          class: 'conduits.RcloneConduit'
          priority: 50
          events:
            - 'created'
          mappings:
            - '/mnt/gds-metadata:'
  - instance.tricks.MyTrick:
      dirs:
        - '/path/to/be/observed'
```
`name`, `class`, `priority`, `events`, `mappings` 외의 값은 각 `conduit` 클래스의 설정에 따라 다릅니다. `RcloneConduit`은 추가로 아래의 값을 입력 받습니다.
- `rc_url`: rc 주소
- `rc_user`: rc 사용자명
- `rc_pass`: rc 비밀번호
- `vfs`: 대상 리모트

```yaml
observer: polling
timeout: 60
python_path: '/data/commands/watchdog_simple_tricks;/data/commands/watchdog_simple_tricks/instance'
tricks:
  - tricks.SimpleTrick:
      dirs:
        - '/data/commands/watchdog_simple_tricks/instance'
      patterns: ['*']
      ignore_patterns:
        - '*.json'
        - '*.yml'
      ignore_directories: false
      case_sensitive: true
      recursive: true
      event_interval: 2
      conduits:
        - name: 'rclone vfs/refresh'
          class: 'conduits.RcloneConduit'
          priority: 50
          events:
            - 'created'
          mappings:
            - '/mnt/gds-metadata:'
          rc_url: 'http://10.0.0.2:5275'
          rc_user: ''
          rc_pass: ''
          vfs: 'gds:'
  - instance.tricks.MyTrick:
      dirs:
        - '/path/to/be/observed'
```
`PlexmateConduit`은 추가로 아래의 값을 입력받습니다.

- `ff_url`: flaskfarm 주소
- `ff_apikey`: flaskfarm API 키

`PlexConduit`, `GDSToolConduit`은 추가로 아래의 값을 입력받습니다.

- `plex_url`: 플렉스 주소
- `plex_token`: 플렉스 토큰값

`ShellCommandConduit`은 추가로 아래의 값을 입력받습니다.

- `wait_for_process`: 프로세스가 끝날 때까지 대기
- `drop_during_process`: 이전 이벤트로 실행된 프로세스가 아직 실행중이면 건너뛰기
- `command`: 실행할 명령어. event_type, file(directory), src_path, dest_path 순으로 인자를 전달

`DiscordConduit`은 추가로 아래의 값을 입력받습니다.

- `webhook_id`: 웹훅 아이디 (웹훅 주소중 숫자 부분)
- `webhook_token`: 웹훅 토큰 (숫자 부분 이후)

```yaml
observer: polling
timeout: 60
python_path: '/data/commands/watchdog_simple_tricks;/data/commands/watchdog_simple_tricks/instance'
tricks:
  - tricks.SimpleTrick:
      dirs:
        - './instance'
      patterns: ['*']
      ignore_patterns:
        - '*.json'
        - '*.yml'
      ignore_directories: false
      case_sensitive: true
      recursive: true
      event_interval: 2
      conduits:
        - name: 'rclone vfs/refresh'
          class: 'conduits.RcloneConduit'
          priority: 50
          events:
            - 'created'
            - 'moved'
            - 'deleted'
          mappings:
            - '/mnt/gds-metadata:'
          rc_url: 'http://10.0.0.2:5275'
          rc_user: ''
          rc_pass: ''
          vfs: 'gds:'
        - name: 'plex_mate scan'
          class: 'conduits.PlexmateConduit'
          priority: 40
          events:
            - 'created'
            - 'moved'
          mappings:
            - '/mnt/gds-metadata:/mnt/gds'
          ff_url: 'http://flaskfarm:9999'
          ff_apikey: '1234567890'
        - name: 'plex web scan'
          class: 'conduits.PlexConduit'
          priority: 40
          events:
            - 'created'
            - 'moved'
          mappings:
            - '/mnt/gds-metadata:/mnt/gds'
          plex_url: 'http://plex:32400'
          plex_token: '12345678901234567890'
        - name: 'shell command'
          class: 'conduits.ShellCommandConduit'
          events: ['modified']
          mappings:
            - '/mnt/gds-metadata:/mnt/gds'
          wait_for_process: true
          drop_during_process: false
          command: './instance/test.sh'
        - name: 'discord'
          class: 'conduits.DiscordConduit'
          events: ['created', 'moved', 'deleted']
          webhook_id: '1234567890123456789'
          webhook_token: 'abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmnopqrstuvwxyz123456'
          mappings:
            - '/mnt/gds-metadata:'
  - instance.tricks.MyTrick:
      dirs:
        - '/path/to/be/observed'
```
### 사용자 정의

기본 클래스 외에 본인이 직접 기능을 추가해서 사용할 경우 `python_path`에 본인의 클래스 경로를 추가하세요.
```yaml
observer:
timeout: 2
python_path: '/data/commands/watchdog_simple_tricks;/data/commands/watchdog_simple_tricks/instance'
tricks:
  - instance.tricks.MyTrick:
      dirs:
        - './instance'
      conduits:
        - name: 'My conduit'
          class: 'instance.conduits.MyConduit'
          priority: 100
          events: ['created', 'deleted', 'moved', 'modified', 'opened', 'closed']
          mappings: ['/mnt/gds-metadata:']
          my_setting: 'Bow Wow'
```

### 로그 파일

로그 파일은 `/instance/log_config.yaml`에서 설정해 주세요.
```yaml
...
handlers:
  default:
    level: 'NOTSET'
    formatter: 'redacted'
    class: 'logging.StreamHandler'
    stream: 'ext://sys.stdout'
  default_file_handler: # 이 핸들러의 이름은 고정
    level: 'NOTSET'
    formatter: 'redacted'
    class: 'logging.handlers.RotatingFileHandler'
    filename: '/path/to/log_file.log' # 로그를 파일에 저장하려면 파일 경로 입력
    mode: 'a'
    maxBytes: 5242880
    backupCount: 5
...
```

### 설정 예시

아래의 경로를 사용중이라고 가정할 경우...
```
읽기 전용 GDS 마운트 경로: /mnt/gds-metadata/GDRIVE
실제 PLEX에서 사용중인 GDS 경로: /mnt/gds/GDRIVE
이 패키지가 설치된 경로: /data/commands/watchdog_simple_tricks
```

#### `watcher.sh`

경로: `/data/commands/watchdog_simple_tricks/instance/watcher.sh`

`watcher.sh`파일은 `instance` 폴더에 넣을 필요 없이 아무곳에나 저장해도 됩니다. 소스의 `watcher.sh`와 분리하기 위해서 `instance`라는 임의 폴더에 넣은 거예요.

```bash
BASE="/data/commands/watchdog_simple_tricks"
WATCHER_CMD="python3 ${BASE}/watcher.py"
LOG_CONFIG_FILE="${BASE}/instance/log_config.yaml"
TRICKS="${BASE}/instance/tricks.yaml"
DAEMON=false # false로 먼저 실행해서 에러 로그가 있나 확인 후 true로 변경하세요.
TERMINATION_TIME_OUT=30
```

#### `tricks.yaml`

경로: `/data/commands/watchdog_simple_tricks/instance/tricks.yaml`

마찬가지로 `instance`라는 임의 폴더에 넣은 거예요.

```yaml
observer: polling # GDS는 polling, 복사요청하는 개인 구글 드라이브도 polling
timeout: 60
python_path: '/data/src/watchdog_simple_tricks/;/data/src/watchdog_simple_tricks/instance'
tricks:
  - tricks.SimpleTrick:
      patterns: # 생략 가능
      ignore_patterns: # 생략 가능
      ignore_directories: # 생략 가능 (기본값: false)
      case_sensitive: # 생략 가능 (기본값: false)
      recursive: # 생략 가능 (기본값: false)
      dirs: # 감시하려는 폴더
        - '/mnt/gds-metadata/GDRIVE/VIDEO/방송중/외국'
      event_interval: #생략 가능 (기본값: 0)
      conduits:
        - name: 'plex_mate scan'
          class: 'conduits.PlexmateConduit'
          events: ['created', 'moved']
          priority: 40
          ff_url: 'http://flaskfarm:9999'
          ff_apikey: 'abcdefghig'
          mappings:
            - '/mnt/gds-metadata/GDRIVE:/mnt/gds/GDRIVE' # plex_mate는 /mnt/gds/GDRIVE 경로를 사용중이라서 변환
```

이렇게 설정하면 `created`나 `moved`일 경우 `plex_mate`에 스캔 요청이 추가됩니다. `vfs/refresh`는 `plex_mate`에서 설정할 수 있으니 그걸 이용하면 돼요. 아니면 여기에 `RcloneConduit`을 넣어서 `vfs/refresh`를 해주면 됩니다.
```yaml
observer: polling # GDS는 polling, 복사요청하는 개인 구글 드라이브도 polling
timeout: 60
python_path: '/data/src/watchdog_simple_tricks/;/data/src/watchdog_simple_tricks/instance'
tricks:
  - tricks.SimpleTrick:
      patterns: # 생략 가능
      ignore_patterns: # 생략 가능
      ignore_directories: # 생략 가능 (기본값: false)
      case_sensitive: # 생략 가능 (기본값: false)
      recursive: # 생략 가능 (기본값: false)
      dirs: # 감시하려는 폴더
        - '/mnt/gds-metadata/GDRIVE/VIDEO/방송중/외국'
      event_interval: #생략 가능 (기본값: 0)
      conduits:
        - name: 'plex_mate scan'
          class: 'conduits.PlexmateConduit'
          events: ['created', 'moved']
          priority: 40
          ff_url: 'http://flaskfarm:9999'
          ff_apikey: 'abcdefghig'
          mappings:
            - '/mnt/gds-metadata/GDRIVE:/mnt/gds/GDRIVE' # plex_mate는 /mnt/gds/GDRIVE 경로를 사용중이라서 변환
        - name: 'rclone vfs/refresh'
          class: 'conduits.RcloneConduit'
          events: ['created', 'moved']
          priority: 50 # plex_mate scan보다 우선 실행되도록
          rc_url: 'http://172.17.0.1:5275'
          rc_user: ''
          rc_pass: ''
          vfs: 'gds:' # 실제 사용중인 GDS 리모트 이름
          mappings:
            - '/mnt/gds-metadata:' # 리모트 경로에는 /mnt/gds-metadat가 없으니까 삭제
```

이렇게 설정하면 `priority`가 더 높은 `RcloneConduit`이 먼저 실행되어서 `vfs/refresh`를 한 다음에 `PlexmateConduit`이 실행되어서 스캔 요청을 하게 됩니다.

#### gds_tool 방송용

```yaml
observer: polling # GDS는 polling, 복사요청하는 개인 구글 드라이브도 polling
timeout: 60
python_path: '/data/src/watchdog_simple_tricks/;/data/src/watchdog_simple_tricks/instance'
tricks:
  - tricks.SimpleTrick:
      patterns: # 생략 가능
      ignore_patterns: # 생략 가능
      ignore_directories: # 생략 가능 (기본값: false)
      case_sensitive: # 생략 가능 (기본값: false)
      recursive: # 생략 가능 (기본값: false)
      dirs: # 감시하려는 폴더
        - '/mnt/gds-metadata/GDRIVE/VIDEO/방송중/일본 애니메이션'
        - '/mnt/gds-metadata/GDRIVE/VIDEO/방송중/외국'
      event_interval: #생략 가능 (기본값: 0)
      conduits:
        - name: 'gds_tool broadcast'
          class: 'conduits.GDSToolConduit'
          priority: 40
          ff_url: 'http://flaskfarm:9999'
          ff_apikey: 'abcdefghig'
          mappings:
            - '/mnt/gds-metadata/GDRIVE:/ROOT/GDRIVE' # 방송용은 /ROOT/GDRIVE 로 시작되어야 하므로...
```
