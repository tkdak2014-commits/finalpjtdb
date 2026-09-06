# 지하주차장 시스템 모니터

## 11단계 완료 범위

Flask 기본 구조, SQLite 초기화, 인증·권한, 대시보드, AMR1·AMR2 상태, Nav2 점유 지도, 화재·누수·장애물 이벤트, 네 카메라 최신 영상, 차량 입출차 로그와 통합 이력 검색을 구현했다. 최근 두 로그는 사용자별로 표시 초기화할 수 있고 DB 이력은 유지한다. 실제 ROS 토픽과 costmap 동적 장애물은 후속 단계다.

`../day5/0_app.py`의 Flask 생성·경로 등록·템플릿 표시 방식을 기반으로 실행 파일과 페이지 경로를 분리했다. 기능 처리 위치에 한국어 주석을 작성한다.

## 구현 기록과 코드리뷰

- [단계별 구현 기록](docs/implementation-log.md): 구현 순서·설계 이유·함수 흐름·문제 해결·검증 결과
- [30분 코드리뷰 진행안](docs/code-review-30min.md): 시간 배분·설명 멘트·코드 탐색·시연·예상 질문
- [후속 작업 지침](AGENTS.md): 기능을 구현할 때마다 기록과 리뷰 자료를 갱신하는 기준

## 실행

```bash
cd /home/hun/finalproject/sysmon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app run create-admin
python run.py
```

브라우저에서 http://127.0.0.1:5000 에 접속한다. 종료는 터미널에서 Ctrl+C.

`create-admin`은 최초 계정 생성 때 실행한다. 관리자 아이디와 비밀번호를 직접 입력하고 비밀번호 확인을 마치면 DB에 계정이 생성된다. 비밀번호 입력은 화면에 표시되지 않는다. 이미 계정이 있다면 서버만 실행하면 된다.

이미 만들어 둔 가상환경을 사용한다면 다음 명령으로 관리자 계정을 생성할 수 있다.

```bash
cd /home/hun/finalproject/sysmon
.venv/bin/flask --app run create-admin
.venv/bin/python run.py
```

이전 서버가 실행 중이면 해당 터미널에서 Ctrl+C로 종료하고 재실행한다. 로그인 성공 후 상단의 **사용자 관리**에서 추가 계정을 만든다. 기본 아이디·비밀번호는 자동 생성하지 않는다.

## 파일 구성

- `run.py`: 로컬 서버 실행
- `app/__init__.py`: 앱 생성과 기능별 경로 등록
- `app/database.py`: 요청별 SQLite 연결·초기화·연결 종료
- `app/schema.sql`: 필수 테이블·제약 조건·조회 인덱스
- `app/security.py`: 세션 서명 키·로그인/권한 검사·CSRF 검증
- `app/routes/auth.py`: 로그인·로그아웃·사용자 관리·관리자 생성 명령
- `app/services/auth_service.py`: 계정 입력 검사·비밀번호 해시 생성 및 검증
- `app/models/user.py`: 사용자 DB 조회·생성·권한 변경
- `app/templates/auth/`: 로그인 및 사용자 관리 화면
- `app/routes/dashboard.py`: 기본 페이지 경로
- `app/routes/robots.py`: 로봇 상태 수신·로그인 사용자 조회 API
- `app/services/robot_service.py`: 상태 필드·시각 검증과 화면 표시값 변환
- `app/models/robot.py`: 최신 상태·수신 이력의 원자적 저장과 중복·순서 검사
- `app/routes/maps.py`: 점유 지도 임시 수신·현재 지도 JSON·보호된 PNG 조회 API
- `app/services/map_service.py`: OccupancyGrid 검증·PNG 변환·좌표/경로 변환
- `app/models/map.py`: 지도 이력·현재 지도·최근 로봇 위치 DB 조회
- `app/routes/events.py`: 이상 이벤트 multipart 수신·로그인 사용자용 증거 이미지 조회
- `app/services/event_service.py`: 화재·누수·장애물 필드·시각·이미지 검증과 원자적 저장
- `app/models/event.py`: 이벤트·증거 경로 원자적 저장과 재전송·충돌 판정
- `app/routes/vehicle_access.py`: 고정 웹캠 입차·출차 내역 수신·목록 API
- `app/services/vehicle_access_service.py`: 입출차 토픽 메타데이터 검증과 표시값 변환
- `app/models/vehicle_access.py`: 입출차 기록의 중복·충돌 판정과 SQLite 저장
- `app/models/dashboard_state.py`: 사용자별 이벤트·입출차 목록 표시 초기화 시각 저장
- `app/routes/cameras.py`: 네 카메라의 최신 PNG/JPEG 수신·로그인 사용자 조회 API
- `app/services/camera_service.py`: 프레임 검증·순서 판정·카메라별 최신 파일 교체·연결 상태 계산
- `app/routes/history.py`: 통합 이력 검색 페이지와 로그인 사용자용 JSON API
- `app/services/history_service.py`: 검색값·한국 날짜 검증과 DB 결과 라벨 변환·페이지 계산
- `app/models/history.py`: 사건·처리·상태·순찰·교대 테이블의 조건 조회와 시간순 통합
- `app/templates/index.html`: 기본 페이지
- `app/templates/history.html`: 통합 이력 필터·결과 표·페이지 이동 화면
- `app/templates/dashboard/icons.html`: 대시보드 공통 SVG 아이콘
- `app/static/css/dashboard.css`: 대시보드 전용 배치·반응형 스타일
- `app/static/css/history.css`: 통합 이력 검색 폼·결과 표·반응형 스타일
- `app/static/js/dashboard.js`: 한국 시간 표시와 2초 간격 로봇 상태 갱신
- `app/static/js/map.js`: 2초 간격 지도·로봇 마커·최근 경로 갱신
- `app/static/js/events.js`: 3초 간격 이벤트 목록·상세·처리 상태 갱신
- `app/static/js/cameras.js`: 1초 간격 영상 상태 조회와 변경된 최신 프레임 교체
- `tools/send_demo_map.py`: 실제 Nav2 연결 전 수동 지도 시연 도구
- `tools/send_demo_event.py`: 실제 이벤트 토픽 연결 전 화재·누수·장애물 시연 도구
- `tools/send_demo_vehicle_access.py`: 실제 차량 인식 연결 전 입차·출차 시연 도구
- `tools/send_demo_video.py`: 실제 영상 토픽 연결 전 네 카메라 움직임 시연 도구
- `app/static/css/style.css`: 기본 스타일
- `app/services/`: 후속 기능 처리 로직
- `app/models/`: 후속 데이터 접근 코드

