# AMR 기능 설계

상태: 설계 초안 · 담당: AMR 단위(PC 1·2) · 공통 계약: [interfaces.md](interfaces.md)

## 1. 책임과 경계

AMR1(robot1)과 AMR2(robot6)은 이 문서를 공유한다. 각 로봇은 명령 수신·임무 실행, Nav2·AMCL, 로컬 안전, 배터리·도킹, 감지·증적 생성을 담당한다. 식별 차이는 [architecture.md](architecture.md)에 둔다.

관제는 임무·주행 권한을 결정하고 AMR은 실행과 로컬 안전을 담당한다. PC 4 CCTV 이벤트 생성은 AMR 책임이 아니다. 기능 구분은 실제 ROS 노드 분할을 확정하지 않는다.

| 기능 | 입력 | 출력·역할 |
|---|---|---|
| mission_supervisor | MissionCommand, 로컬 상태 | 내부 Nav2 Action, 임무 진행·결과 |
| local_safety_supervisor | token, heartbeat, E-stop, 장애물, 주행 후보 | 최종 로봇별 속도 출력 |
| navigation/localization | 지도, LiDAR, odometry 등 | 경로 실행, map pose·유효성 |
| battery_monitor | SOC·충전 상태 | Battery enum |
| docking 기능 | 도킹 임무·센서 | 도킹 상태·결과 |
| 로컬 Detection·증적 | OAK-D 영상 | 후보, 확정 이벤트, 증적 |
| 상태·결과 발행 | 위 기능 상태 | RobotStatus, PatrolReport |

## 2. 명령과 임무 실행

1. 수신 namespace와 robot_id, 명령 enum, 필수 인자를 검증한다. 미정 인자 규칙은 TBD-IF-001을 따른다.
2. 영속 command_id 기록을 조회해 동일 명령을 다시 실행하지 않는다.
3. 주행이 필요한 명령은 유효 token 및 로컬 안전 조건을 통과해야 한다.
4. 필요할 때 mission_supervisor가 내부 Nav2 Action을 호출한다. 관제가 Nav2 Action을 직접 실행하는 경로를 만들지 않는다.
5. 진행 상태를 RobotStatus에 반영하고 종료 시 PatrolReport를 생성한다.

START_PATROL, MOVE_TO_SAFE_ZONE, RESUME_PATROL, DOCK는 실행 목적을 구분한다. STOP과 CANCEL의 정확한 임무 보존·종료 차이, 명령 대체 우선순위, 순찰 재개 지점은 TBD-AMR-005 및 TBD-CTRL-001에서 합의한다.

Operational/Mission/Docking은 별개 상태 축이다. interfaces.md의 enum을 따른다. 순찰→대피→대기→재개, 복귀→도킹→완료/실패 흐름은 기준이나 모든 상태 쌍 사이의 전이가 허용된다는 뜻은 아니다. 상세 전이표는 TBD-AMR-005다.

## 3. 로컬 안전과 속도 출력

local_safety_supervisor가 최종 속도 발행권을 가진다. Nav2나 yaw 정렬 기능이 안전 출력을 우회하지 않도록 한다. 구체적인 토픽·타입은 TBD-IF-009다.

- 유효하지 않은 token은 주행에 사용하지 않는다. 만료·회수 시 신규 주행을 막고 안전 정지한다.
- token의 sequence·holder·message age를 확인한다. 로컬 lease 경과는 Q-01을 따른다.
- 새 token만 수신했다고 임무를 자동 시작하지 않는다.
- E-stop 활성화는 즉시 반영한다. 물리 E-stop latch는 수동 reset 전까지 유지한다.
- token·heartbeat·장애물 원인이 사라진 뒤의 해제 결정은 관제가 한다. 해제 조건 유지 시간은 Q-10이다.
- heartbeat 상세 계약은 TBD-IF-004다. 임의 timeout을 추가하지 않는다.

정지 감속 방식·허용 정지 거리·센서 장애에 대한 속도 출력 규칙은 TBD-AMR-006이다. 안전 정지 요청과 실제 정지 관측을 구분한다.

## 4. Nav2·위치·Keepout

map frame의 pose·측정 시각·covariance를 제공한다. pose가 무효이면 마지막 유효 위치를 보존하되 현재 위치로 사용하지 않는다. 참고 위치 검증과 실제 주행 재개 기준은 Q-06과 Q-05로 구분한다.

AMR2 LiDAR 위치 검증 규칙은 제공 자료에 있으나 대상·계산 주체·통신 계약이 불명확하다(TBD-AMR-002). 이를 두 로봇에 임의로 일반화하지 않는다.

Keepout은 각 로봇의 global/local costmap에 필요하다. 계획 구성 예시는 다음과 같다.

~~~yaml
filters: ["keepout_filter"]
keepout_filter:
  plugin: "nav2_costmap_2d::KeepoutFilter"
  enabled: true
  filter_info_topic: costmap_filter_info
~~~

