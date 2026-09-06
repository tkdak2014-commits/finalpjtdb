# AMR 순찰 시스템 개발 문서

작성일: 2026-09-06 · 상태: 설계 초안 · 대상: AMR·관제·비전 전체 개발자

두 AMR이 CCTV 차량 상태와 관제의 주행 권한에 따라 순찰·대피·도킹·역할 교대를 수행하는 시스템이다. 전체 시스템의 공용 계약·배포·통합은 아직 설계 단계다. 다만 PC 3 관제의 모니터링 웹앱 `sysmon`은 1~11단계 기능 구현을 완료했으며, 실제 ROS 2·Nav2·TF·costmap·영상 토픽 연결과 전체 통합 검증은 아직 진행 전이다. 기존 결정은 유지하고 상세 계약이 부족한 부분은 각 문서의 TBD에 표시했다. 이는 실제 장비 배포와 전체 통합시험 완료를 의미하지 않는다.

## 문서 지도

~~~text
AGENTS.md
docs/
├── README.md
├── architecture.md
├── interfaces.md
├── amr.md
├── control_server.md
├── vision.md
├── monitoring_and_data.md
├── integration.md
└── change_requests/
    └── README.md
~~~

| 문서 | 역할 |
|---|---|
| [AGENTS.md](../AGENTS.md) | 공용 개발 규칙·승인·개발 단위 경계 |
| [architecture.md](architecture.md) | 시스템 구성·PC 역할·로봇 식별·Discovery·실행 환경 |
| [interfaces.md](interfaces.md) | 메시지·토픽·enum·QoS·시간 정책·공용 계약 TBD |
| [amr.md](amr.md) | PC 1·2 임무·주행·안전·배터리·도킹·Detection |
| [control_server.md](control_server.md) | PC 3 명령·권한·Keepout·교대·복구 판단 |
| [vision.md](vision.md) | PC 4 CCTV·차량 이벤트·patrol_allowed |
| [monitoring_and_data.md](monitoring_and_data.md) | PC 3 모니터링·이력·증적·읽기 전용 대시보드 |
| [integration.md](integration.md) | 기동·연결·정상 및 장애 흐름·통합시험 |
| [change_requests/README.md](change_requests/README.md) | 개발 단위 간 수정 요청 양식·처리 상태 |

## 읽기 순서와 작성 원칙

모든 개발자는 AGENTS → architecture → interfaces를 먼저 읽는다. 이후 담당 기능 문서와 integration을 읽는다. AMR1·AMR2는 amr.md를 공유하며 식별자·설정 차이만 구분한다.

통신 이름·필드·enum·공통 시간값은 interfaces.md가 기준이다. 기능 문서는 처리 규칙을, integration.md는 여러 단위를 통과하는 순서와 시험을 설명한다. 값을 변경할 때 기준 문서와 참조 문서의 일관성을 함께 확인한다.

- **기준:** 제공 자료 또는 사용자가 명시한 결정. 구현 검증 완료라는 뜻은 아니다.
- **제안:** 이번 문서에서 정리한 구현·운영 초안. 기존 결정으로 승격하지 않는다.
- **TBD:** 합의나 추가 정보가 필요한 항목. 본문 근처의 ID와 문서 끝 표를 참조한다.
- 미결 목록을 따로 복제하는 TBD 파일은 만들지 않는다. 요청서는 실제 공용 변경 결정 또는 타 단위 수정 필요가 있을 때 생성한다.

## 참고 자료와 최신 반영

- 사용자 제공 interface_tree.md 전체 1~17절을 기반으로 재구성했다.
- [공유 대화](https://chatgpt.com/s/cx_6a9d43ce6c50819180dbf0914b14bbab)의 텍스트를 참고했다. 대화 내 구성도 이미지는 직접 분석하지 않았다.
- 이후 현재 대화에서 확정한 간소화 문서 구조, 개발 규칙, 로컬/Offboard Discovery, robot1·robot6 식별 체계를 우선 반영했다.
- 기존 문서의 /amr1·/amr2 예시는 /robot1·/robot6으로 대체했다. 화면 표시는 AMR1·AMR2다.
- 이전 system_document_tree.md는 상세 폴더 구조의 과거 제안이며 현재 문서 지도가 기준이다.

## 초안의 한계

Detection 계약, 완전한 RobotStatus·PatrolReport 스키마, heartbeat/E-stop 세부 계약, 증적 전송·DB 설계 등이 남아 있다. 소프트웨어 버전·주소의 실제 적용 상태 및 장비 통신은 배포 시 검증한다. 승인되지 않은 설정이나 코드는 변경하지 않았다.