## day5 예제 활용 계획

- 1단계: `0_app.py`의 서버·템플릿 기본 구조
- 로그인 단계: `4_login.py`, `6_login_two_camera.py`의 세션 흐름을 참고하되 DB 계정·비밀번호 해시·권한 검사 적용
- 영상 단계: `6_login_two_camera.py`의 두 영상 화면 구성을 참고하되, 네 소스가 서버로 최신 프레임을 보내는 구조와 연결 중단 표시로 확장
- DB 단계: `7_create_DB_TBL.py`, `9_TBL_on_Web.py` 참고. 고정 절대 경로와 시작 시 데이터 삭제는 사용하지 않고 이력 보존

## 진행 상태

- [x] 1단계: 프로젝트 폴더 구성·Flask 기본 페이지
- [x] 2단계: SQLite 저장 폴더·DB 초기화·필수 테이블 생성
- [x] 3단계: 로그인·로그아웃·권한 관리
- [x] 4단계: 기본 대시보드 화면 배치
- [x] 5단계: AMR1·AMR2 상태 수신·검증·최신/이력 저장·화면 갱신
- [x] 6단계: 점유 지도 수신·PNG 변환·로봇 위치와 최근 경로 표시
- [x] 7단계: 화재 이벤트·감지 로봇·좌표·위험도·증거 이미지 한 장 수신 및 저장
- [x] 8단계: 이벤트 로그·상세 이미지·권한별 순차 처리 상태와 메모 이력
- [x] 9단계: 로봇·고정 웹캠 최신 영상 수신·표시·연결 중단 감지
- [x] 10단계: 사건·처리·로봇 상태·순찰·교대 통합 이력 검색
- [x] 11단계: 누수·장애물 이벤트와 고정 웹캠 차량 입출차 로그
- [ ] 12단계 이후: 실제 ROS adapter·전체 통합 검증

## DB 초기화 흐름

서버 실행 → 앱 생성 → DB 경로 설정 → 저장 폴더 준비 → SQLite 연결 → 외래 키 검사 활성화 → WAL 설정 → 없는 테이블·인덱스 생성 → 연결 종료 → 요청 대기.