mask server와 costmap_filter_info_server도 필요하다. 이는 예시이며 실제 parameter 파일 변경 승인이 아니다. 원본에는 당시 param.yaml에 Keepout이 없다고 기록되어 있으며 현재 장비 설정을 직접 확인한 것은 아니다.

안전구역은 Q-08 조건을 모두 충족해야 한다. 차량 동선과의 거리를 우선하고 다음으로 경로 비용을 평가한다. 후보가 없으면 현재 위치에서 정지하고 SAFE_ZONE_NOT_FOUND를 보고한다. 계산 주체·지도/차량 동선 공급자는 TBD-CTRL-002다.

## 5. 배터리와 도킹

SOC·충전 방향에 따른 Battery enum은 interfaces.md 8절과 Q-11을 따른다. 무효·미수신은 UNKNOWN이다. 배터리 센서 신선도와 전류 부호·충전 여부 판정은 TBD-AMR-003이다.

도킹은 DOCKING 진입 시 타이머를 시작한다. Q-09의 제한 안에서는 Nav2 재계획을 허용하지만 새 도킹 mission을 만들지 않는다. 접점 또는 완료 센서의 연속 확인으로 성공을 판정하고 실패는 관제로 보고한다. 가용 로봇 선정과 역할 교대는 관제 책임이다.

## 6. 로컬 Detection과 증적

다음은 사용자가 제시한 설계 의도이며 Detection 관련 상세 계약은 TBD로 유지한다.

~~~text
OAK-D 영상 → bbox 생성 / DetectionCandidate
→ mission_supervisor가 AMR yaw 정렬
→ 영상 중심과 bbox 중심 정렬 상태에서 1초 연속 탐지
→ DetectionEvent 확정 → 증적 생성 → 관제 전달
~~~

PC 3는 bbox·yaw 제어를 직접 수행하지 않는다. 1초 조건의 의도는 보존하지만 정렬 오차, 동일 대상 기준, 탐지 단절 시 초기화, yaw timeout·token 및 이동 제한은 TBD-AMR-001이다. 이전 답변에서 추정한 즉시 타이머 초기화는 확정 정책으로 취급하지 않는다.

Candidate/Event 필드·enum·QoS는 TBD-IF-006, 증적 전송은 TBD-IF-007을 참조한다. 차량 CameraState와 DetectionEvent를 합친다고 가정하지 않는다.

화재 확정 시 부저 ON, 동일 event_id 중복 처리 금지, 도킹 완료 후 OFF라는 정책을 유지한다. 원본의 CHARGING 연속 확인 조건과 도킹 완료 센서 기준, 높은 SOC의 PATROL_READY/FULL 상태와의 관계는 TBD-AMR-004다. 실제 부저 제어 위치·계약도 미정이다.

## 7. 상태·결과·진단

RobotStatus의 발행·변경 rate는 Q-02다. PatrolReport는 명령과 연결해 SUCCEEDED/FAILED/CANCELED 및 실패·취소 reason을 제공한다. 통신 두절 후 결과 전달 방식은 TBD-IF-003이다.

다음 기존 안전 로그를 보존한다.

~~~text
E_STOP_ACTIVATED
E_STOP_RELEASE_CONDITION_STARTED
E_STOP_RELEASE_CONDITION_CANCELED
E_STOP_AUTO_RELEASED
DRIVE_TOKEN_REVOKED
DRIVE_TOKEN_EXPIRED
~~~

E-stop 해제 부저는 사용하지 않는다. 화재 부저와 E-stop 로그 정책을 혼용하지 않는다. 로봇·명령·이벤트 ID를 진단에 연결하는 것은 권장안이며 정확한 로그 스키마는 monitoring_and_data.md에서 정한다.

## 8. 검증 기준

명령 중복·토큰 역순/만료·최종 속도 발행권·무효 pose 보존·배터리 경계·도킹 제한·Detection 미확정 조건을 확인한다. 구체적 실행과 기대 결과는 [통합시험](integration.md#4-통합시험-명세)에 연결한다.

## TBD

| ID | 미정 사항 | 영향 단위 | 상태 |
|---|---|---|---|
| TBD-AMR-001 | 정렬 오차, 동일 대상·confidence, 연속 탐지 단절, yaw 속도·timeout·주행 중재 | AMR·관제 | OPEN |
| TBD-AMR-002 | AMR2 LiDAR 검증 대상·연산 위치·요청/결과·timeout | AMR·관제 | OPEN |
| TBD-AMR-003 | 배터리 입력 신선도, 충전 방향·무효값 판정 | AMR·관제 | OPEN |
| TBD-AMR-004 | 도킹 완료·CHARGING·높은 SOC 관계, 화재 부저 제어자·해제 계약 | AMR·관제 | OPEN |
| TBD-AMR-005 | 상세 상태 전이·STOP/CANCEL 차이·재개 지점·waypoint/scan 정책 | AMR·관제 | OPEN |
| TBD-AMR-006 | 로컬 정지 감속·거리·장애물 및 센서 실패 판정 | AMR·관제 | OPEN |

해결 시 결정 근거·일자와 [수정 요청서](change_requests/README.md)를 기록한다.
