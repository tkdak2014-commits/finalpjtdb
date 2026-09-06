"""임시 HTTP 로봇 상태를 내부 형식으로 검증하고 화면 표시값을 만든다."""

from datetime import datetime, timedelta, timezone
import math
import re

from flask import current_app

from ..models import robot as robot_model


ROBOT_NAMES = {"AMR1": "로봇 1", "AMR2": "로봇 2"}
MISSION_LABELS = {
    "IDLE": "대기", "PATROLLING": "순찰 중", "PAUSED": "일시정지",
    "RETURNING": "복귀 중", "DOCKING": "도킹 중", "CHARGING": "충전 중",
    "EVACUATING": "대피 중", "ERROR": "오류",
}
CONNECTION_LABELS = {"ONLINE": "온라인", "OFFLINE": "오프라인", "UNKNOWN": "확인 불가"}
MESSAGE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
FRAME_ID_PATTERN = re.compile(r"^[A-Za-z0-9_./-]{1,64}$")


class StatusValidationError(ValueError):
    """로봇 상태 입력 형식이 내부 규약과 다를 때 사용한다."""


def _required_text(payload, field):
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise StatusValidationError(f"{field} 값이 필요합니다.")
    return value.strip()


def _finite_number(payload, field):
    value = payload.get(field)
    # [숫자 검사] bool은 Python에서 int의 하위 형식이므로 좌표·배터리로 받지 않는다.
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise StatusValidationError(f"{field} 값은 유한한 숫자여야 합니다.")
    return float(value)


def _utc_timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise StatusValidationError("observed_at은 시간대가 포함된 ISO 8601 시각이어야 합니다.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise StatusValidationError("observed_at에 시간대가 필요합니다.")
    return parsed.astimezone(timezone.utc)


def validate_status(payload, now=None):
    """외부 메시지를 DB와 대시보드가 공통으로 쓰는 값으로 정규화한다."""
    if not isinstance(payload, dict):
        raise StatusValidationError("JSON 객체 형식의 상태가 필요합니다.")
    message_id = _required_text(payload, "message_id")
    if not MESSAGE_ID_PATTERN.fullmatch(message_id):
        raise StatusValidationError("message_id 형식이 올바르지 않습니다.")
    robot_id = _required_text(payload, "robot_id").upper()
    if robot_id not in ROBOT_NAMES:
        raise StatusValidationError("robot_id는 AMR1 또는 AMR2여야 합니다.")
    battery = _finite_number(payload, "battery")
    if not 0 <= battery <= 100:
        raise StatusValidationError("battery는 0에서 100 사이여야 합니다.")
    x = _finite_number(payload, "x")
    y = _finite_number(payload, "y")
    frame_id = _required_text(payload, "frame_id")
    if not FRAME_ID_PATTERN.fullmatch(frame_id):
        raise StatusValidationError("frame_id 형식이 올바르지 않습니다.")
    mission_status = _required_text(payload, "mission_status").upper()
    if mission_status not in MISSION_LABELS:
        raise StatusValidationError("지원하지 않는 mission_status입니다.")
    connection_status = _required_text(payload, "connection_status").upper()
    if connection_status not in CONNECTION_LABELS:
        raise StatusValidationError("connection_status는 ONLINE, OFFLINE, UNKNOWN 중 하나여야 합니다.")
    observed = _utc_timestamp(payload.get("observed_at"))
    current = now or datetime.now(timezone.utc)
    if observed > current + timedelta(minutes=5):
        raise StatusValidationError("observed_at이 서버 시각보다 5분 이상 미래입니다.")
    return {
        "robot_id": robot_id,
        "message_id": message_id,
        "battery": battery,
        "x": x,
        "y": y,
        "frame_id": frame_id,
        "mission_status": mission_status,
        "connection_status": connection_status,
        "observed_at": observed.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
    }


def receive_status(payload, now=None):
    # [수신 처리] 유효성 검사 뒤 모델 한 곳에서 중복·순서 검사와 두 테이블 저장을 수행한다.
    current = now or datetime.now(timezone.utc)
    status = validate_status(payload, current)
    received_at = current.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return robot_model.store_status(status, received_at)


def _parse_stored_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _display_time(value):
    # [화면 시각] DB는 UTC로 보존하고 사용자 화면에는 한국 시각을 함께 표시한다.
    korea = timezone(timedelta(hours=9))
    return _parse_stored_time(value).astimezone(korea).strftime("%m-%d %H:%M:%S")


def dashboard_robots(now=None):
    """DB 최신 행을 AMR1·AMR2 카드와 JSON 응답에 맞는 형식으로 변환한다."""
    current = now or datetime.now(timezone.utc)
    rows = {row["robot_id"]: row for row in robot_model.list_latest()}
    stale_after = timedelta(seconds=current_app.config["ROBOT_OFFLINE_AFTER_SECONDS"])
    result = []
    for robot_id, name in ROBOT_NAMES.items():
        row = rows.get(robot_id)
        if row is None or row["message_id"] is None:
            result.append({
                "id": robot_id, "name": name, "has_status": False,
                "connection_status": "UNKNOWN", "connection_label": "수신 대기",
                "battery": None, "mission_status": None, "mission_label": "—",
                "x": None, "y": None, "frame_id": None, "location_label": "—",
                "observed_at": None, "received_at": None, "received_label": "—",
            })
            continue
        received = _parse_stored_time(row["received_at"])
        stale = current - received > stale_after
        effective = "OFFLINE" if stale else row["connection_status"]
        result.append({
            "id": robot_id, "name": name, "has_status": True,
            "connection_status": effective, "connection_label": CONNECTION_LABELS[effective],
            "battery": row["battery"], "mission_status": row["mission_status"],
            "mission_label": MISSION_LABELS.get(row["mission_status"], row["mission_status"]),
            "x": row["x"], "y": row["y"], "frame_id": row["frame_id"],
            "location_label": f'{row["frame_id"]} ({row["x"]:.2f}, {row["y"]:.2f})',
            "observed_at": row["observed_at"], "received_at": row["received_at"],
            "received_label": _display_time(row["received_at"]),
        })
    return result


def fleet_summary(robots):
    online_count = sum(robot["connection_status"] == "ONLINE" for robot in robots)
    if online_count == len(robots):
        return "모든 로봇 온라인"
    if online_count:
        return f"로봇 {online_count}/{len(robots)} 온라인"
    if any(robot["has_status"] for robot in robots):
        return "연결된 로봇 없음"
    return "장비 연결 대기"
