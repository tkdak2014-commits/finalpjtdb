# 공용 ROS 2 토픽·메시지 계약

- 계약 버전: 1.0
- 확정일: 2026-09-07
- 상태: 문서 계약 확정 · 공용 메시지 PC 3 빌드 및 sysmon 일부 반영 · 실장비 검증 전
- 담당: AMR·관제·비전 공동
- 확정 근거: 2026-09-07 사용자의 인터페이스 문서 확정 요청

이 문서는 통신 이름, 메시지 필드·enum, ID, QoS와 공통 시간 기준의 원본이다. 문서 계약 확정은 `.msg` 패키지 구현, launch·YAML 적용, 장비 배포 또는 통합시험 완료를 의미하지 않는다. `{robot}`에는 슬래시 없는 `robot1` 또는 `robot6`만 사용한다. 화면 표시명 `AMR1`·`AMR2`를 계약 식별자로 사용하지 않는다.

## 1. 공통 규칙

- 사용자 정의 메시지는 모두 `parking_interfaces/msg`에 둔다.
- 모든 `message_id`, `command_id`, `mission_id`, `patrol_id`, `visit_id`, `event_id`, `evidence_id`, `estop_id`는 UUID v4 소문자 문자열이다. 값이 없는 선택 ID는 빈 문자열이다.
- `std_msgs/Header.stamp`는 생산자가 측정하거나 결정한 시각이다. 관제 수신 시각은 메시지를 바꾸지 않고 DB의 `received_at`으로 별도 기록한다.
- 위치를 포함하는 메시지의 `header.frame_id`는 `map`이다. 영상 메시지는 센서 optical frame을 사용한다.
- `sequence` 필드가 있는 메시지는 생산자별로 단조 증가시킨다. `boot_id` 필드가 있는 ControlHeartbeat·EStopState·RobotStatus는 생산자 재시작 시 `sequence=1`과 새 boot UUID를 사용한다.
- 같은 `message_id`와 같은 내용은 중복으로 인정하고 다시 처리하지 않는다. 같은 ID와 다른 내용은 충돌로 폐기하고 진단한다.
- 서로 다른 PC의 monotonic clock은 비교하지 않는다. lease와 timeout은 수신 측 monotonic clock으로 측정한다. `header.stamp` age 검사는 시간 동기화가 정상일 때만 사용하며, 시간 동기화가 불확실하면 주행 권한은 보수적으로 거부한다.
- QoS deadline 위반 알림과 애플리케이션 timeout 판정은 별개다.

## 2. 토픽 목록

### 2.1 관제·임무·안전

| 토픽·API | 타입·방식 | 송신 → 수신 |
|---|---|---|
| `/{robot}/mission_command` | `parking_interfaces/msg/MissionCommand` | 관제 → 해당 AMR |
| `/{robot}/mission_command_ack` | `parking_interfaces/msg/MissionCommandAck` | 해당 AMR → 관제 |
| `/control/drive_token` | `parking_interfaces/msg/DriveToken` | 관제 → 두 AMR의 local safety |
| `/control/heartbeat` | `parking_interfaces/msg/ControlHeartbeat` | 관제 → 두 AMR의 local safety |
| `/control/estop` | `parking_interfaces/msg/EStopState` | Safety Arbiter → AMR·관제 모니터링 |
| `/{robot}/keepout/status` | `parking_interfaces/msg/KeepoutStatus` | 해당 AMR → 관제·모니터링 |
| `/{robot}/cmd_vel_nav` | `geometry_msgs/msg/Twist` | Nav2 → local safety 후보 입력 |
| `/{robot}/cmd_vel_align` | `geometry_msgs/msg/Twist` | yaw 정렬 → local safety 후보 입력 |
| `/{robot}/cmd_vel` | `geometry_msgs/msg/Twist` | local safety → 해당 로봇 구동부 |

Keepout 변경은 토픽이 아니라 해당 로봇 global/local costmap의 ROS 2 parameter API를 사용한다. 외부 시스템은 Nav2 Action을 직접 호출하지 않고 MissionCommand를 사용한다.