- DB 파일: `instance/sysmon.sqlite3`
- 증거 이미지 폴더: `instance/evidence/` (유효한 이벤트를 받을 때 PNG/JPEG 한 장 생성)
- 지도 이미지 폴더: `instance/maps/` (유효한 점유 지도를 받을 때 PNG 생성)
- 최신 영상 폴더: `instance/live_frames/` (카메라별 프레임 한 장과 메타데이터만 덮어쓰기)
- 사용자·로봇·샘플 이벤트는 자동 입력하지 않는다. 관리자 계정은 `create-admin` 명령으로 생성한다.
- 서버를 재실행해도 저장 데이터와 증거 파일을 삭제하지 않는다.
- 요청별 연결을 사용하고 요청 종료 시 닫는다. 후속 서비스는 `with get_db() as db:` 등으로 저장 단위의 커밋·실패 시 롤백을 수행해야 한다.
- WAL과 5초 잠금 대기는 동시 접근 경합을 줄이지만 여러 쓰기를 동시에 실행하지는 않는다. 잠금 시간 초과 등의 API 오류 처리는 후속 서비스 단계에서 추가한다.
- DB 초기화에 실패하면 오류를 기록하고 서버 시작을 중단한다.
- DB 기본 생성 시각은 UTC ISO 형식이다. 외부 발생 시각도 서비스 단계에서 같은 형식으로 검증·변환하고, 화면에서 한국 시간으로 표시한다.
- `CREATE TABLE IF NOT EXISTS`는 기존 테이블 구조를 변경하지 않는다. 향후 스키마 변경 시 별도 마이그레이션을 추가해야 한다.

| 테이블 | 저장 내용 |
| --- | --- |
| users | 계정·비밀번호 해시·권한 |
| robots | 로봇 기본 정보 |
| robot_latest_status | 로봇별 최신 상태 |
| robot_status_history | 로봇 상태 수신 이력 |
| maps | 지도 이력·좌표 메타데이터·PNG 파일 경로 |
| map_latest | 현재 표시할 지도 한 건 |
| events | 이벤트·감지 로봇·좌표·위험도·처리 상태 |
| event_evidence | 이벤트당 한 장의 증거 이미지 경로 |
| event_changes | 사용자·메모·처리 상태 변경 |
| vehicle_access_logs | 고정 웹캠의 입차·출차 구분과 발생 시각 |
| dashboard_clear_state | 사용자별 이벤트·입출차 최근 목록 표시 시작 시각 |
| commands | 외부 모듈 명령 결과 연동을 위한 예약 테이블; 시스템 모니터는 요청을 생성하지 않음 |
| patrol_runs | 순찰 실행 이력 |
| patrol_visits | 관측점 방문 이력 |
| handovers | 로봇 교대 이력 |

이벤트 위험도 `HIGH/MEDIUM/LOW`는 화면의 상/중/하에 대응한다. 처리 상태 `NEW/REVIEWING/WORK_REQUESTED/RESOLVED`는 신규/확인중/작업요청/조치완료에 대응한다. 실제 상태 전이와 이미지 저장은 후속 기능에서 구현한다.

## 2단계 검증

```bash
cd /home/hun/finalproject/sysmon
.venv/bin/python -m unittest discover -s tests -v
```

테스트는 임시 DB만 사용한다. 최초 생성, 재시작 데이터 보존, 이벤트 중복·잘못된 외래 키·위험도·두 번째 이미지 차단, 연결 정리·롤백, 잘못된 저장 경로에서 시작 중단을 확인한다.

## 3단계 인증 흐름

페이지 접속 → 로그인 여부 확인 → 아이디·비밀번호 입력 → DB 계정 조회 → 해시 검증 및 활성 상태 확인 → 사용자 세션 생성 → 권한에 맞는 페이지 표시.

| 기능 | 관리자 ADMIN | 관제자 OPERATOR | 조회자 VIEWER |
| --- | --- | --- | --- |
| 로그인·기본 페이지·로그아웃 | 허용 | 허용 | 허용 |
| 계정 생성·목록·권한 변경·비활성화 | 허용 | 차단 | 차단 |
| 이벤트 처리 기록 | 후속 단계 구현 | 후속 단계 구현 | 조회만 허용할 예정 |

