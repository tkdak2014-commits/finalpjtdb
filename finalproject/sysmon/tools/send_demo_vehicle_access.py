"""실제 차량 인식 토픽 연결 전 입차·출차 내역을 보내는 수동 시연 도구."""

from datetime import datetime, timezone
import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description="Sysmon에 임시 차량 입출차 내역을 전송합니다.")
    parser.add_argument("--url", default="http://127.0.0.1:5000/api/vehicle-access")
    parser.add_argument("--camera", choices=("webcam1", "webcam2"), default="webcam1")
    parser.add_argument("--direction", choices=("ENTRY", "EXIT"), default="ENTRY")
    args = parser.parse_args()
    token = os.environ.get("SYSMON_ROBOT_API_KEY")
    if not token:
        raise SystemExit("SYSMON_ROBOT_API_KEY 환경변수를 먼저 설정하세요.")
    try:
        token.encode("ascii")
    except UnicodeEncodeError as exc:
        raise SystemExit("SYSMON_ROBOT_API_KEY는 ASCII 문자열이어야 합니다.") from exc

    now = datetime.now(timezone.utc)
    unique = now.strftime("%Y%m%d%H%M%S%f")
    payload = {
        "access_id": f"demo-access-{unique}",
        "message_id": f"demo-access-message-{unique}",
        "camera_id": args.camera,
        "direction": args.direction,
        "detected_at": now.isoformat(),
    }
    request = urllib.request.Request(
        args.url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "X-Robot-Token": token},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            print(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(exc.read().decode("utf-8"), file=sys.stderr)
        raise SystemExit(exc.code) from exc


if __name__ == "__main__":
    main()
