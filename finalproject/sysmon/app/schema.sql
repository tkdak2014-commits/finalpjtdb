-- [사용자] 원문 비밀번호 대신 해시를 저장한다. 계정 생성·로그인은 3단계에서 구현한다.
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('ADMIN', 'OPERATOR', 'VIEWER')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- [로봇 기본 정보] robot_id로 AMR1·AMR2를 식별한다. 등록 데이터는 후속 단계에서 입력한다.
CREATE TABLE IF NOT EXISTS robots (
    robot_id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- [최신 상태] 로봇별 한 행을 유지한다. 좌표·임무 상태 값은 ROS 인터페이스 확정 전 내부 형식이다.
CREATE TABLE IF NOT EXISTS robot_latest_status (
    robot_id TEXT PRIMARY KEY NOT NULL REFERENCES robots(robot_id),
    message_id TEXT NOT NULL UNIQUE,
    battery REAL CHECK (battery BETWEEN 0 AND 100),
    x REAL,
    y REAL,
    frame_id TEXT,
    mission_status TEXT NOT NULL,
    connection_status TEXT NOT NULL CHECK (connection_status IN ('ONLINE', 'OFFLINE', 'UNKNOWN')),
    observed_at TEXT NOT NULL,
    received_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- [상태 이력] 최신 상태를 덮어써도 이전 수신 기록을 유지한다.
CREATE TABLE IF NOT EXISTS robot_status_history (
    id INTEGER PRIMARY KEY,
    robot_id TEXT NOT NULL REFERENCES robots(robot_id),
    message_id TEXT NOT NULL UNIQUE,
    battery REAL CHECK (battery BETWEEN 0 AND 100),
    x REAL,
    y REAL,
    frame_id TEXT,
    mission_status TEXT NOT NULL,
    connection_status TEXT NOT NULL CHECK (connection_status IN ('ONLINE', 'OFFLINE', 'UNKNOWN')),
    observed_at TEXT NOT NULL,
    received_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- [지도 이력] Nav2 OccupancyGrid를 웹 이미지로 변환하고 DB에는 파일 경로·좌표 메타데이터만 저장한다.
CREATE TABLE IF NOT EXISTS maps (
    id INTEGER PRIMARY KEY,
    message_id TEXT NOT NULL UNIQUE,
    frame_id TEXT NOT NULL,
    resolution REAL NOT NULL CHECK (resolution > 0),
    width INTEGER NOT NULL CHECK (width > 0),
    height INTEGER NOT NULL CHECK (height > 0),
    origin_x REAL NOT NULL,
    origin_y REAL NOT NULL,
    origin_yaw REAL NOT NULL,
    content_hash TEXT NOT NULL,
    image_path TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    received_at TEXT NOT NULL
);

-- [현재 지도] 지도 이력 중 대시보드에 사용할 한 건만 가리킨다.
CREATE TABLE IF NOT EXISTS map_latest (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    map_id INTEGER NOT NULL UNIQUE REFERENCES maps(id)
);

-- [이벤트] message_id 중복 저장을 막고 위험도와 관제 처리 상태를 별도 필드로 관리한다.
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY NOT NULL,
    message_id TEXT NOT NULL UNIQUE,
    robot_id TEXT NOT NULL REFERENCES robots(robot_id),
    event_type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    x REAL,
    y REAL,
    frame_id TEXT,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('HIGH', 'MEDIUM', 'LOW')),
    status TEXT NOT NULL DEFAULT 'NEW'
        CHECK (status IN ('NEW', 'REVIEWING', 'WORK_REQUESTED', 'RESOLVED')),
    received_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- [증거 이미지] 이벤트마다 한 장의 파일 경로만 저장한다. 영상·이미지 바이너리는 넣지 않는다.
CREATE TABLE IF NOT EXISTS event_evidence (
    id INTEGER PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE REFERENCES events(event_id),
    image_path TEXT NOT NULL,
    captured_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- [관제 이력] 사용자 확인·메모·상태 변경을 기록한다. 상태 전이 규칙은 후속 서비스에서 검사한다.
CREATE TABLE IF NOT EXISTS event_changes (
    id INTEGER PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events(event_id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    previous_status TEXT NOT NULL CHECK (previous_status IN ('NEW', 'REVIEWING', 'WORK_REQUESTED', 'RESOLVED')),
    new_status TEXT NOT NULL CHECK (new_status IN ('NEW', 'REVIEWING', 'WORK_REQUESTED', 'RESOLVED')),
    memo TEXT NOT NULL DEFAULT '',
    changed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- [차량 입출차] 인식 모듈에서 받은 입차·출차 내역만 저장한다.
CREATE TABLE IF NOT EXISTS vehicle_access_logs (
    access_id TEXT PRIMARY KEY NOT NULL,
    message_id TEXT NOT NULL UNIQUE,
    camera_id TEXT NOT NULL CHECK (camera_id IN ('webcam1', 'webcam2')),
    direction TEXT NOT NULL CHECK (direction IN ('ENTRY', 'EXIT')),
    detected_at TEXT NOT NULL,
    received_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- [대시보드 표시 기준] DB 이력을 삭제하지 않고 사용자별 최근 목록 시작 시각만 저장한다.
CREATE TABLE IF NOT EXISTS dashboard_clear_state (
    user_id INTEGER PRIMARY KEY NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_cleared_at TEXT,
    vehicle_access_cleared_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- [외부 연동 예약] 기존 설계의 명령 이력 구조다. 시스템 모니터에서는 운영 요청을 생성하지 않는다.
CREATE TABLE IF NOT EXISTS commands (
    command_id TEXT PRIMARY KEY NOT NULL,
    robot_id TEXT NOT NULL REFERENCES robots(robot_id),
    event_id TEXT REFERENCES events(event_id),
    requested_by INTEGER REFERENCES users(id),
    command_type TEXT NOT NULL CHECK (command_type IN ('START_PATROL', 'PAUSE', 'RESUME', 'RETURN', 'EVACUATE')),
    status TEXT NOT NULL DEFAULT 'REQUESTED'
        CHECK (status IN ('REQUESTED', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'REJECTED', 'TIMED_OUT')),
    result_message TEXT,
    requested_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    accepted_at TEXT,
    started_at TEXT,
    finished_at TEXT
);

-- [순찰] 순찰 실행 단위와 각 관측점 방문 기록을 분리한다.
CREATE TABLE IF NOT EXISTS patrol_runs (
    patrol_id TEXT PRIMARY KEY NOT NULL,
    robot_id TEXT NOT NULL REFERENCES robots(robot_id),
    command_id TEXT REFERENCES commands(command_id),
    status TEXT NOT NULL CHECK (status IN ('RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED')),
    started_at TEXT NOT NULL,
    ended_at TEXT
);
CREATE TABLE IF NOT EXISTS patrol_visits (
    id INTEGER PRIMARY KEY,
    patrol_id TEXT NOT NULL REFERENCES patrol_runs(patrol_id),
    observation_point TEXT NOT NULL CHECK (observation_point IN ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7')),
    visited_at TEXT NOT NULL,
    event_id TEXT REFERENCES events(event_id)
);

-- [교대] 교대 전후 로봇과 요청·완료 시각을 보존한다.
CREATE TABLE IF NOT EXISTS handovers (
    handover_id TEXT PRIMARY KEY NOT NULL,
    from_robot_id TEXT NOT NULL REFERENCES robots(robot_id),
    to_robot_id TEXT NOT NULL REFERENCES robots(robot_id),
    reason TEXT,
    status TEXT NOT NULL CHECK (status IN ('REQUESTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED')),
    requested_at TEXT NOT NULL,
    completed_at TEXT,
    CHECK (from_robot_id <> to_robot_id)
);

-- [조회 준비] 날짜별·로봇별 로그 검색에 필요한 인덱스를 만든다.
CREATE INDEX IF NOT EXISTS idx_events_occurred ON events(occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_robot_time ON events(robot_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_status_robot_time ON robot_status_history(robot_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_maps_observed ON maps(observed_at);
CREATE INDEX IF NOT EXISTS idx_event_changes_time ON event_changes(event_id, changed_at);
CREATE INDEX IF NOT EXISTS idx_event_changes_changed_at ON event_changes(changed_at);
CREATE INDEX IF NOT EXISTS idx_commands_robot_time ON commands(robot_id, requested_at);
CREATE INDEX IF NOT EXISTS idx_patrol_robot_time ON patrol_runs(robot_id, started_at);
CREATE INDEX IF NOT EXISTS idx_visits_patrol ON patrol_visits(patrol_id, visited_at);
CREATE INDEX IF NOT EXISTS idx_handovers_time ON handovers(requested_at);
CREATE INDEX IF NOT EXISTS idx_handovers_from_time ON handovers(from_robot_id, requested_at);
CREATE INDEX IF NOT EXISTS idx_handovers_to_time ON handovers(to_robot_id, requested_at);
CREATE INDEX IF NOT EXISTS idx_vehicle_access_detected ON vehicle_access_logs(detected_at);
CREATE INDEX IF NOT EXISTS idx_vehicle_access_camera_time ON vehicle_access_logs(camera_id, detected_at);