- `/login`: 로그인 화면. 실패하면 같은 화면에 안내하며 비밀번호는 재표시하지 않는다.
- `/`: 로그인 필수. 성공한 사용자의 이름·권한을 표시한다.
- `/logout`: 폼 POST 요청으로 현재 브라우저 세션을 제거한다.
- `/admin/users`: 관리자 전용 사용자 목록·계정 생성 화면.
- `/admin/users/<id>/access`: 관리자 전용 권한·활성 상태 변경 POST 요청.
- 아이디는 영문·숫자·밑줄·점·하이픈 3~32자, 대소문자를 구분한다. 비밀번호는 8~128자이며 scrypt 해시만 저장한다.
- 세션은 로그인 후 8시간 만료되며 다른 브라우저의 세션과 분리된다. 같은 브라우저 프로필의 탭은 쿠키를 공유하므로 서로 다른 계정을 시험할 때는 다른 브라우저 또는 시크릿 창을 사용한다.
- 모든 변경 폼에 CSRF 토큰을 넣는다. 후속 로봇 HTTP 입력은 사용자 세션과 별도의 장치 인증을 설계할 때 추가한다.
- 요청마다 DB 권한을 다시 읽으므로 비활성화·권한 변경은 기존 로그인에도 다음 요청부터 반영된다.
- 마지막 활성 관리자의 강등·비활성화를 차단한다. 두 관리자의 동시 변경도 트랜잭션에서 확인한다.
- 세션 서명 키는 `instance/session.key`에 소유자 전용 권한으로 저장한다. `SYSMON_SECRET_KEY` 환경변수로도 지정할 수 있다. 키 파일·환경변수 값을 외부에 공유하지 않는다.
- 현재는 로컬 HTTP 개발 서버 기준으로 동작한다. 다중 PC 서비스용 서버·HTTPS 배포는 후속 단계이며, HTTPS 사용 시 `SESSION_COOKIE_SECURE=True`로 설정한다.

위 테스트 명령으로 인증 테스트도 함께 실행된다. 로그인 성공·실패, 사용자별 세션 분리, CSRF, 관리자 전용 URL 직접 접근, 계정 입력 검사, 비활성화, 마지막 관리자 보호, 재시작 계정 보존을 검증한다.

## 4단계 대시보드

서버 재시작 후 `/`에 로그인하면 통합 대시보드가 표시된다. 기본 실행은 `run.py`와 5000번 포트를 그대로 사용한다.

- 상단: 시스템 이름, 장비 연결 상태, 한국 시간, 사용자·권한, 로그아웃.
- 상태 요약: 시스템 상태와 AMR1·AMR2의 배터리·임무·위치·최근 수신을 한 줄에 표시한다.
- 본문: 좌측 Nav2 지도, 중앙 로봇 카메라 2개와 고정 웹캠 2개의 2×2 영상, 우측 최근 이벤트·차량 입출차 로그를 동시에 표시한다.
- 최근 이벤트: 발생 시각·종류·위험도를 요약하고, 이벤트 종류를 누르면 로봇·좌표·처리 상태·증거 이미지를 상세 창에서 확인한다. 최근 이벤트와 차량 입출차 행이 많아지면 각 패널 내부에서 세로 스크롤하며 지도와 네 영상 높이는 유지한다.
- 통합 이력: 우측 바로가기나 왼쪽 메뉴에서 전체 DB 기록 검색 화면으로 이동한다.
- 좁은 화면: 영상 2×2 구성을 우선 유지하고 공간이 부족하면 최근 로그를 영상 아래로 이동한다.

4단계는 화면 구조만 구현하므로 기존 DB에 이벤트가 있어도 아직 조회하지 않는다. 샘플 이벤트·배터리·정상 연결 상태를 자동 생성하지 않으며, 이벤트 발생·이미지 확대·검색은 각각 후속 단계에서 연결한다. 운영 명령 요청은 시스템 모니터 범위에서 제외한다.

검증: 2026-09-06 기존 인증·DB 테스트 16개 통과. 임시 DB를 사용한 실제 브라우저에서 로그인→대시보드, 메뉴 이동, 로그아웃, 관리자 화면 연결, 조회자 관리 접근 차단을 확인했다. 1440×1050과 390×844 화면을 확인했으며 페이지 전체 가로 넘침은 없었다. 테스트용 5002번 서버와 계정은 임시 사본에서만 사용했고 실제 프로젝트 DB에는 복사하지 않는다.

## 5단계 로봇 상태 수신

서버를 실행하기 전에 로봇 입력 전용 토큰을 환경변수로 설정한다. 값은 로봇·adapter와 서버에만 두며 HTML이나 JavaScript에 넣지 않는다.

```bash
cd /home/hun/finalproject/sysmon
export SYSMON_ROBOT_API_KEY='sysmon-demo-key-2026'
.venv/bin/python run.py
```

임시 입력 규약은 다음과 같다.

