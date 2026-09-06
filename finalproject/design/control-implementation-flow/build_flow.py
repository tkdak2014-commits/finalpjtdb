"""관제(UI+서버·DB) 담당자가 이해해야 할 흐름도.
ROS 토픽은 아직 미연동 상태이며, Mock/HTTP로 먼저 구현하고
토픽 계약 확정 후 어댑터만 교체하는 단계적 구현을 전제로 한다.
기준 문서: design/parking-dashboard-v2/상세설계.md

출력: control-implementation-flow.drawio (3페이지) + 01~03 PNG 미리보기
"""
from pathlib import Path
import xml.etree.ElementTree as E
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
FONTB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'

BG = '#04101c'; PANEL = '#0a1e30'; PANEL2 = '#0d2438'; BORDER = '#1f3a52'
TEXT = '#e6eef7'; MUTED = '#9db0c4'
BLUE = '#5cb8ff'; GREEN = '#3ddc72'; ORANGE = '#ffb020'; RED = '#e5484d'
GRAY = '#5a6b7c'; GRAY_FILL = '#0e1620'

doc = E.Element('mxfile', host='app.diagrams.net', type='device')
pages = []
root = None; im = None; draw = None; W = H = 0
_n = [0]

def nid(p='n'):
    _n[0] += 1
    return f'{p}{_n[0]}'

def page(title, slug, w, h):
    global root, im, draw, W, H
    W, H = w, h
    d = E.SubElement(doc, 'diagram', name=title, id=slug)
    m = E.SubElement(d, 'mxGraphModel', grid='1', gridSize='10', page='1',
                      pageWidth=str(w), pageHeight=str(h), background=BG)
    root = E.SubElement(m, 'root')
    E.SubElement(root, 'mxCell', id='0')
    E.SubElement(root, 'mxCell', id='1', parent='0')
    im = Image.new('RGB', (w, h), BG)
    draw = ImageDraw.Draw(im)
    pages.append((d, slug))

def box(t, x, y, w, h, fill=PANEL, stroke=BORDER, size=15, color=TEXT,
        align='center', bold=False, rounded=1, dashed=False, sw=2, valign='middle'):
    st = (f'shape=rectangle;whiteSpace=wrap;html=1;rounded={rounded};arcSize=10;'
          f'fillColor={fill};strokeColor={stroke};strokeWidth={sw};'
          f'fontFamily=Noto Sans CJK KR;fontSize={size};fontColor={color};'
          f'align={align};verticalAlign={valign};spacing=6;'
          f'{"fontStyle=1;" if bold else ""}{"dashed=1;dashPattern=5 4;" if dashed else ""}')
    c = E.SubElement(root, 'mxCell', id=nid(), parent='1', vertex='1', value=t, style=st)
    E.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as': 'geometry'})
    pf = None if fill == 'none' else fill
    ps = None if stroke == 'none' else stroke
    if pf or ps:
        if dashed:
            _dashed_rect(x, y, w, h, ps, pf, sw)
        else:
            draw.rounded_rectangle((x, y, x + w, y + h), radius=6 if rounded else 0, fill=pf, outline=ps, width=sw)
    if t:
        f = ImageFont.truetype(FONTB if bold else FONT, size, index=1)
        tt = t.replace('<br>', '\n')
        tt = _wrap(tt, f, w - 20)
        b = draw.multiline_textbbox((0, 0), tt, font=f, spacing=5)
        tx = x + 10 if align == 'left' else (x + w - 10 - (b[2] - b[0]) if align == 'right' else x + (w - b[2] + b[0]) / 2)
        if valign == 'top':
            ty = y + 8 - b[1]
        else:
            ty = y + (h - b[3] + b[1]) / 2 - b[1]
        draw.multiline_text((tx, ty), tt, font=f, fill=color, spacing=5, align=align)
    return c

def _wrap(text, font, maxw):
    if maxw <= 0:
        return text
    lines = []
    for para in text.split('\n'):
        cur = ''
        for word in para.split(' '):
            test = word if not cur else cur + ' ' + word
            if draw.textlength(test, font=font) <= maxw or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    out = []
    for ln in lines:
        while draw.textlength(ln, font=font) > maxw and len(ln) > 1:
            k = len(ln)
            while k > 1 and draw.textlength(ln[:k], font=font) > maxw:
                k -= 1
            out.append(ln[:k])
            ln = ln[k:]
        out.append(ln)
    return '\n'.join(out)

