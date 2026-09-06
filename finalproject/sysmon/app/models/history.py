"""통합 이력 화면에서 여러 기록 테이블을 같은 열 구조로 조회한다."""

from ..database import get_db


def _like_pattern(keyword):
    """사용자 입력의 LIKE 기호를 문자로 취급해 의도하지 않은 전체 검색을 막는다."""
    escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _common_conditions(filters, time_column, robot_sql, search_columns):
    clauses = []
    parameters = []
    if filters["start_utc"]:
        clauses.append(f"{time_column} >= ?")
        parameters.append(filters["start_utc"])
    if filters["end_utc"]:
        clauses.append(f"{time_column} < ?")
        parameters.append(filters["end_utc"])
    if filters["robot_id"]:
        clauses.append(robot_sql)
        parameters.extend([filters["robot_id"]] * robot_sql.count("?"))
    if filters["keyword"]:
        pattern = _like_pattern(filters["keyword"].lower())
        clauses.append("(" + " OR ".join(
            f"LOWER(COALESCE({column}, '')) LIKE ? ESCAPE '\\'" for column in search_columns
        ) + ")")
        parameters.extend([pattern] * len(search_columns))
    return clauses, parameters


def _where(clauses):
    return " WHERE " + " AND ".join(clauses) if clauses else ""


def _event_query(filters):
    clauses, parameters = _common_conditions(
        filters, "e.occurred_at", "e.robot_id = ?",
        ("e.event_id", "e.message_id", "e.event_type", "e.frame_id", "r.name"),
    )
    if filters["risk_level"]:
        clauses.append("e.risk_level = ?")
        parameters.append(filters["risk_level"])
    if filters["event_status"]:
        clauses.append("e.status = ?")
        parameters.append(filters["event_status"])
    sql = """
        SELECT 'EVENT' AS record_type, e.event_id AS record_id,
               e.occurred_at AS recorded_at, e.robot_id, r.name AS robot_name,
               e.event_type AS title_code,
               CASE WHEN e.x IS NULL OR e.y IS NULL THEN '좌표 없음'
                    ELSE COALESCE(e.frame_id, '좌표계 없음') || printf(' (%.2f, %.2f)', e.x, e.y) END AS summary,
               e.risk_level, e.status AS status_code, e.event_id,
               NULL AS actor,
               EXISTS(SELECT 1 FROM event_evidence evidence WHERE evidence.event_id=e.event_id) AS has_evidence
          FROM events e JOIN robots r ON r.robot_id=e.robot_id
    """ + _where(clauses)
    return sql, parameters


def _event_change_query(filters):
    clauses, parameters = _common_conditions(
        filters, "c.changed_at", "e.robot_id = ?",
        ("e.event_id", "c.memo", "c.previous_status", "c.new_status", "u.username", "r.name"),
    )
    if filters["risk_level"]:
        clauses.append("e.risk_level = ?")
        parameters.append(filters["risk_level"])
    if filters["event_status"]:
        clauses.append("c.new_status = ?")
        parameters.append(filters["event_status"])
    sql = """
        SELECT 'EVENT_CHANGE' AS record_type, CAST(c.id AS TEXT) AS record_id,
               c.changed_at AS recorded_at, e.robot_id, r.name AS robot_name,
               'EVENT_CHANGE' AS title_code,
               e.event_id || ' · ' || c.previous_status || ' → ' || c.new_status ||
                    CASE WHEN c.memo='' THEN '' ELSE ' · ' || c.memo END AS summary,
               e.risk_level, c.new_status AS status_code, e.event_id,
               u.username AS actor,
               EXISTS(SELECT 1 FROM event_evidence evidence WHERE evidence.event_id=e.event_id) AS has_evidence
          FROM event_changes c
          JOIN events e ON e.event_id=c.event_id
          JOIN robots r ON r.robot_id=e.robot_id
          JOIN users u ON u.id=c.user_id
    """ + _where(clauses)
    return sql, parameters


def _robot_status_query(filters):
    clauses, parameters = _common_conditions(
        filters, "h.observed_at", "h.robot_id = ?",
        ("h.message_id", "h.mission_status", "h.connection_status", "h.frame_id", "r.name"),
    )
    sql = """
        SELECT 'ROBOT_STATUS' AS record_type, CAST(h.id AS TEXT) AS record_id,
               h.observed_at AS recorded_at, h.robot_id, r.name AS robot_name,
               'ROBOT_STATUS' AS title_code,
               (CASE WHEN h.battery IS NULL THEN '배터리 —'
                     ELSE printf('배터리 %.0f%%', h.battery) END) || ' · ' ||
               h.mission_status || ' · ' || h.connection_status ||
               CASE WHEN h.x IS NULL OR h.y IS NULL THEN ''
                    ELSE ' · ' || COALESCE(h.frame_id, '좌표계 없음') || printf(' (%.2f, %.2f)', h.x, h.y) END AS summary,
               NULL AS risk_level, h.mission_status AS status_code, NULL AS event_id,
               NULL AS actor, 0 AS has_evidence
          FROM robot_status_history h JOIN robots r ON r.robot_id=h.robot_id
    """ + _where(clauses)
    return sql, parameters


