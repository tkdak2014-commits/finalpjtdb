"""SQLite 연결과 초기화: day5의 DB 예제를 기능별 모듈로 분리한다."""

import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    # [요청별 DB 연결] 사용자 요청 간 연결을 공유하지 않고 현재 앱 문맥에서 재사용한다.
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"], timeout=5.0)
        try:
            connection.row_factory = sqlite3.Row
            # [참조 무결성] SQLite 외래 키 검사는 새 연결마다 활성화해야 한다.
            connection.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error:
            connection.close()
            raise
        g.db = connection
    return g.db


def close_db(error=None):
    # [연결 정리] 요청 종료 시 연결을 닫는다. 저장은 서비스에서 명시적으로 커밋한다.
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    # [폴더 준비] DB와 이미지 파일은 소스 코드와 분리해서 보관한다.
    Path(current_app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    Path(current_app.config["EVIDENCE_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(current_app.config["MAP_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(current_app.config["VIDEO_DIR"]).mkdir(parents=True, exist_ok=True)
    connection = get_db()
    # [동시 접근 준비] 읽기와 쓰기의 경합을 줄인다. 쓰기는 여전히 한 번에 하나씩 처리된다.
    connection.execute("PRAGMA journal_mode = WAL")
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    try:
        # [테이블 생성] 없을 때만 생성하며 초기화 전체를 하나의 트랜잭션으로 처리한다.
        connection.executescript("BEGIN IMMEDIATE;\n" + schema + "\nCOMMIT;")
    except sqlite3.Error:
        connection.rollback()
        raise
    _migrate_vehicle_access(connection)


def _migrate_vehicle_access(connection):
    """초기 이미지형 입출차 테이블을 토픽 내역 전용 구조로 한 번 변환한다."""
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(vehicle_access_logs)")
    }
    expected = {
        "access_id", "message_id", "camera_id", "direction", "detected_at", "received_at",
    }
    if columns == expected:
        return
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "ALTER TABLE vehicle_access_logs RENAME TO vehicle_access_logs_legacy"
        )
        connection.execute(
            """
            CREATE TABLE vehicle_access_logs (
                access_id TEXT PRIMARY KEY NOT NULL,
                message_id TEXT NOT NULL UNIQUE,
                camera_id TEXT NOT NULL CHECK (camera_id IN ('webcam1', 'webcam2')),
                direction TEXT NOT NULL CHECK (direction IN ('ENTRY', 'EXIT')),
                detected_at TEXT NOT NULL,
                received_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
            """
        )
        # [기존 기록 보존] 제거 대상 부가 필드를 버리고 입차·출차 핵심 내역은 유지한다.
        connection.execute(
            """
            INSERT INTO vehicle_access_logs
                (access_id, message_id, camera_id, direction, detected_at, received_at)
            SELECT access_id, message_id, camera_id, direction, detected_at, received_at
              FROM vehicle_access_logs_legacy
            """
        )
        connection.execute("DROP TABLE vehicle_access_logs_legacy")
        connection.execute(
            "CREATE INDEX idx_vehicle_access_detected ON vehicle_access_logs(detected_at)"
        )
        connection.execute(
            "CREATE INDEX idx_vehicle_access_camera_time ON vehicle_access_logs(camera_id, detected_at)"
        )
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        try:
            init_db()
        except (OSError, sqlite3.Error):
            # [초기화 실패] DB 없이 서버가 정상 동작하는 것처럼 시작하지 않도록 중단한다.
            app.logger.exception("SQLite 초기화 실패: 저장 경로와 접근 권한을 확인하세요.")
            raise
