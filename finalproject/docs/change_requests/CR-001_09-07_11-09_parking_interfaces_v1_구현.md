# CR-001: parking_interfaces v1.0 공용 메시지 패키지 구현

- 상태: 반영 중
- 최초 작성 시각: 2026-09-07 11:09 KST
- 요청자: 프로젝트 사용자
- 요청 단위: 관제(PC 3)
- 대상 단위 및 로봇: AMR(PC 1·2, robot1·robot6), 관제(PC 3), 비전(PC 4)
- 관련 TBD ID: TBD-IF-001~010(해결됨), TBD-ARCH-001(배포 위치·기동 방식 미정)
- 기준 문서·절: [interfaces.md](../interfaces.md) 1~6절, 특히 3.1~3.14
- 결정 일자·근거: 2026-09-07, 사용자의 `interfaces.md` 계약 v1.0 확정 요청
- 코드 변경 승인 근거·범위: 2026-09-07 사용자의 “14단계 진행” 및 요청서 제시 후 “승인”. 프로젝트 루트 공용 패키지 생성과 PC 3 빌드·검증 승인

## 변경 이유

`interfaces.md`의 토픽·메시지 계약은 v1.0으로 확정됐지만 실제 `parking_interfaces` ROS 2 패키지와 설치본이 없다. 2026-09-07 PC 3에서 프로젝트와 `/home/hun/rokey_ws`를 확인한 결과 소스 패키지를 찾지 못했고, `ros2 pkg prefix parking_interfaces`는 `Package not found`, Python module 조회는 `None`이었다. 이 때문에 sysmon ROS adapter의 실제 구독 시작이 차단돼 있다.

## 변경 전 → 변경 후

### 기준

- 변경 전: `interfaces.md`에 계약 v1.0 메시지 정의만 있고 `.msg`, `package.xml`, `CMakeLists.txt`는 미구현이다.
- 변경 후 기준: 계약 v1.0을 내용 변경 없이 표현하는 `ament_cmake`·`rosidl` 기반 `parking_interfaces` 패키지를 공용 소스로 추가했다.
- 메시지 계약의 필드, 타입, enum 번호, 토픽, QoS, timeout은 이번 요청에서 변경하지 않는다.

### 제안 패키지 범위

- 생성 파일: `package.xml`, `CMakeLists.txt`
- 생성 메시지: `MissionCommand`, `MissionCommandAck`, `DriveToken`, `ControlHeartbeat`, `EStopState`, `RobotStatus`, `PatrolVisit`, `PatrolReport`, `IngestionAck`, `CameraState`, `DetectionCandidate`, `DetectionEvent`, `EvidenceChunk`, `KeepoutStatus`
- 직접 의존성 제안: `builtin_interfaces`, `geometry_msgs`, `std_msgs`, `rosidl_default_generators`, `rosidl_default_runtime`
- 공용 소스 위치 기준: 프로젝트 루트의 `parking_interfaces/`
- PC별 workspace 배치·source 방식: TBD-ARCH-001에서 실제 경로를 기록하되, 세 단위가 동일한 계약 버전을 빌드해야 한다.

## 요청 작업

| 대상 단위 | 필요한 변경·검토 | 대상 경로 또는 기능 | 담당 |
|---|---|---|---|
| 공용 | 계약 v1.0 그대로 `.msg` 14개와 rosidl 빌드 파일 생성·검토 | `parking_interfaces/` 제안 | 공동 검토 |
| AMR | robot1·robot6 workspace에서 동일 패키지 빌드·import 가능 여부 확인. 생산자·소비자 코드는 후속 승인 범위 | PC 1·2 ROS workspace | AMR |
| 관제 | PC 3 workspace에서 빌드·source 후 sysmon dependency check 수행. 실제 구독은 다음 단계 | PC 3 ROS workspace, `sysmon/ros_adapter.py --check` | 관제 |
| 비전 | PC 4 workspace에서 동일 패키지 빌드·CameraState import 가능 여부 확인. 생산자 코드는 후속 승인 범위 | PC 4 ROS workspace | 비전 |

## 영향과 적용 순서

1. 이 요청서에서 패키지 위치·범위와 계약 v1.0 무변경을 공동 확인한다.
2. 공용 패키지를 한 번 생성하고 모든 `.msg`가 `interfaces.md`와 일치하는지 대조한다.
3. PC 1·2·3·4가 같은 소스 버전을 각 workspace에서 빌드한다.
4. 각 PC가 해당 workspace를 source하고 필요한 메시지를 import한다.
5. PC 3에서 `ros_adapter.py --check`가 모든 의존성을 찾는지 확인한다.
6. 실제 producer·subscriber, launch·YAML·배포는 개발 단위별 후속 승인 후 반영한다.

기존 설치본이 없어 이전 패키지와의 호환 문제는 없지만, 일부 PC만 먼저 다른 메시지 정의를 사용하면 DDS 타입 호환이 깨진다. 따라서 독자적인 필드 수정이나 enum 재번호 부여를 금지하고 같은 패키지 버전을 사용한다. 빌드 또는 import 실패 시 기존 실행 환경을 유지하고 실제 ROS 구독을 시작하지 않는다.

## 단위별 반영 상태

| 단위·로봇 | 상태 | 반영 버전·근거 | 남은 작업 |
|---|---|---|---|
| AMR / robot1 | 미반영 | PC 1 확인 전 | 동일 소스 빌드·import 확인 |
| AMR / robot6 | 미반영 | PC 2 확인 전 | 동일 소스 빌드·import 확인 |
| 관제 | 반영 완료 | PC 3에서 공용 패키지 빌드, 14개 import와 sysmon dependency check PASS | 실제 publisher 구독은 후속 단계 |
| 비전 | 미반영 | PC 4 확인 전 | 동일 소스 빌드·CameraState import 확인 |

## 완료 조건과 검증

- 관련 `integration.md` 시험 ID: IT-01의 사전 준비. 실제 publisher 송수신 판정은 다음 단계에서 수행한다.
- `colcon build`가 오류 없이 완료된다.
- `ros2 pkg prefix parking_interfaces`가 source 후 설치 경로를 반환한다.
- `ros2 interface list`에 14개 메시지가 나타나고 `ros2 interface show` 결과가 `interfaces.md`와 일치한다.
- Python에서 14개 메시지를 import할 수 있다.
- PC 3에서 `sysmon/ros_adapter.py --check`가 종료 코드 0을 반환한다.
- AMR·비전의 실제 송수신 코드 변경 및 실제 장비 통합시험: NOT_RUN, 후속 승인 필요.

## 검토·결정 이력

| 일자 | 검토자·단위 | 결정·의견 | 근거 |
|---|---|---|---|
| 2026-09-07 | 관제(PC 3) | 초안 작성. 현 환경에서 패키지 소스·설치본 부재 확인 | `ros2 pkg prefix`, Python module 조회 |
| 2026-09-07 11:46 KST | 사용자·관제(PC 3) | 공용 패키지 구현 승인 후 계약 v1.0 메시지 14개 생성, PC 3 반영 완료 | `colcon build`, `ros2 interface package`, Python import, sysmon `--check` |