### 2.2 상태·순찰·지도

| 토픽 | 타입 | 송신 → 수신 |
|---|---|---|
| `/{robot}/robot_status` | `parking_interfaces/msg/RobotStatus` | 해당 AMR → 관제·모니터링 |
| `/{robot}/patrol_visit` | `parking_interfaces/msg/PatrolVisit` | 해당 AMR → 관제·모니터링 |
| `/{robot}/patrol_report` | `parking_interfaces/msg/PatrolReport` | 해당 AMR → 관제·모니터링 |
| `/{robot}/ingestion_ack` | `parking_interfaces/msg/IngestionAck` | 관제 저장 계층 → 해당 AMR |
| `/map` | `nav_msgs/msg/OccupancyGrid` | 단일 canonical map publisher → AMR·관제 모니터링 |
| `/{robot}/global_costmap/costmap` | `nav_msgs/msg/OccupancyGrid` | 해당 AMR Nav2 → 관제 모니터링 |
| `/{robot}/local_costmap/costmap` | `nav_msgs/msg/OccupancyGrid` | 해당 AMR Nav2 → 관제 모니터링 |

`/map`에는 ROS_DOMAIN_ID 6에서 활성 publisher를 하나만 둔다. 로봇별 map server를 유지해야 하면 PC 3 adapter가 선택된 동일 지도 하나만 `/map`으로 relay한다. publisher의 실제 프로세스 위치와 launch는 TBD-ARCH-001에서 결정한다. costmap은 로봇별 namespace를 유지하고 sysmon에서 정적 지도와 별도 동적 레이어로 표시한다.

### 2.3 AMR Detection·증적

| 토픽 | 타입 | 송신 → 수신 |
|---|---|---|
| `/{robot}/detection/candidate` | `parking_interfaces/msg/DetectionCandidate` | AMR 감지 → 같은 AMR의 확정 처리 |
| `/{robot}/detection/event` | `parking_interfaces/msg/DetectionEvent` | 해당 AMR → 관제·모니터링 |
| `/{robot}/detection/evidence` | `parking_interfaces/msg/EvidenceChunk` | 해당 AMR → 관제 저장 계층 |
| `/{robot}/ingestion_ack` | `parking_interfaces/msg/IngestionAck` | 관제 저장 계층 → 해당 AMR |

Candidate는 AMR 로컬 경계다. 관제는 bbox 정렬과 yaw 제어를 수행하지 않는다. Event와 Evidence는 서로 독립적으로 도착할 수 있으며 원자적·순차 도착을 가정하지 않는다.

### 2.4 CCTV·순찰 허용

| 토픽 | 타입 | 송신 → 수신 |
|---|---|---|
| `/vision/cctv/gate_event` | `parking_interfaces/msg/CameraState` | gate_cam → cam_master·관제 모니터링 |
| `/vision/cctv/center_event` | `parking_interfaces/msg/CameraState` | center_cam → cam_master·관제 모니터링 |
| `/vision/cctv/patrol_allowed` | `std_msgs/msg/Bool` | cam_master → 관제 |

`patrol_allowed`는 판단 조건이며 주행·정지 명령이 아니다. `/control/vehicle_entry_block`은 만들지 않는다.

### 2.5 모니터링용 영상

| 토픽 | 타입 | 화면 매핑 |
|---|---|---|
| `/robot1/oakd/image/compressed` | `sensor_msgs/msg/CompressedImage` | AMR1 |
| `/robot6/oakd/image/compressed` | `sensor_msgs/msg/CompressedImage` | AMR2 |
| `/vision/cctv/gate/image/compressed` | `sensor_msgs/msg/CompressedImage` | 현재 sysmon의 webcam1 영역 |
| `/vision/cctv/center/image/compressed` | `sensor_msgs/msg/CompressedImage` | 현재 sysmon의 webcam2 영역 |

일반 영상은 최신 프레임만 표시하고 이력으로 저장하지 않는다. sysmon adapter는 표시용으로 최대 5 Hz까지만 처리하며 5초 동안 수신하지 못하면 최근 프레임을 유지한 채 연결 끊김을 표시한다. 이벤트 증적은 이 영상 계약과 별도다.