- `POST /api/robots/status`: 로봇 또는 임시 adapter의 상태 입력. `X-Robot-Token` 헤더 필요.
- `GET /api/robots/status`: 로그인한 대시보드의 최신 상태 조회.
- 허용 로봇: `AMR1`, `AMR2`.
- 필수 값: `message_id`, `robot_id`, `battery`, `x`, `y`, `frame_id`, `mission_status`, `connection_status`, `observed_at`.
- 임무: `IDLE`, `PATROLLING`, `PAUSED`, `RETURNING`, `DOCKING`, `CHARGING`, `EVACUATING`, `ERROR`.
- 연결: `ONLINE`, `OFFLINE`, `UNKNOWN`.
- 시각: 시간대가 포함된 ISO 8601. DB에는 UTC로 정규화해 저장한다.

시연용 입력 예시는 아래와 같다. 토큰과 `observed_at`은 실행 환경의 값으로 바꾼다.

```bash
curl -X POST http://127.0.0.1:5000/api/robots/status \
  -H 'Content-Type: application/json' \
  -H 'X-Robot-Token: sysmon-demo-key-2026' \
  -d '{
    "message_id": "amr1-status-0001",
    "robot_id": "AMR1",
    "battery": 82,
    "x": 12.4,
    "y": 8.7,
    "frame_id": "map",
    "mission_status": "PATROLLING",
    "connection_status": "ONLINE",
    "observed_at": "2026-09-06T10:50:00+09:00"
  }'
```

정상 신규 메시지는 HTTP 201, 내용이 같은 `message_id` 재전송은 200과 `duplicate`를 반환한다. 같은 ID에 다른 내용이 있거나 현재 상태보다 오래된 메시지는 409다. 잘못된 필드·범위·시각은 400이며 저장하지 않는다. 토큰이 없거나 다르면 401, 서버에 토큰 자체가 설정되지 않았으면 503이다.

유효한 상태는 `robot_status_history`에 한 행씩 보존하고 `robot_latest_status`의 해당 로봇 행을 갱신한다. 두 작업은 한 트랜잭션으로 처리한다. 마지막 수신 뒤 기본 15초 동안 새 상태가 없으면 화면에서 오프라인으로 판단한다. 대시보드는 2초마다 로그인 전용 조회 API를 호출하며, AMR1·AMR2 카드와 왼쪽 장비 연결 상태를 갱신한다. 샘플 상태는 서버 시작 때 자동 생성하지 않는다.

5단계 검증: 2026-09-06 임시 DB에서 전체 단위·요청 테스트 **25개 통과**. 추가된 9개 테스트는 장치 토큰, 입력 검증, 최신/이력 저장, 정상 재전송, ID 충돌, 오래된 메시지, 로그인 조회, 15초 오프라인 판정, 동시 재전송 한 건 저장을 확인한다. 실제 ROS 토픽과 실제 로봇은 아직 연결하지 않았다.

## 6단계 Nav2 점유 지도

현재 구현은 ROS 토픽명이 확정되기 전 사용할 내부 지도 서비스와 임시 HTTP 입력이다. Nav2가 일반적으로 사용하는 `nav_msgs/OccupancyGrid`의 핵심 필드와 같은 구조를 받는다.

- `POST /api/maps/current`: 지도 입력. `X-Robot-Token` 헤더 필요.
- `GET /api/maps/current`: 로그인 사용자의 지도 메타데이터·로봇 마커·최근 경로 조회.
- `GET /api/maps/current/image`: 로그인 사용자에게 현재 지도 PNG 제공.
- 필수 값: `message_id`, `frame_id`, `resolution`, `width`, `height`, `origin`, `data`, `observed_at`.
- `data`: 행 우선 방식의 `width × height` 정수 목록. `-1`은 미탐색, `0`은 빈 공간, `100`은 점유 공간이다.
- 현재 지도 좌표계는 `map`, 격자 제한은 100만 칸이다.

지도 격자 자체는 DB에 넣지 않는다. `instance/maps/`에 PNG로 저장하고 DB에는 해상도·크기·원점·회전·파일 경로와 수신 시각을 저장한다. 같은 message_id와 같은 내용은 중복 저장하지 않고, 같은 ID의 다른 내용이나 현재보다 오래된 지도는 409로 거부한다.

실제 지도가 없을 때는 다음 수동 시연 도구로 임시 지도를 한 건 전송할 수 있다. 서버와 명령을 실행하는 터미널에 동일한 환경변수가 있어야 한다.

```bash
cd /home/hun/finalproject/sysmon
export SYSMON_ROBOT_API_KEY='sysmon-demo-key-2026'
.venv/bin/python tools/send_demo_map.py
```