def _patrol_query(filters):
    clauses, parameters = _common_conditions(
        filters, "p.started_at", "p.robot_id = ?",
        ("p.patrol_id", "p.status", "r.name"),
    )
    if filters["keyword"]:
        pattern = _like_pattern(filters["keyword"].lower())
        # [관측점 검색] P1~P7 방문값도 순찰 이력의 키워드로 찾을 수 있게 한다.
        clauses[-1] = clauses[-1][:-1] + (
            " OR EXISTS(SELECT 1 FROM patrol_visits pv2 WHERE pv2.patrol_id=p.patrol_id "
            "AND LOWER(pv2.observation_point) LIKE ? ESCAPE '\\'))"
        )
        parameters.append(pattern)
    sql = """
        SELECT 'PATROL' AS record_type, p.patrol_id AS record_id,
               p.started_at AS recorded_at, p.robot_id, r.name AS robot_name,
               'PATROL' AS title_code,
               p.patrol_id || ' · 관측점 ' ||
               COALESCE((SELECT GROUP_CONCAT(pv.observation_point, ', ')
                           FROM patrol_visits pv WHERE pv.patrol_id=p.patrol_id), '없음') AS summary,
               NULL AS risk_level, p.status AS status_code, NULL AS event_id,
               NULL AS actor, 0 AS has_evidence
          FROM patrol_runs p JOIN robots r ON r.robot_id=p.robot_id
    """ + _where(clauses)
    return sql, parameters


def _handover_query(filters):
    clauses, parameters = _common_conditions(
        filters, "h.requested_at", "(h.from_robot_id = ? OR h.to_robot_id = ?)",
        ("h.handover_id", "h.reason", "h.status", "source.name", "target.name"),
    )
    sql = """
        SELECT 'HANDOVER' AS record_type, h.handover_id AS record_id,
               h.requested_at AS recorded_at,
               h.from_robot_id || '→' || h.to_robot_id AS robot_id,
               source.name || ' → ' || target.name AS robot_name,
               'HANDOVER' AS title_code,
               h.handover_id || CASE WHEN COALESCE(h.reason, '')='' THEN '' ELSE ' · ' || h.reason END AS summary,
               NULL AS risk_level, h.status AS status_code, NULL AS event_id,
               NULL AS actor, 0 AS has_evidence
          FROM handovers h
          JOIN robots source ON source.robot_id=h.from_robot_id
          JOIN robots target ON target.robot_id=h.to_robot_id
    """ + _where(clauses)
    return sql, parameters


def _vehicle_access_query(filters):
    clauses, parameters = _common_conditions(
        filters, "v.detected_at", "0 = ?",
        ("v.access_id", "v.message_id", "v.camera_id", "v.direction"),
    )
    sql = """
        SELECT 'VEHICLE_ACCESS' AS record_type, v.access_id AS record_id,
               v.detected_at AS recorded_at, v.camera_id AS robot_id,
               CASE v.camera_id WHEN 'webcam1' THEN '고정 웹캠 1' ELSE '고정 웹캠 2' END AS robot_name,
               'VEHICLE_ACCESS' AS title_code,
               CASE v.direction WHEN 'ENTRY' THEN '입차' ELSE '출차' END || ' · ' || v.camera_id AS summary,
               NULL AS risk_level, v.direction AS status_code, NULL AS event_id,
               NULL AS actor, 0 AS has_evidence
          FROM vehicle_access_logs v
    """ + _where(clauses)
    return sql, parameters


QUERY_BUILDERS = {
    "EVENT": _event_query,
    "EVENT_CHANGE": _event_change_query,
    "ROBOT_STATUS": _robot_status_query,
    "PATROL": _patrol_query,
    "HANDOVER": _handover_query,
    "VEHICLE_ACCESS": _vehicle_access_query,
}


def search(filters):
    """선택한 기록 종류를 UNION한 뒤 전체 시간순으로 페이지 조회한다."""
    selected = list(QUERY_BUILDERS) if filters["record_type"] == "ALL" else [filters["record_type"]]
    if filters["risk_level"] or filters["event_status"]:
        selected = [name for name in selected if name in {"EVENT", "EVENT_CHANGE"}]
    if not selected:
        return [], 0
    statements = []
    parameters = []
    for name in selected:
        statement, values = QUERY_BUILDERS[name](filters)
        statements.append(statement)
        parameters.extend(values)
    union_sql = " UNION ALL ".join(statements)
    db = get_db()
    total = db.execute(f"SELECT COUNT(*) FROM ({union_sql}) AS history", parameters).fetchone()[0]
    rows = db.execute(
        f"SELECT * FROM ({union_sql}) AS history ORDER BY recorded_at DESC, record_type, record_id DESC LIMIT ? OFFSET ?",
        (*parameters, filters["per_page"], (filters["page"] - 1) * filters["per_page"]),
    ).fetchall()
    return rows, total