## 3. 메시지 계약

아래 블록은 `.msg` 구현의 필수 필드와 상수다. 필드 삭제·타입 변경·enum 재번호 부여는 새 계약 버전과 수정 요청서가 필요하다.

### 3.1 MissionCommand

~~~text
std_msgs/Header header
string command_id
string robot_id
uint8 command
string target_id
geometry_msgs/PoseStamped target_pose
string issued_by
string parameters_json

uint8 STOP=0
uint8 START_PATROL=1
uint8 MOVE_TO_SAFE_ZONE=2
uint8 RESUME_PATROL=3
uint8 DOCK=4
uint8 CANCEL=5
~~~

- `command_id`는 관제가 생성한다. 같은 명령 재전송은 같은 ID, 목적·내용 변경은 새 ID다.
- `robot_id`는 수신 namespace와 일치해야 한다.
- STOP·CANCEL은 target을 사용하지 않는다. `target_id=""`, `target_pose.header.frame_id=""`로 보낸다.
- START_PATROL·RESUME_PATROL은 `target_id`에 route 또는 patrol plan ID를 넣고 target pose는 비운다.
- MOVE_TO_SAFE_ZONE·DOCK는 `target_id` 또는 `target_pose` 중 정확히 하나를 사용한다. pose를 사용하면 frame은 `map`이다.
- 계약 v1.0의 `parameters_json`은 모든 command에서 `{}`만 허용한다. 후속 key는 계약 버전을 올려 정의하며, 정의되지 않은 key는 REJECTED 처리한다.
- AMR은 `command_id`를 영속 저장한다. 24시간이 지나거나 보관 개수가 1,000개를 초과하면 오래된 순서로 제거한다.
- 동일 ID·동일 내용은 다시 실행하지 않고 DUPLICATE ACK, 동일 ID·다른 내용은 REJECTED ACK를 보낸다.

### 3.2 MissionCommandAck

~~~text
std_msgs/Header header
string message_id
string command_id
string robot_id
uint8 status
uint16 reason_code
string detail

uint8 ACCEPTED=0
uint8 REJECTED=1
uint8 DUPLICATE=2
~~~

ACK는 명령 수신·검증 결과이며 임무 완료 결과가 아니다. 완료는 PatrolReport로 보고한다.

### 3.3 DriveToken

~~~text
std_msgs/Header header
string token
string holder_robot_id
builtin_interfaces/Duration lease_duration
uint32 sequence
~~~

- token은 발급마다 UUID v4이며, 빈 문자열은 회수다.
- `sequence`는 관제 실행 중 전역 단조 증가한다. 같은 token에서 마지막 수락 값 이하인 메시지는 폐기한다.
- 관제 재시작 또는 uint32 wrap 시 이전 lease 1.0초가 완전히 지난 뒤 새 token·`sequence=1`로 시작한다. 새 token을 받았다는 사실만으로 임무를 시작하지 않는다.
- holder 교체는 기존 holder 회수 → RobotStatus의 `drive_token_valid=false` 확인 → 신규 발급 순서다. 종단 주행 순서는 TBD-INT-001을 따른다.
- DDS lifespan과 동기화된 `header.stamp` 기준 500 ms보다 오래된 메시지는 폐기한다. lease는 AMR의 로컬 monotonic 수신 경과로 판정한다.
- 다른 holder용 token, 만료 token, 회수된 token은 주행 권한으로 사용하지 않는다.

### 3.4 ControlHeartbeat

~~~text
std_msgs/Header header
string message_id
string source_id
string boot_id
uint32 sequence
~~~

`source_id`는 `control`, `boot_id`는 관제 프로세스 시작마다 생성한 UUID v4다. 5 Hz로 발행하고 AMR이 1.0초 동안 유효 heartbeat를 받지 못하면 로컬 안전 정지한다. 재수신만으로 자동 출발하지 않는다.

### 3.5 EStopState