이 도구는 48×64 격자, 0.5m/pixel, 원점 `(0, 0)`인 시연용 지도만 전송하며 자동 실행되지 않는다. 이후 AMR 상태의 `frame_id`가 `map`이고 좌표가 지도 범위 안이면 지도 위에 현재 위치가 표시된다. 상태 이력의 최근 120개 좌표로 이동 경로를 그린다. 좌표계가 다르거나 범위를 벗어나면 잘못된 위치에 마커를 그리지 않고 화면에 이유를 표시한다.

6단계에서 표시하는 것은 정적 점유 지도다. 현재 사람·차량 같은 동적 장애물은 Nav2 costmap 토픽이 확정된 뒤 별도 레이어로 연결한다. 관측점 7개, 도크와 안전구역도 실제 좌표를 받기 전까지 임의 생성하지 않는다. 실제 ROS 연결 시 `ros_adapter.py`가 OccupancyGrid를 `map_service.receive_map`에 전달하므로 DB·PNG·화면 로직을 재사용한다.

6단계 검증: 2026-09-06 임시 DB에서 전체 테스트 **33개 통과**. 추가된 8개 지도 테스트는 장치 인증, 입력 검증, PNG와 메타데이터 저장, 재전송·충돌·오래된 지도, 로그인 보호, 원점·해상도·회전을 반영한 좌표 변환, 최근 경로, 좌표계 불일치와 범위 이탈을 확인한다. 임시 5004번 서버의 실제 브라우저에서 지도 한 건과 AMR1·AMR2 마커, AMR1 최근 경로, 2초 자동 갱신, 가로 넘침과 브라우저 오류가 없음을 확인했다. 실제 Nav2·TF·costmap 토픽은 아직 연결하지 않았다.

## 7단계 화재 이벤트·증거 이미지

임시 입력은 `POST /api/events`이며 `X-Robot-Token` 헤더와 `multipart/form-data`를 사용한다. `metadata`에는 JSON 객체를, `image`에는 PNG 또는 JPEG 한 장을 넣는다.

- 필수 메타데이터: `event_id`, `message_id`, `robot_id`, `event_type`, `occurred_at`, `captured_at`, `x`, `y`, `frame_id`, `risk_level`.
- `robot_id`: `AMR1` 또는 `AMR2`.
- 7단계 `event_type`: `FIRE`.
- `risk_level`: `HIGH`, `MEDIUM`, `LOW`이며 처리 상태와 별개다.
- 신규 이벤트의 처리 상태는 `NEW`로 저장한다.
- 증거 이미지는 이벤트당 한 장, PNG/JPEG, 최대 5MB다.
- 파일은 `instance/evidence/`에 저장하고 DB에는 이미지 경로만 저장한다.
- 같은 ID와 같은 내용의 재전송은 200 `duplicate`, ID가 같고 내용이 다르면 409다.
- 저장 성공 응답은 수신·기록 완료를 뜻하며 로봇의 다음 행동 명령이 아니다.

실제 이벤트 토픽 없이 수동 시연하려면 서버와 시연 터미널에 같은 ASCII 토큰을 설정한다.

```bash
cd /home/hun/finalproject/sysmon
export SYSMON_ROBOT_API_KEY='sysmon-demo-key-2026'
.venv/bin/python tools/send_demo_event.py --robot AMR1 --risk HIGH
```

성공하면 HTTP 201과 `accepted`, 이벤트 ID, `NEW` 상태가 출력된다. 시연 도구가 생성하는 불꽃 모양 PNG는 실제 카메라 사진이 아니다. 7단계는 수신·저장까지이며 대시보드 이벤트 표와 이미지 상세 표시는 8단계에서 연결한다.

7단계 검증: 실제 프로젝트 반영 후 임시 테스트 DB에서 전체 테스트 **40개 통과**. 추가된 이벤트 테스트 7개는 장치 인증, multipart 규약, 필드·시각·이미지 검증, 이벤트·파일 연결 저장, 정확한 재전송, ID 충돌, 로그인 이미지 보호와 경로 이탈 방지를 확인한다. 별도 임시 5006번 서버에 시연 도구를 실제로 요청해 AMR1 `FIRE/HIGH/NEW` 이벤트와 PNG 파일이 연결 저장되는 것을 확인했다. 실제 ROS 이벤트·카메라 토픽은 아직 연결하지 않았다.

## 8단계 이벤트 로그·상세·처리 기록

