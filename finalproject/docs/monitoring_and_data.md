# 모니터링과 데이터

상태: 기능 범위 기준·저장 모델 제안 · 담당: 관제(PC 3)

## 1. 책임과 경계

상태·이벤트·임무 결과를 수집해 관측 가능한 상태와 이력으로 제공한다. Dashboard는 읽기 전용이다. 모니터 기능이 독립적으로 mission·token·E-stop을 발행하지 않는다. 제어 판단은 [control_server.md](control_server.md)의 책임이다.

| 기능 | 역할 |
|---|---|
| Topic Ingestion | RobotStatus·PatrolReport·확정 이벤트 및 관련 상태 수신·검증 |
| Robot Status Monitor | 로봇 상태·pose 유효성·신선도·배터리·도킹 표시 |
| Event / Alarm Monitor | 확정 이벤트·화재·안전 원인·중복 처리 상태 관측 |
| Patrol / Handover Monitor | 순찰·방문·교대·보고 누락 추적 |
| Monitoring Data Logger | 이력·증적 연결·저장 오류 기록 |
| Monitoring DB / Dashboard | 조회용 데이터와 읽기 전용 화면 |

## 2. 상태와 결과 수집

- 화면 표시명 AMR1/AMR2는 robot1/robot6 매핑으로 표시한다.
- pose_valid=false일 때 마지막 유효 위치임을 구분하고 age를 표시한다. 무효 위치를 현재 위치처럼 표시하지 않는다.
- STALE은 수신 상태이며 AMR operational enum과 분리한다. Q-03을 따른다.
- 결과가 없는 임무는 UNREPORTED로 표시한다. FAILED 또는 CANCELED 보고서를 대필하지 않는다.
- CCTV timeout은 경고로 기록하고 마지막 permit을 유지하는 정책을 표시한다.
- E-stop 원인·활성화·해제 조건 시작/취소·해제 및 token 회수/만료 로그를 연결한다.

보고 재수신과 재연결 후 이력 합치기, 메시지 ID·측정 시각·수신 시각 필드는 [TBD-IF-003](interfaces.md#tbd)에서 확정한다. 수신 시각을 로봇의 측정 시각으로 대체하지 않는다.

## 3. 이벤트와 증적

관제는 AMR에서 확정된 DetectionEvent와 증적 메타데이터를 수신한다. bbox 정렬·감지 검증은 AMR에서 수행한다. 같은 event_id를 반복 처리하지 않는 정책을 유지하되 ID·보존 범위는 TBD-IF-006에서 정한다.

증적 이미지의 생성·전달·저장 완료를 구분한다. 이벤트 도착과 이미지 도착의 순서·원자성이 보장된다고 가정하지 않는다. 실제 전송 방식은 TBD-IF-007, 재시도·불완전 상태 표시와 저장 실패 처리는 TBD-MON-002다.

화재 부저의 실제 제어는 확정된 담당자·계약에 따른다. 모니터는 정책과 관측 결과를 보여주며 별도 제어권을 임의로 갖지 않는다.

## 4. 논리 데이터 모델 초안

아래 이름은 공유 대화에 등장한 논리 모델 후보다. 실제 DB·컬럼·타입·제약조건·DDL은 확정하지 않았다.

| 논리 항목 | 기록할 내용 | 연결 의도 |
|---|---|---|
| events | 로봇별 확정 감지 이벤트 | robot_id, event_id |
| event_evidence | 증적 위치·메타데이터·저장 상태 | 해당 event_id |
| event_changes | 이벤트 처리 상태 변경 이력 | 해당 event_id |
| robot_status_history | 로봇 상태와 시간 이력 | robot_id, 관측 시각 |
| patrol_runs | 순찰 실행·결과·보고 상태 | patrol/mission 식별자 |
| patrol_visits | waypoint 방문·스캔·결과 | 순찰 실행 식별자 |

ID 관계는 의도이며 필드 계약으로 확정된 것은 아니다. 명령과 임무·순찰·보고 ID의 연결은 interfaces.md에서 먼저 정하고 데이터 모델이 이를 따른다. event_changes는 '조회 전용 Dashboard에서 사용자가 수정한다'는 의미가 아니다.

## 5. Dashboard 범위

로봇별 상태·최근 유효 위치·배터리·도킹·현재 임무, 통신 신선도, permit·Keepout·안전 상태, 순찰/교대 진행, 이벤트와 증적 조회를 기능 초안으로 둔다. 정확한 화면 구성과 갱신 주기, 검색·조회 범위는 TBD-MON-003이다.

## 6. 보존과 운영

원본 데이터 유지 기간, 이미지 저장 위치·용량, 삭제 정책, 백업·복구, DB 장애 시 로컬 버퍼 여부는 아직 미정이다. 무제한 보존이나 자동 삭제를 기본 정책으로 채택하지 않는다.

명령 ID의 AMR 영속 캐시, CCTV 중복 제거 캐시, 관제 DB 보존은 서로 다른 저장 목적이다. Q-13/Q-14 값을 DB 전체의 보존 기간으로 사용하지 않는다.

## 7. 검증

상태 신선도·무효 pose 표시·UNREPORTED 보존, 중복 이벤트, 증적 누락/지연, 저장 실패, 조회 화면의 읽기 전용 범위를 검증한다. [IT-12·14·15](integration.md#4-통합시험-명세)에 연결한다.

## TBD

| ID | 미정 사항 | 영향 단위 | 상태 |
|---|---|---|---|
| TBD-MON-001 | DB 엔진·컬럼·ID 관계·인덱스, 로그 스키마·보존·백업 | 관제; 데이터 계약 변경 시 AMR·비전 | OPEN |
| TBD-MON-002 | 증적/DB 저장 실패, 버퍼·재시도·중복 저장, 제어에 미치는 영향 | 관제·AMR | OPEN |
| TBD-MON-003 | Dashboard 구성·갱신·조회 범위·접근 방식 | 관제 | OPEN |

공용 인터페이스 변화가 생기면 [수정 요청서](change_requests/README.md)를 통해 생산자·소비자 적용 여부를 추적한다.