~~~text
std_msgs/Header header
string message_id
string estop_id
string boot_id
bool active
uint16 reason_code
string reason
bool manual_reset_required
string source_id
uint32 sequence
~~~

Safety Arbiter만 발행한다. 활성화마다 새 `estop_id`를 만들고, 해제 메시지는 같은 ID와 `active=false`를 사용한다. 물리 E-stop은 `manual_reset_required=true`이며 수동 reset 전에는 해제할 수 없다. E-stop 해제가 이동 명령을 뜻하지 않는다.

### 3.6 RobotStatus

~~~text
std_msgs/Header header
string message_id
string boot_id
uint32 sequence
string robot_id
uint8 operational_state
uint8 mission_state
uint8 docking_state
uint8 battery_state
float32 battery_soc
geometry_msgs/PoseWithCovariance pose
bool pose_valid
builtin_interfaces/Time last_valid_pose_stamp
string active_command_id
string mission_id
string patrol_id
uint32 safety_flags
bool drive_token_valid
bool keepout_enabled
uint16 diagnostic_code
string diagnostic_text
~~~

Operational enum:

~~~text
OP_UNKNOWN=0
OP_INITIALIZING=1
OP_READY=2
OP_MOVING=3
OP_STOPPED_SAFETY=4
OP_CHARGING=5
OP_ERROR=6
~~~

Mission enum:

~~~text
MISSION_NONE=0
MISSION_UNDOCKING=1
MISSION_PATROLLING=2
MISSION_MOVING_TO_SAFE_ZONE=3
MISSION_WAITING_SAFE_ZONE=4
MISSION_RETURNING_TO_DOCK=5
MISSION_DOCKING=6
MISSION_PAUSED=7
MISSION_COMPLETED=8
MISSION_FAILED=9
MISSION_CANCELED=10
~~~

Docking enum:

~~~text
DOCK_UNKNOWN=0
DOCK_UNDOCKED=1
DOCK_UNDOCKING=2
DOCK_DOCKING=3
DOCK_DOCKED=4
DOCK_FAILED=5
~~~

Battery enum:

~~~text
BATTERY_UNKNOWN=0
BATTERY_CRITICAL=1
BATTERY_LOW=2
BATTERY_NORMAL=3
BATTERY_CHARGING=4
BATTERY_PATROL_READY=5
BATTERY_FULL=6
~~~

Safety flags는 bit mask다.

~~~text
SAFETY_NONE=0
TOKEN_INVALID=1
HEARTBEAT_LOST=2
ESTOP_ACTIVE=4
OBSTACLE_BLOCKED=8
LOCALIZATION_INVALID=16
SENSOR_ERROR=32
KEEPOUT_UNKNOWN=64
~~~

- `battery_soc`는 0.0~1.0이며 무효이면 NaN과 BATTERY_UNKNOWN을 사용한다.
- `pose_valid=false`이면 pose에는 마지막 유효 pose를 유지하고 `last_valid_pose_stamp`를 함께 보낸다. 이를 현재 위치로 사용하지 않는다.
- STALE·ONLINE·OFFLINE은 수신 측 판단이며 메시지 enum에 넣지 않는다.
- safety 원인이 여러 개이면 flag를 OR로 결합한다.
- 정기 2 Hz로 발행하고 mission/safety/battery/pose_valid 변경 시 즉시 발행하되 전체 발행은 최대 10 Hz다.

### 3.7 PatrolVisit

~~~text
std_msgs/Header header
string message_id
string visit_id
string command_id
string mission_id
string patrol_id
string robot_id
string waypoint_id
geometry_msgs/PoseStamped pose
uint8 result
uint16 reason_code
string reason
builtin_interfaces/Time arrived_at
builtin_interfaces/Time completed_at

uint8 SUCCEEDED=0
uint8 SKIPPED=1
uint8 FAILED=2
~~~

### 3.8 PatrolReport

~~~text
std_msgs/Header header
string message_id
string report_id
string command_id
string mission_id
string patrol_id
string robot_id
uint8 result
uint16 reason_code
string reason
builtin_interfaces/Time started_at
builtin_interfaces/Time ended_at
uint32 planned_visit_count
uint32 completed_visit_count