로그인한 대시보드는 서버 렌더링 시 최근 이벤트 최대 50건을 표시하고 `GET /api/events`를 3초마다 조회한다. 각 행에는 발생 시각, 화재, 감지 로봇, `frame_id (x, y)`, 위험도 상·중·하, 처리 상태와 증거 이미지 썸네일이 나온다. 썸네일의 **상세 보기**를 누르면 원본 이미지, 이벤트 ID, 촬영·발생 시각, 로봇과 좌표, 위험도, 상태, 변경 이력을 확인할 수 있다.

- `GET /api/events`: 로그인 사용자에게 최근 이벤트 목록 제공.
- `GET /api/events/<event_id>`: 이벤트 상세와 처리 변경 이력 제공.
- `GET /api/events/<event_id>/evidence`: 로그인 사용자에게 증거 이미지 제공.
- `POST /api/events/<event_id>/status`: 관리자·관제자만 처리 상태와 메모 기록.
- 허용 전이: `NEW → REVIEWING → WORK_REQUESTED → RESOLVED`.
- 조회자는 목록·상세·이미지를 볼 수 있지만 상태를 변경할 수 없다.
- 상태 변경 요청은 세션 CSRF 토큰을 검사하고 메모는 최대 500자다.
- `WORK_REQUESTED`는 외부 조치 요청을 관제 이력으로 표시할 뿐 로봇 명령을 만들지 않는다.

8단계 검증: 실제 프로젝트 반영 후 임시 테스트 DB에서 전체 테스트 **43개 통과**. 추가된 3개 요청 테스트는 저장값의 목록·상세·초기 HTML 표시, 조회자 변경 차단, 관제자의 순차 상태 전이·메모·감사 이력, CSRF·잘못된 전이·메모 길이·없는 이벤트를 확인한다. 임시 5007번 서버의 실제 브라우저에서 이벤트 2건·썸네일·상세 이미지와 `신규 → 확인중` 변경을 확인했다. 문서 너비 1265px/뷰포트 1280px로 가로 넘침이 없었고 브라우저 오류 로그도 없었다.

## 9단계 네 카메라 최신 영상

실제 ROS 영상 토픽이 확정되기 전에는 각 영상 소스가 PNG/JPEG 프레임을 임시 HTTP API로 보낸다. 서버는 녹화 영상을 DB나 파일 이력으로 쌓지 않고 `instance/live_frames/`의 카메라별 최신 프레임 한 장만 원자적으로 교체한다.

- `POST /api/cameras/<camera_id>/frame`: 장치 프레임 입력. `X-Robot-Token`, `X-Frame-Id`, `X-Captured-At` 필요.
- `GET /api/cameras`: 로그인 사용자의 네 카메라 상태·최신 이미지 URL 조회.
- `GET /api/cameras/<camera_id>/frame`: 로그인 사용자에게 최신 PNG/JPEG 제공.
- 카메라 ID: `amr1`, `amr2`, `webcam1`, `webcam2`.
- 프레임 최대 크기: 기본 2MB. 같은 프레임의 정상 재전송은 200, 같은 ID의 다른 내용이나 오래된 프레임은 409.
- 화면은 1초마다 상태를 확인하고 내용 해시가 달라졌을 때만 이미지를 교체한다.
- 마지막 서버 수신 후 기본 5초가 지나면 최근 이미지를 유지한 채 `연결 끊김`으로 표시한다.

서버를 실행한 상태에서 네 영역을 30초 동안 시험하는 명령은 다음과 같다. 생성되는 움직이는 격자 이미지는 실제 카메라 영상이 아니다.

```bash
cd /home/hun/finalproject/sysmon
export SYSMON_ROBOT_API_KEY='sysmon-demo-key-2026'
.venv/bin/python tools/send_demo_video.py
```

계속 보내려면 `--duration 0`, 특정 카메라만 보내려면 `--camera amr1`처럼 지정한다. 실제 ROS 연결에서는 adapter가 `sensor_msgs/Image` 또는 `CompressedImage`를 현재 `camera_service.receive_frame` 입력으로 변환하도록 연결한다. 최종 영상 해상도·FPS·압축 형식은 토픽 규약과 네트워크 시험 뒤 조정한다.

9단계 검증: 실제 프로젝트 코드로 임시 테스트 DB에서 전체 테스트 **49개 통과**. 추가된 6개 테스트는 장치 인증, 네 카메라 ID, PNG/JPEG·크기·시각 검증, 최신 프레임 덮어쓰기, 중복·충돌·오래된 프레임, 로그인 보호와 5초 연결 중단을 확인했다. 임시 5008번 서버의 실제 브라우저에서 네 영상의 `LIVE` 표시와 움직이는 프레임을 확인했고, 전송 종료 뒤 네 영역이 최근 프레임을 유지하며 `연결 끊김`으로 바뀌는 것도 확인했다.