def _dashed_rect(x, y, w, h, stroke, fill, sw):
    if fill:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=6, fill=fill)
    if not stroke:
        return
    seg, gap = 8, 5
    for xx in range(int(x), int(x + w), seg + gap):
        draw.line((xx, y, min(xx + seg, x + w), y), fill=stroke, width=sw)
        draw.line((xx, y + h, min(xx + seg, x + w), y + h), fill=stroke, width=sw)
    for yy in range(int(y), int(y + h), seg + gap):
        draw.line((x, yy, x, min(yy + seg, y + h)), fill=stroke, width=sw)
        draw.line((x + w, yy, x + w, min(yy + seg, y + h)), fill=stroke, width=sw)

def label(t, x, y, w, h, size=14, color=TEXT, align='left', bold=False, valign='middle'):
    return box(t, x, y, w, h, 'none', 'none', size, color, align, bold, 0, valign=valign)

def arrow(pts, color=BORDER, width=2, dashed=False, text=None, tsize=13, tcolor=None, toffset=(8, -10)):
    if dashed:
        _dashed_line(pts, color, width)
    else:
        draw.line(pts, fill=color, width=width)
    x2, y2 = pts[-1]
    x1, y1 = pts[-2]
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    L = 11
    p1 = (x2 - L * math.cos(ang - 0.4), y2 - L * math.sin(ang - 0.4))
    p2 = (x2 - L * math.cos(ang + 0.4), y2 - L * math.sin(ang + 0.4))
    draw.polygon([pts[-1], p1, p2], fill=color)
    style = (f'endArrow=block;html=1;strokeColor={color};strokeWidth={width};rounded=1;'
             f'{"dashed=1;dashPattern=5 4;" if dashed else ""}fontFamily=Noto Sans CJK KR;fontSize={tsize};'
             f'fontColor={tcolor or color};')
    c = E.SubElement(root, 'mxCell', id=nid('e'), parent='1', edge='1', value=text or '', style=style)
    g = E.SubElement(c, 'mxGeometry', relative='1', **{'as': 'geometry'})
    E.SubElement(g, 'mxPoint', x=str(pts[0][0]), y=str(pts[0][1]), **{'as': 'sourcePoint'})
    E.SubElement(g, 'mxPoint', x=str(pts[-1][0]), y=str(pts[-1][1]), **{'as': 'targetPoint'})
    a = E.SubElement(g, 'Array', **{'as': 'points'})
    for x, y in pts[1:-1]:
        E.SubElement(a, 'mxPoint', x=str(x), y=str(y))
    if text:
        if len(pts) == 2:
            tx, ty = (pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2
        else:
            tx, ty = pts[len(pts) // 2]
        f = ImageFont.truetype(FONT, tsize, index=1)
        tw = draw.textlength(text, font=f)
        draw.rectangle((tx + toffset[0] - 3, ty + toffset[1] - 2, tx + toffset[0] + tw + 3, ty + toffset[1] + tsize + 3), fill=BG)
        draw.text((tx + toffset[0], ty + toffset[1]), text, font=f, fill=tcolor or color)

def _dashed_line(pts, color, width):
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]; x2, y2 = pts[i + 1]
        dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if dist == 0:
            continue
        seg, gap = 9, 6
        n = int(dist // (seg + gap)) + 1
        for k in range(n):
            t0 = k * (seg + gap) / dist
            t1 = min(t0 + seg / dist, 1)
            draw.line((x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0, x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1), fill=color, width=width)

def title_bar(t, sub, w):
    box('', 0, 0, w, 66, '#061524', '#061524', rounded=0)
    label(t, 24, 8, w - 400, 32, 22, TEXT, bold=True)
    label(sub, 24, 38, w - 400, 22, 13, MUTED)

def legend(x, y, w):
    box('', x, y, w, 74, PANEL, BORDER)
    label('범례', x + 12, y + 4, 60, 20, 12, MUTED, bold=True)
    arrow([(x + 16, y + 30), (x + 70, y + 30)], GREEN, 3)
    label('지금 활성 (Mock/HTTP)', x + 78, y + 20, 220, 22, 12, GREEN)
    arrow([(x + 16, y + 55), (x + 70, y + 55)], GRAY, 2, dashed=True)
    label('예정 · ROS 미연동', x + 78, y + 45, 220, 22, 12, GRAY)

def layer(title, x, y, w, h, items, fill=PANEL2, stroke=BORDER, dashed=False, note=None, cols=None, tcolor=TEXT):
    box('', x, y, w, h, fill, stroke, dashed=dashed)
    label(title, x + 14, y + 6, w - 28, 24, 15, tcolor, bold=True)
    n = len(items)
    cols = cols or n
    rows = -(-n // cols)
    pad = 12
    cw = (w - pad * (cols + 1)) / cols
    ch = (h - 40 - pad * rows) / rows if rows else 0
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        ix = x + pad + c * (cw + pad)
        iy = y + 36 + r * (ch + pad)
        box(it, ix, iy, cw, ch, '#132c42' if not dashed else GRAY_FILL, '#2c4c68' if not dashed else GRAY,
            12, TEXT if not dashed else MUTED, dashed=dashed)
    if note:
        label(note, x + 14, y + h - 20, w - 28, 18, 11, MUTED)

def finish(slug):
    im.save(OUT / f'{slug}.png')

# ════════════════════════════════════════════════════════════════
# PAGE 1 — 상태·이벤트 수신 흐름 (ROS 미연동 지점 표시)
# ════════════════════════════════════════════════════════════════
W1, H1 = 1600, 1430
page('01 상태·이벤트 수신 흐름', '01-status-event', W1, H1)
title_bar('관제 흐름도 ① — 로봇 상태·이벤트 수신 (ROS 아직 미연동)',
          '기준: design/parking-dashboard-v2/상세설계.md · 지금은 Mock/HTTP로 개발, 토픽 계약 확정 후 ros_adapter로 교체', W1)
legend(1330, 14, 250)

y = 90
box('', 40, y, 1520, 90, GRAY_FILL, GRAY, dashed=True)
label('실제 로봇 · 감지/YOLO 모듈 (ROS 노드)', 60, y + 8, 1480, 24, 15, TEXT, bold=True)
label('로봇 상태(위치·배터리·순찰상태), 이벤트(누수·적치물·조도) — 아직 토픽 계약 미확정', 60, y + 38, 1480, 24, 13, MUTED)
label('※ 화재 포함 여부는 BR/SR 제외범위와 상충 → 팀 결정 전 기본 이벤트로 추가 안 함', 60, y + 62, 1480, 22, 12, ORANGE)

arrow([(800, y + 90), (800, y + 140)], GRAY, 2, dashed=True)
y2 = y + 140
box('ROS 토픽 계약 (미정)', 680, y2, 240, 50, GRAY_FILL, GRAY, 13, MUTED, dashed=True)

y3 = y2 + 90
bw = 730
box('', 40, y3, bw, 150, '#0e2a1c', GREEN)
label('지금 사용 중 — 개발용 Mock/HTTP 입력', 60, y3 + 8, bw - 40, 24, 14, GREEN, bold=True)
for i, t in enumerate(['Mock 로봇 상태 생성기', 'MockMission (명령 결과 시뮬레이터)']):
    box(t, 60 + i * (bw / 2 - 15), y3 + 40, bw / 2 - 30, 38, '#123a26', GREEN, 12)
box('POST /dev/ingest/status, /events', 60, y3 + 88, bw - 40, 32, '#123a26', GREEN, 12)
label('개발 환경 전용 인증 · 일반 대시보드 계정과 분리', 60, y3 + 124, bw - 40, 20, 11, MUTED)

box('', 830, y3, bw, 150, GRAY_FILL, GRAY, dashed=True)
label('예정 — ros_adapter.py (미연동)', 850, y3 + 8, bw - 40, 24, 14, MUTED, bold=True)
for i, t in enumerate(['ROS 구독 노드 (예정)', '토픽 → 내부 형식 변환 (예정)']):
    box(t, 850 + i * (bw / 2 - 15), y3 + 40, bw / 2 - 30, 38, GRAY_FILL, GRAY, 12, MUTED, dashed=True)
box('토픽명·메시지 필드 확정 후 구현', 850, y3 + 88, bw - 40, 32, GRAY_FILL, GRAY, 12, MUTED, dashed=True)
label('연결만 교체 — 위·아래 계층 코드는 그대로 재사용', 850, y3 + 124, bw - 40, 20, 11, MUTED)

arrow([(800, y2 + 50), (800, y3 - 20), (830, y3 - 20), (830, y3)], GRAY, 2, dashed=True)
arrow([(405, y3 + 150), (405, y3 + 190), (800, y3 + 190)], GREEN, 3, text='지금 이 경로로 개발/시연')
arrow([(1195, y3 + 150), (1195, y3 + 190), (800, y3 + 190)], GRAY, 2, dashed=True)

y4 = y3 + 190
box('공통 내부 형식 (models) — 출처와 무관하게 동일한 이벤트/상태 스키마', 620, y4, 360, 50, PANEL, BLUE, 13, BLUE, bold=True)
arrow([(800, y4 + 50), (800, y4 + 90)], BLUE, 2)

y5 = y4 + 90
box('검증·중복확인 — source_id+message_id 중복 제거 · 시퀀스/시각 역전 방지 · 필드 유효성', 400, y5, 800, 55, PANEL, BLUE, 13)
arrow([(800, y5 + 55), (800, y5 + 90)], BLUE, 2)

y6 = y5 + 90
layer('서비스 계층 (services) — 업무 규칙', 40, y6, 1520, 110,
      ['robot_service', 'event_service', 'command_service', 'patrol_service',
       'handover_service', 'camera_service', 'map_service', 'auth_service'], cols=8)
arrow([(800, y6 + 110), (800, y6 + 150)], BLUE, 2)

y7 = y6 + 150
layer('저장소 (repositories → SQLite)', 40, y7, 1520, 110,
      ['robots / robot_latest_status', 'events / event_evidence / event_changes',
       'commands / command_updates', 'patrol_runs / patrol_visits',
       'handovers / handover_updates', 'maps / map_features / routes'], cols=6)
arrow([(800, y7 + 110), (800, y7 + 150)], BLUE, 2)

y8 = y7 + 150
layer('API 계층 (Flask routes)', 40, y8, 1520, 110,
      ['GET /api/robots', 'GET /api/maps/{id}', 'GET /api/cameras',
       'GET·PATCH /api/events', 'GET /api/history/*', 'WS/폴링 갱신'], cols=6)
arrow([(800, y8 + 110), (800, y8 + 150)], BLUE, 2)

y9 = y8 + 150
layer('브라우저 UI (관제 화면)', 40, y9, 1520, 110,
      ['대시보드 (지도+로봇+영상)', '이벤트 상세·처리', '운영 명령 패널', '이력 조회'], cols=4)

label('DB 오류는 빈 데이터 성공 응답으로 숨기지 않는다 · 로봇 연결상태는 received_at 기준, 영상 연결상태와 별도 표시',
      40, y9 + 120, 1520, 24, 12, MUTED)
finish('01-status-event')

# ════════════════════════════════════════════════════════════════
# PAGE 2 — 운영 명령 요청 흐름 (ROS 미연동 지점 표시)
# ════════════════════════════════════════════════════════════════
W2, H2 = 1600, 1300
page('02 운영 명령 요청 흐름', '02-command-flow', W2, H2)
title_bar('관제 흐름도 ② — 운영 명령 요청 (순찰시작·일시정지·재개·복귀·대피)',
          '웹은 요청을 생성·기록만 한다 — 실제 수락·실행 판단은 로봇/미션 모듈이 담당', W2)
legend(1330, 14, 250)

y = 90
layer('브라우저 UI — 운영 명령 패널', 380, y, 840, 80,
      ['start_patrol', 'pause', 'resume', 'return_to_dock', 'evacuate'], cols=5)
arrow([(800, y + 80), (800, y + 140)], BLUE, 2, text='POST /api/commands', toffset=(10, -26))

y2 = y + 140
box('API — 권한(운영자·관리자) + 입력 검증 + idempotency_key 확인', 400, y2, 800, 55, PANEL, BLUE, 13)
arrow([(800, y2 + 55), (800, y2 + 95)], BLUE, 2)

y3 = y2 + 95
box('command_service — DB 저장: status=요청됨, delivery_status=pending', 400, y3, 800, 55, PANEL, ORANGE, 13, ORANGE)
label('재전송/더블클릭 → 동일 idempotency_key면 같은 request_id 반환', 400, y3 + 58, 800, 18, 11, MUTED)
label('응답: 202 + request_id (요청됨 — 로봇 수락을 의미하지 않음)', 400, y3 + 78, 800, 18, 11, MUTED)
arrow([(800, y3 + 100), (800, y3 + 140)], ORANGE, 2)

y4 = y3 + 140
bw = 730
box('', 40, y4, bw, 130, '#0e2a1c', GREEN)
label('지금 사용 중 — mock_adapter.py', 60, y4 + 8, bw - 40, 24, 14, GREEN, bold=True)
box('MockMission — 수락 → 진행 → 완료/실패 피드백 생성', 60, y4 + 42, bw - 40, 38, '#123a26', GREEN, 12)
label('시연 모드 표시 · UI에 "모의 실행" 뱃지', 60, y4 + 90, bw - 40, 24, 11, MUTED)

box('', 830, y4, bw, 130, GRAY_FILL, GRAY, dashed=True)
label('예정 — ros_adapter.py (미연동)', 850, y4 + 8, bw - 40, 24, 14, MUTED, bold=True)
box('실제 미션 모듈로 명령 전달 (예정)', 850, y4 + 42, bw - 40, 38, GRAY_FILL, GRAY, 12, MUTED, dashed=True)
label('토픽 계약 확정 후: 어댑터만 교체, 위 서비스 계층은 변경 없음', 850, y4 + 90, bw - 40, 24, 11, MUTED)

arrow([(405, y3 + 140), (405, y4)], GREEN, 3)
arrow([(1195, y3 + 140), (1195, y4)], GRAY, 2, dashed=True)

y5 = y4 + 130 + 55
box('로봇/미션 모듈 — 명령별 허용 상태·경로 유효성·최종 실행 가능 여부 판단 (책임 주체)', 300, y5, 1000, 60, GRAY_FILL, GRAY, 13, MUTED, dashed=True)
arrow([(405, y4 + 130), (405, y5)], GREEN, 3, text='결과: 수락/진행/완료/실패', toffset=(10, -34))
arrow([(1195, y4 + 130), (1195, y5)], GRAY, 2, dashed=True)

y6 = y5 + 60 + 55
box('command_updates 저장 — 시퀀스 검사(역전 방지) · external_update_id 중복 제거', 400, y6, 800, 55, PANEL, BLUE, 13)
arrow([(800, y5 + 60), (800, y6)], BLUE, 2, text='status: 수락됨→진행중→완료/실패', toffset=(10, -40))

y7 = y6 + 95
box('commands 최신 상태 갱신 (SQLite) — 응답 지연은 결과 미확인으로 표시, 실행 실패로 단정하지 않음', 350, y7, 900, 55, PANEL, ORANGE, 13, ORANGE)
arrow([(800, y6 + 55), (800, y7)], BLUE, 2)

y8 = y7 + 95
arrow([(800, y7 + 55), (800, y8)], BLUE, 2)
layer('브라우저 UI — 명령 이력·상태 반영', 500, y8, 600, 70,
      ['요청됨', '수락됨', '진행중', '완료 / 실패'], cols=4)

label('연결 복구 시 동일 request_id로 결과 확인/조정 — 새 요청 자동 생성 금지', 300, y8 + 90, 1000, 22, 12, MUTED)
finish('02-command-flow')

# ════════════════════════════════════════════════════════════════
# PAGE 3 — 구현 순서 로드맵
# ════════════════════════════════════════════════════════════════
W3, H3 = 1600, 1160
page('03 구현 순서 로드맵', '03-roadmap', W3, H3)
title_bar('구현 순서 로드맵 — 하나씩 단계적으로 (ROS 연동은 별도 단계)',
          '기준: 상세설계.md §10 구현순서 제안 · 계획이며 완료를 보장하거나 예약 실행한 것은 아님', W3)

steps = [
    ('1', '범위·내부 계약 고정', ['역할(관리자/운영자/조회자) 확정', '기본 이벤트 종류·위험등급 표기 방식 결정',
                              '명령 요청/실행 책임 경계 문서화', '로봇 ID(AMR1/2)·지도 ID 확정'], BLUE),
    ('2', '기반 기능', ['Flask 모듈 구성 (routes/services/repositories 분리)', 'SQLite 초기화·스키마 버전 관리',
                     '로그인·권한(3역할) 구현', '빈 대시보드 화면(초기 상태) 구현'], BLUE),
    ('3', '관제·사건', ['샘플 AMR1/2 상태 수신 (Mock)', '지도 7관측점·경로·안전구역·도크 표시',
                     '영상 4자리(로봇2+웹캠2) 연결 대기 표시', '이벤트 저장·상태변경(신규→확인중→작업요청→조치완료)·검색'], GREEN),
    ('4', '명령·미션 이력', ['명령 요청 저장(요청됨) → MockMission 수락·진행·완료/실패', '순찰(patrol_runs)·관측점 방문 기록',
                        '교대(handovers) 기록·검색', 'idempotency_key·시퀀스 역전 방지 적용'], GREEN),
    ('5', '검증·시연 준비', ['완료 확인 시나리오 표(§11) 전체 실행', '화면·DB 증거 캡처', 'draw.io·구현 범위 문서 최신화'], ORANGE),
    ('6', 'ROS 연동 (별도 단계·미정)', ['팀과 토픽명·메시지 필드·중복ID·순서 계약 확정',
                                   'ros_adapter.py 구현 — mock_adapter를 교체만 함',
                                   '서비스·저장소·API·UI 계층은 변경 없음', '실물 로봇 연동 시험 → 시연'], GRAY),
]

cols, rows = 3, 2
margin, gap_x, gap_y = 60, 40, 70
cardw = (W3 - 2 * margin - (cols - 1) * gap_x) / cols
cardh = 320
top = 100
positions = []
for i in range(len(steps)):
    r, c = divmod(i, cols)
    cx = margin + c * (cardw + gap_x)
    cy = top + r * (cardh + gap_y)
    positions.append((cx, cy))

for i, (num, title, items, color) in enumerate(steps):
    cx, cy = positions[i]
    dashed = (color == GRAY)
    fill = GRAY_FILL if dashed else PANEL
    box('', cx, cy, cardw, cardh, fill, color, dashed=dashed)
    box(num, cx + 14, cy + 14, 38, 38, color, color, 18, BG if not dashed else TEXT, bold=True, rounded=1)
    label(title, cx + 62, cy + 16, cardw - 76, 40, 16, TEXT if not dashed else MUTED, bold=True, valign='top')
    iy = cy + 68
    for it in items:
        box('•', cx + 16, iy, 16, 54, 'none', 'none', 14, color)
        label(it, cx + 34, iy, cardw - 50, 54, 12, MUTED, valign='top')
        iy += 60

# 화살표: 1→2→3 (행1), 3→4 (꺾임), 4→5→6 (행2)
for i in range(2):
    (x1, y1), (x2, y2) = positions[i], positions[i + 1]
    arrow([(x1 + cardw, y1 + cardh / 2), (x2, y2 + cardh / 2)], BLUE if i == 0 else GREEN, 3)
p3, p4 = positions[2], positions[3]
midy = p3[1] + cardh + gap_y / 2
arrow([(p3[0] + cardw / 2, p3[1] + cardh), (p3[0] + cardw / 2, midy),
       (p4[0] + cardw / 2, midy), (p4[0] + cardw / 2, p4[1])], GREEN, 3)
for i in range(3, 5):
    (x1, y1), (x2, y2) = positions[i], positions[i + 1]
    dashed = (i + 1 == 5)
    arrow([(x1 + cardw, y1 + cardh / 2), (x2, y2 + cardh / 2)], ORANGE if not dashed else GRAY, 3, dashed=dashed)

foot_y = top + rows * cardh + (rows - 1) * gap_y + 30
label('P0 (구현 전 필수 확정): 화재 포함 여부·감지유형·위험등급 산정주체 / 명령별 인자·권한·허용상태 / 교대 의미·생성주체·완료기준 / 지도 좌표계·버전·7관측점',
      60, foot_y, 1480, 24, 13, ORANGE)
label('P1 (진행하며 확정): 작업요청 외부전달 여부·오탐정책 / 영상 소스 수·주소 / 토픽·메시지 형식 / 이력 보존·응답지연 기준',
      60, foot_y + 28, 1480, 24, 13, MUTED)
label('※ 6단계(ROS 연동)는 1~5단계와 같은 우선순위로 지금 착수하지 않는다 — 계약 확정이 선행 조건',
      60, foot_y + 56, 1480, 24, 12, GRAY)
finish('03-roadmap')

# ════════════════════════════════════════════════════════════════
E.indent(doc)
E.ElementTree(doc).write(OUT / 'control-implementation-flow.drawio', encoding='utf-8', xml_declaration=True)
total = 0
for d, slug in pages:
    ids = [c.get('id') for c in d.findall('.//mxCell')]
    assert len(ids) == len(set(ids)), f'중복 ID 발견 in {slug}'
    total += len(ids)
print('OK', len(pages), 'pages,', total, 'cells total')