uint8 SUCCEEDED=0
uint8 FAILED=1
uint8 CANCELED=2
~~~

FAILED·CANCELED는 4절의 `reason_code`와 구체적인 `reason`이 필수다. 결과가 없으면 관제가 대필하지 않고 로컬 DB에서 UNREPORTED로 표시한다. UNREPORTED는 메시지 enum이 아니다.

PatrolVisit·PatrolReport·DetectionEvent·EvidenceChunk는 IngestionAck의 STORED 또는 DUPLICATE를 받을 때까지 1초 간격으로 재전송한다. AMR은 미확인 데이터를 24시간 영속 보관한다.

### 3.9 IngestionAck

~~~text
std_msgs/Header header
string message_id
string robot_id
uint8 entity_type
string source_message_id
string entity_id
uint8 status
uint32[] missing_chunks
string detail

uint8 PATROL_VISIT=0
uint8 PATROL_REPORT=1
uint8 DETECTION_EVENT=2
uint8 EVIDENCE=3

uint8 STORED=0
uint8 DUPLICATE=1
uint8 INCOMPLETE=2
uint8 REJECTED=3
~~~

INCOMPLETE evidence ACK는 `missing_chunks`만 재전송하도록 요청한다. ACK는 저장 결과이며 다음 임무·주행 명령이 아니다.

### 3.10 CameraState와 patrol_allowed

~~~text
std_msgs/Header header
string event_id
string camera_id
uint8 state
float32 confidence

uint8 UNKNOWN=0
uint8 ENTERING=1
uint8 PARKED=2
uint8 EXITING=3
uint8 EXITED=4
~~~

- `camera_id`는 `gate_cam` 또는 `center_cam`이다.
- gate topic은 ENTERING·EXITED, center topic은 PARKED·EXITING만 허용한다.
- `event_id`는 상태 확정마다 PC 4가 생성한 UUID v4다. 동일 ID·동일 내용은 10분 동안 중복 제거하고, 동일 ID·다른 내용은 충돌로 폐기한다.
- confidence는 0.0~1.0이다. 확정 알고리즘의 threshold는 TBD-VIS-001이며 메시지 계약에는 포함하지 않는다.
- `patrol_allowed`는 초기 true다. ENTERING·EXITING은 false, PARKED·EXITED는 true다.
- cam_master는 값 변경 즉시 발행하고 2 Hz로 반복 발행한다. 관제가 1.5초 동안 받지 못하면 경고를 기록하되 마지막 값을 유지한다.

### 3.11 DetectionCandidate

~~~text
std_msgs/Header header
string message_id
string candidate_id
string robot_id
uint8 event_type
float32 confidence
uint32 image_width
uint32 image_height
float32 bbox_center_x
float32 bbox_center_y
float32 bbox_width
float32 bbox_height
~~~

### 3.12 DetectionEvent

~~~text
std_msgs/Header header
string message_id
string event_id
string robot_id
uint8 event_type
float32 confidence
uint8 risk_level
geometry_msgs/PoseWithCovariance pose
bool location_valid
builtin_interfaces/Time detected_at
string evidence_id

uint8 EVENT_UNKNOWN=0
uint8 FIRE=1
uint8 LEAK=2
uint8 OBSTACLE=3
uint8 LIGHTING=4
uint8 FACILITY_DAMAGE=5

uint8 RISK_UNKNOWN=0
uint8 RISK_LOW=1
uint8 RISK_MEDIUM=2
uint8 RISK_HIGH=3
~~~

- `header.frame_id`는 `map`이며 위치가 무효여도 빈 문자열로 바꾸지 않고 `location_valid=false`로 표시한다.
- `evidence_id`는 증적 생성 예정이면 UUID v4, 증적이 없으면 빈 문자열이다.
- 같은 event_id는 관제 DB 보존 기간 전체에서 한 사건으로 취급한다. 보완 정보는 새 `message_id`와 같은 `event_id`로 보낸다.
- Detection 확정 알고리즘 수치는 TBD-AMR-001을 따른다.
- DetectionCandidate의 `event_type`도 위 DetectionEvent enum 값을 사용한다.
- FIRE enum은 현재 sysmon과 AMR 문서의 wire compatibility를 위해 예약한다. 화재의 제품 인수 범위 포함 여부는 별도 사용자 결정 전까지 이 인터페이스 계약의 범위 밖이다.