## 10단계 통합 이력 검색

로그인 후 대시보드 왼쪽의 **통합 이력 검색** 또는 `/history`에서 사용한다. 별도 이력 테이블에 복사하지 않고 기존 DB 테이블을 같은 결과 열로 합쳐 발생 시각 역순으로 조회한다.

- 기록 종류: 전체, 화재 이벤트, 이벤트 처리, 로봇 상태, 순찰, 로봇 교대.
- 공통 조건: 한국 날짜 기준 시작일·종료일, AMR1·AMR2, 100자 이내 검색어.
- 이벤트 조건: 위험도 상·중·하, 처리 상태 신규·확인중·작업요청·조치완료.
- 검색어 대상: 메시지·이벤트·순찰·교대 ID, 임무·연결·처리 상태, 처리 메모·담당자, 관측점, 교대 사유.
- 결과: 시각, 종류, 로봇·웹캠, 주요 내용, 위험도, 상태, 담당자와 증거 이미지 링크.
- 한 페이지에 최대 50건을 표시하며 결과 수와 이전·다음 페이지를 제공한다.
- `/api/history`는 같은 조건을 로그인 사용자에게 JSON으로 제공한다.

일반 카메라 영상은 저장하지 않으므로 검색 대상이 아니다. `commands` 테이블은 외부 연동 예약 구조이며 시스템 모니터가 운영 명령을 요청하지 않으므로 결과에서 제외한다. 순찰·교대는 실제 연동 전에도 테이블에 값이 있으면 조회되지만 현재 값을 생성하는 수신 API는 아직 없다.

10단계 검증: 실제 프로젝트 코드로 임시 테스트 DB에서 전체 테스트 **55개 통과**. 추가된 6개 테스트는 로그인 보호, 다섯 기록 종류의 시간순 통합, 운영 명령 제외, 로봇·위험도·상태·메모·관측점·한국 날짜 검색, 잘못된 조건, 50건 페이지와 HTML 이동을 확인했다. 임시 5009번 서버의 실제 브라우저에서 전체 5건과 `화재 이벤트 + 위험도 상` 검색 결과 1건, 증거 이미지 링크와 화면 배치를 확인했다.

## 11단계 누수·장애물·차량 입출차

기존 화재 이벤트 입력의 `event_type`에 `LEAK`, `OBSTACLE`을 추가했다. 세 이벤트는 좌표·위험도·감지 로봇·증거 이미지와 `신규 → 확인중 → 작업요청 → 조치완료` 처리 흐름을 공유한다.

```bash
# 누수 이벤트
.venv/bin/python tools/send_demo_event.py --type LEAK --robot AMR1 --risk MEDIUM

# 장애물 이벤트
.venv/bin/python tools/send_demo_event.py --type OBSTACLE --robot AMR2 --risk LOW

# 고정 웹캠 입차
.venv/bin/python tools/send_demo_vehicle_access.py --camera webcam1 --direction ENTRY

# 고정 웹캠 출차
.venv/bin/python tools/send_demo_vehicle_access.py --camera webcam2 --direction EXIT
```

차량 입출차는 이상 경고와 분리된 `vehicle_access_logs`에 저장한다. `POST /api/vehicle-access`는 장치 토큰과 JSON 내역을 받고 로그인 사용자는 `GET /api/vehicle-access`로 조회한다. 대시보드는 3초마다 최근 50건을 갱신하며 통합 이력의 `차량 입출차` 종류에서도 검색할 수 있다.

이벤트 로그와 차량 입출차 로그의 **표시 초기화**는 원본 행을 삭제하지 않는다. `dashboard_clear_state`에 현재 사용자의 기준 시각을 저장하고 그 이후 수신된 항목만 최근 목록에 표시한다. 다른 사용자의 화면에는 영향을 주지 않으며 이전 기록은 통합 이력에서 계속 검색할 수 있다. 차량번호·인식률·차량 이미지는 받거나 저장하지 않는다.

11단계 검증: 2026-09-06 임시 DB에서 전체 테스트 **63개 통과**. 누수·장애물 공통 처리, 차량 입차·출차, 인증·입력 검증·중복·충돌·대시보드·통합 이력과 사용자별 표시 초기화를 확인했다. 실제 ROS2 토픽과 차량 인식 모듈은 아직 연결하지 않았다.