### 3.13 EvidenceChunk

~~~text
std_msgs/Header header
string message_id
string evidence_id
string event_id
string robot_id
builtin_interfaces/Time captured_at
string media_type
string sha256
uint32 total_size
uint32 chunk_index
uint32 chunk_count
uint8[] data
~~~

- 허용 media type은 `image/jpeg`, `image/png`다.
- 전체 파일은 최대 5 MiB, chunk data는 최대 64 KiB다.
- `chunk_index`는 0부터 시작하고 모든 chunk의 메타데이터와 sha256이 같아야 한다.
- 관제는 임시 파일로 재조립한 뒤 크기·SHA-256·형식을 확인하고 원자적으로 저장한다.
- 이벤트와 증적 중 어느 것이 먼저 와도 수신하며, 미완료 증적은 INCOMPLETE로 표시한다.
- 저장 완료·중복·누락 chunk·거부는 IngestionAck로 회신한다.

### 3.14 KeepoutStatus

~~~text
std_msgs/Header header
string message_id
string transaction_id
string robot_id
uint8 state
bool global_enabled
bool local_enabled
uint16 reason_code
string detail

uint8 UNKNOWN=0
uint8 DISABLED=1
uint8 APPLIED=2
uint8 ROLLED_BACK=3
uint8 ROLLBACK_FAILED=4
~~~

대상 parameter는 다음과 같다.

| 노드 | parameter |
|---|---|
| `/robot1/global_costmap/global_costmap` | `keepout_filter.enabled` |
| `/robot1/local_costmap/local_costmap` | `keepout_filter.enabled` |
| `/robot6/global_costmap/global_costmap` | `keepout_filter.enabled` |
| `/robot6/local_costmap/local_costmap` | `keepout_filter.enabled` |

BatteryEvent와 ActionFeedback 별도 토픽은 만들지 않는다. 배터리는 RobotStatus, 명령 수신은 MissionCommandAck, 진행 상태는 RobotStatus, 최종 결과는 PatrolReport로 전달한다.

## 4. 공통 reason code

~~~text
0    NONE
100  CONTROL_CANCELED
101  COMMAND_SUPERSEDED
102  SAFETY_POLICY_CANCELED
200  INVALID_COMMAND
201  INVALID_TARGET
202  UNSUPPORTED_COMMAND
203  ID_CONFLICT
300  NAV_NO_PATH
301  NAV_TIMEOUT
302  NAV_GOAL_REJECTED
303  NAV_GOAL_ABORTED
400  SAFE_ZONE_NOT_FOUND
401  KEEPOUT_APPLY_FAILED
402  KEEPOUT_ROLLBACK_FAILED
500  LOCALIZATION_INVALID
501  POSE_STALE
502  LIDAR_VERIFICATION_FAILED
600  DRIVE_TOKEN_MISSING
601  DRIVE_TOKEN_EXPIRED
602  COMMUNICATION_LOST
700  E_STOP_ACTIVE
701  OBSTACLE_BLOCKED
702  FIRE_DETECTED
800  BATTERY_LOW
801  BATTERY_CRITICAL
900  DOCKING_TIMEOUT
901  ROLE_HANDOFF
1000 SENSOR_ERROR
1001 INTERNAL_ERROR
1002 STORAGE_REJECTED
~~~

reason code는 명령 ACK·PatrolReport·EStopState·KeepoutStatus의 진단 원인으로 사용한다. Detection `event_type` 값과 혼용하지 않는다.

## 5. QoS 계약

| 토픽 | Reliability | Durability | History·Depth | Deadline·Lifespan |
|---|---|---|---|---|
| mission_command | RELIABLE | VOLATILE | KEEP_LAST(10) | - |
| mission_command_ack | RELIABLE | VOLATILE | KEEP_LAST(20) | - |
| drive_token | BEST_EFFORT | VOLATILE | KEEP_LAST(3) | deadline 200 ms, lifespan 500 ms |
| heartbeat | BEST_EFFORT | VOLATILE | KEEP_LAST(5) | deadline 200 ms, lifespan 500 ms |
| estop | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) | - |
| robot_status | RELIABLE | VOLATILE | KEEP_LAST(5) | deadline 500 ms |
| patrol_visit·patrol_report | RELIABLE | VOLATILE | KEEP_LAST(20) | - |
| ingestion_ack | RELIABLE | VOLATILE | KEEP_LAST(20) | - |
| CameraState | RELIABLE | VOLATILE | KEEP_LAST(20) | - |
| patrol_allowed | RELIABLE | VOLATILE | KEEP_LAST(1) | deadline 500 ms |
| DetectionCandidate | BEST_EFFORT | VOLATILE | KEEP_LAST(1) | - |
| DetectionEvent | RELIABLE | VOLATILE | KEEP_LAST(20) | - |
| EvidenceChunk | RELIABLE | VOLATILE | KEEP_LAST(20) | - |
| KeepoutStatus | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) | - |
| `/map` | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) | - |
| global/local costmap | RELIABLE | VOLATILE | KEEP_LAST(1) | - |
| compressed image | BEST_EFFORT | VOLATILE | KEEP_LAST(1) | - |
| cmd_vel 후보·최종 | BEST_EFFORT | VOLATILE | KEEP_LAST(1) | - |

## 6. 공통 시간·거리 기준

| 기준 ID | 대상 | 값·규칙 |
|---|---|---|
| Q-01 | Drive Token | 발행 5 Hz, lease 1.0초, AMR 로컬 monotonic 경과 측정 |
| Q-02 | RobotStatus | 정기 2 Hz, 중요 상태 변경 즉시, 전체 최대 10 Hz |
| Q-03 | 관제 STALE | RobotStatus 미수신 1.5초 시 신규 mission·token 갱신 중단 |
| Q-04 | 복구 수신 게이트 | RobotStatus 정상 수신 5초 연속 |
| Q-05 | 주행 재개 pose | pose_valid=true, pose age ≤ 1.5초 |
| Q-06 | 복구 참고 위치 | 마지막 pose age ≤ 30초, AMR2 LiDAR 오차 ≤ 0.5 m, 방향 오차 ≤ 15도, 3회 연속 |
| Q-07 | Keepout 시도 | 시도당 timeout 2초, 총 2회, 첫 실패 후 200 ms 대기 |
| Q-08 | 안전구역 후보 | Keepout 밖 free cell, footprint-장애물 ≥ 0.5 m, 차량 동선 ≥ 1.0 m, 경로 가능, 다른 AMR과 비중첩 |
| Q-09 | 도킹 | DOCKING 진입 후 60초 이내, 접점 또는 완료 센서 3초 연속 확인 |
| Q-10 | E-stop | 활성화 즉시, 자동 해제 조건 3초 연속, 물리 E-stop은 수동 reset까지 latch |
| Q-11 | 배터리 전이 | CRITICAL 즉시, 기타 조건 3초 연속 |
| Q-12 | 화재 부저 OFF | CHARGING 3초 연속 및 DOCKED; 센서 관계는 TBD-AMR-004 |
| Q-13 | CCTV 중복 제거 | cam_master가 event_id 10분 보관 |
| Q-14 | 명령 중복 제거 | AMR 영속 저장, 24시간 또는 1,000개 초과 시 오래된 순서로 삭제 |
| Q-15 | Control heartbeat | 5 Hz, 수신 측 timeout 1.0초 |
| Q-16 | Patrol permit | 변경 즉시 및 2 Hz 반복, 1.5초 미수신 시 경고·마지막 값 유지 |
| Q-17 | 일반 영상 | sysmon 처리 최대 5 Hz, 5초 미수신 시 연결 끊김 표시 |

배터리 상태 구간은 다음과 같다.

| 상태 | SOC·조건 |
|---|---|
| CRITICAL | 방전 중 `< 0.10` |
| LOW | 방전 중 `0.10 ≤ SOC < 0.20` |
| NORMAL | 방전 중 `SOC ≥ 0.20` |
| CHARGING | 충전 중 `SOC < 0.50` |
| PATROL_READY | 충전 중 `0.50 ≤ SOC < 0.80` |
| FULL | 충전 중 `SOC ≥ 0.80` |
| UNKNOWN | 무효 또는 미수신 |

SR-05의 SOC 25% 자동 복귀는 임무 정책 threshold이며 위 Battery enum 경계와 별개다. 실제 복귀·교대 발동 조건은 TBD-CTRL-003에서 결정한다.

<a id="tbd"></a>

## 7. 해결된 인터페이스 TBD

아래 ID는 2026-09-07 사용자의 인터페이스 문서 확정 요청에 따라 계약 v1.0에서 해결했다. 영향 단위는 각 행에 기록하며 해결된 ID는 재사용하지 않는다.

| ID | 결정 | 영향 단위 | 상태 |
|---|---|---|---|
| TBD-IF-001 | MissionCommand 필수값·ACK·ID 충돌·보존 정책을 3.1~3.2로 확정 | AMR·관제 | RESOLVED |
| TBD-IF-002 | token 재시작·sequence·holder 교체·age 검증을 3.3으로 확정 | AMR·관제 | RESOLVED |
| TBD-IF-003 | RobotStatus·PatrolVisit·PatrolReport·ACK를 3.6~3.9로 확정 | AMR·관제 | RESOLVED |
| TBD-IF-004 | heartbeat와 E-stop을 3.4~3.5로 확정 | AMR·관제 | RESOLVED |
| TBD-IF-005 | CameraState 패키지·enum·ID를 3.10으로 확정 | 비전·관제 | RESOLVED |
| TBD-IF-006 | DetectionCandidate·DetectionEvent를 3.11~3.12로 확정 | AMR·관제 | RESOLVED |
| TBD-IF-007 | EvidenceChunk·IngestionAck·재전송을 3.9·3.13으로 확정 | AMR·관제 | RESOLVED |
| TBD-IF-008 | KeepoutStatus를 확정하고 BatteryEvent·ActionFeedback을 별도 생성하지 않음 | AMR·관제 | RESOLVED |
| TBD-IF-009 | namespaced Twist 후보와 local safety의 최종 `cmd_vel` 경계를 2.1로 확정 | AMR·관제 | RESOLVED |
| TBD-IF-010 | RobotStatus·permit 발행 제한과 timeout을 Q-02·Q-16으로 확정 | AMR·관제·비전 | RESOLVED |

## 8. 구현·검증 상태

- `parking_interfaces` `.msg` 파일: 계약 v1.0의 14개 구현, PC 3 빌드·import 확인
- AMR 생산자·소비자 코드: 미반영
- PC 3 Control Server: 미반영
- PC 3 sysmon ROS adapter: RobotStatus·정적 지도·압축 영상·costmap·DetectionEvent·EvidenceChunk 총 15개 구독과 IngestionAck 2개 회신의 로컬 가상 DDS PASS, 외부 publisher 연동 NOT_RUN
- PC 3 sysmon DB: costmap 최신 저장, Detection 보완 message_id, 미완료 evidence·chunk 영수증과 완성 증적 연결 반영
- PC 4 비전 생산자 코드: 미반영
- 장비 배포·통합시험: NOT_RUN

공용 패키지 구현과 단위별 반영 상태는 [CR-001](change_requests/CR-001_09-07_11-09_parking_interfaces_v1_구현.md)에서 추적한다. 이번 구현 승인은 공용 패키지 생성과 PC 3 빌드 확인 범위이며 AMR·비전 생산자 코드와 실제 장비 적용 승인을 뜻하지 않는다. 알고리즘·운영 정책의 남은 TBD는 각 기능 문서와 integration.md에서 관리한다.
