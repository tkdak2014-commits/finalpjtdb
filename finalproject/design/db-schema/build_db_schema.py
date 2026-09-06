"""Sysmon DB 테이블 구조 산출물 (설계 발표용).

페이지 1: ERD — 11개 테이블의 컬럼·키·관계, 현재 실제 행 수 표시
페이지 2: 빈 DB → 데이터 삽입 → 웹페이지 반영 흐름 (실제 저장값 기준)

기준: sysmon/app/schema.sql, 2026-09-06 instance/sysmon.sqlite3 실측 행 수
출력: sysmon-db-schema.drawio + 01-erd.png, 02-data-flow.png
"""
from pathlib import Path
import math
import xml.etree.ElementTree as E
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
FONTB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
MONO = FONT

BG = '#04101c'; PANEL = '#0a1e30'; PANEL2 = '#0d2438'; BORDER = '#1f3a52'
TEXT = '#e6eef7'; MUTED = '#9db0c4'
BLUE = '#5cb8ff'; GREEN = '#3ddc72'; ORANGE = '#ffb020'; RED = '#e5484d'
GRAY = '#5a6b7c'; GRAY_FILL = '#0e1620'

doc = E.Element('mxfile', host='app.diagrams.net', type='device')
pages = []
root = None; im = None; draw = None
_n = [0]


def nid(p='n'):
    _n[0] += 1
    return f'{p}{_n[0]}'


def page(title, slug, w, h):
    global root, im, draw
    d = E.SubElement(doc, 'diagram', name=title, id=slug)
    m = E.SubElement(d, 'mxGraphModel', grid='1', gridSize='10', page='1',
                     pageWidth=str(w), pageHeight=str(h), background=BG)
    root = E.SubElement(m, 'root')
    E.SubElement(root, 'mxCell', id='0')
    E.SubElement(root, 'mxCell', id='1', parent='0')
    im = Image.new('RGB', (w, h), BG)
    draw = ImageDraw.Draw(im)
    pages.append((d, slug))


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


def box(t, x, y, w, h, fill=PANEL, stroke=BORDER, size=13, color=TEXT,
        align='center', bold=False, rounded=1, dashed=False, sw=2, valign='middle'):
    st = (f'shape=rectangle;whiteSpace=wrap;html=1;rounded={rounded};arcSize=8;'
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
        tt = _wrap(t.replace('<br>', '\n'), f, w - 16)
        b = draw.multiline_textbbox((0, 0), tt, font=f, spacing=4)
        tx = x + 8 if align == 'left' else (x + w - 8 - (b[2] - b[0]) if align == 'right' else x + (w - b[2] + b[0]) / 2)
        ty = y + 6 - b[1] if valign == 'top' else y + (h - b[3] + b[1]) / 2 - b[1]
        draw.multiline_text((tx, ty), tt, font=f, fill=color, spacing=4, align=align)
    return c


def label(t, x, y, w, h, size=13, color=TEXT, align='left', bold=False, valign='middle'):
    return box(t, x, y, w, h, 'none', 'none', size, color, align, bold, 0, valign=valign)


def arrow(pts, color=BORDER, width=2, dashed=False, text=None, tsize=12, toffset=(8, -18)):
    if dashed:
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]; x2, y2 = pts[i + 1]
            dist = math.hypot(x2 - x1, y2 - y1)
            if not dist:
                continue
            seg, gap = 9, 6
            for k in range(int(dist // (seg + gap)) + 1):
                t0 = k * (seg + gap) / dist
                t1 = min(t0 + seg / dist, 1)
                draw.line((x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0,
                           x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1), fill=color, width=width)
    else:
        draw.line(pts, fill=color, width=width)
    x2, y2 = pts[-1]; x1, y1 = pts[-2]
    ang = math.atan2(y2 - y1, x2 - x1)
    L = 10
    draw.polygon([pts[-1],
                  (x2 - L * math.cos(ang - 0.4), y2 - L * math.sin(ang - 0.4)),
                  (x2 - L * math.cos(ang + 0.4), y2 - L * math.sin(ang + 0.4))], fill=color)
    style = (f'endArrow=block;html=1;strokeColor={color};strokeWidth={width};rounded=1;'
             f'{"dashed=1;dashPattern=5 4;" if dashed else ""}'
             f'fontFamily=Noto Sans CJK KR;fontSize={tsize};fontColor={color};')
    c = E.SubElement(root, 'mxCell', id=nid('e'), parent='1', edge='1', value=text or '', style=style)
    g = E.SubElement(c, 'mxGeometry', relative='1', **{'as': 'geometry'})
    E.SubElement(g, 'mxPoint', x=str(pts[0][0]), y=str(pts[0][1]), **{'as': 'sourcePoint'})
    E.SubElement(g, 'mxPoint', x=str(pts[-1][0]), y=str(pts[-1][1]), **{'as': 'targetPoint'})
    a = E.SubElement(g, 'Array', **{'as': 'points'})
    for x, y in pts[1:-1]:
        E.SubElement(a, 'mxPoint', x=str(x), y=str(y))
    if text:
        mx, my = (pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2
        f = ImageFont.truetype(FONT, tsize, index=1)
        tw = draw.textlength(text, font=f)
        tx, ty = mx + toffset[0], my + toffset[1]
        draw.rectangle((tx - 3, ty - 2, tx + tw + 3, ty + tsize + 3), fill=BG)
        draw.text((tx, ty), text, font=f, fill=color)


def title_bar(t, sub, w):
    box('', 0, 0, w, 62, '#061524', '#061524', rounded=0)
    label(t, 24, 6, w - 420, 30, 21, TEXT, bold=True)
    label(sub, 24, 34, w - 420, 22, 12, MUTED)


# ════════════════════════════════════════════════════════════════
# PAGE 1 — ERD
# ════════════════════════════════════════════════════════════════
ROW_H = 21
HEAD_H = 42


def table(name, x, y, cols, rows_now, note='', live=True):
    """테이블 상자: 헤더(이름·행 수) + 컬럼 목록. cols = [(컬럼, 타입, 키)]"""
    w = 300
    h = HEAD_H + len(cols) * ROW_H + (20 if note else 6)
    accent = GREEN if live else GRAY
    fill = PANEL if live else GRAY_FILL
    box('', x, y, w, h, fill, accent, dashed=not live)
    box('', x, y, w, HEAD_H, '#12314b' if live else '#151d27', accent, dashed=not live, rounded=1)
    label(name, x + 10, y + 4, w - 110, 20, 14, TEXT if live else MUTED, bold=True)
    label(f'{rows_now}행', x + w - 100, y + 4, 90, 20, 12, accent, 'right')
    label('현재 데이터 있음' if live else '아직 0행 (미구현)', x + 10, y + 22, w - 20, 16, 10, MUTED)
    for i, (cname, ctype, key) in enumerate(cols):
        cy = y + HEAD_H + i * ROW_H
        kc = {'PK': ORANGE, 'FK': BLUE, 'U': '#c58bff', '': MUTED}[key]
        if key:
            label(key, x + 8, cy, 30, ROW_H, 10, kc, 'left', bold=True)
        label(cname, x + 42, cy, 150, ROW_H, 11, TEXT if live else MUTED)
        label(ctype, x + w - 110, cy, 100, ROW_H, 10, MUTED, 'right')
    if note:
        label(note, x + 10, y + h - 20, w - 20, 16, 10, ORANGE)
    return (x, y, w, h)


W1, H1 = 1980, 1320
page('01 DB 테이블 구조 (ERD)', '01-erd', W1, H1)
title_bar('Sysmon DB 테이블 구조 — 11개 테이블 · 관계 · 현재 적재 상태',
          '기준: sysmon/app/schema.sql · 행 수는 2026-09-06 instance/sysmon.sqlite3 실측값 · PK 기본키 / FK 외래키 / U 고유값', W1)

label('초록 실선 = 지금 실제로 데이터가 쌓이는 테이블   |   회색 점선 = 스키마만 만들어 둔 테이블 (기능 미구현)',
      24, 68, 1200, 20, 12, MUTED)

t_users = table('users', 60, 100, [
    ('id', 'INTEGER', 'PK'), ('username', 'TEXT', 'U'), ('password_hash', 'TEXT', ''),
    ('role', 'TEXT', ''), ('is_active', 'INTEGER', ''), ('created_at', 'TEXT', ''),
], 1, 'role CHECK: ADMIN/OPERATOR/VIEWER')

t_robots = table('robots', 430, 100, [
    ('robot_id', 'TEXT', 'PK'), ('name', 'TEXT', ''), ('created_at', 'TEXT', ''),
], 2, 'AMR1 · AMR2 두 행')

t_latest = table('robot_latest_status', 800, 100, [
    ('robot_id', 'TEXT', 'PK'), ('message_id', 'TEXT', 'U'), ('battery', 'REAL', ''),
    ('x', 'REAL', ''), ('y', 'REAL', ''), ('frame_id', 'TEXT', ''),
    ('mission_status', 'TEXT', ''), ('connection_status', 'TEXT', ''),
    ('observed_at', 'TEXT', ''), ('received_at', 'TEXT', ''),
], 2, '로봇당 1행 UPSERT — 화면 카드의 원본')

t_hist = table('robot_status_history', 1170, 100, [
    ('id', 'INTEGER', 'PK'), ('robot_id', 'TEXT', 'FK'), ('message_id', 'TEXT', 'U'),
    ('battery', 'REAL', ''), ('x', 'REAL', ''), ('y', 'REAL', ''), ('frame_id', 'TEXT', ''),
    ('mission_status', 'TEXT', ''), ('connection_status', 'TEXT', ''),
    ('observed_at', 'TEXT', ''), ('received_at', 'TEXT', ''),
], 1013, 'message_id UNIQUE → 재전송 중복 차단')

t_events = table('events', 430, 430, [
    ('event_id', 'TEXT', 'PK'), ('message_id', 'TEXT', 'U'), ('robot_id', 'TEXT', 'FK'),
    ('event_type', 'TEXT', ''), ('occurred_at', 'TEXT', ''), ('x', 'REAL', ''), ('y', 'REAL', ''),
    ('frame_id', 'TEXT', ''), ('risk_level', 'TEXT', ''), ('status', 'TEXT', ''),
    ('received_at', 'TEXT', ''),
], 0, 'risk_level: HIGH/MEDIUM/LOW · status 기본값 NEW', live=False)

t_evid = table('event_evidence', 800, 430, [
    ('id', 'INTEGER', 'PK'), ('event_id', 'TEXT', 'FK U'.split()[0]), ('image_path', 'TEXT', ''),
    ('captured_at', 'TEXT', ''), ('created_at', 'TEXT', ''),
], 0, 'event_id UNIQUE → 사건당 사진 1장', live=False)

t_chg = table('event_changes', 1170, 430, [
    ('id', 'INTEGER', 'PK'), ('event_id', 'TEXT', 'FK'), ('user_id', 'INTEGER', 'FK'),
    ('previous_status', 'TEXT', ''), ('new_status', 'TEXT', ''), ('memo', 'TEXT', ''),
    ('changed_at', 'TEXT', ''),
], 0, '신규→확인중→작업요청→조치완료 이력', live=False)

t_cmd = table('commands', 430, 790, [
    ('command_id', 'TEXT', 'PK'), ('robot_id', 'TEXT', 'FK'), ('event_id', 'TEXT', 'FK'),
    ('requested_by', 'INTEGER', 'FK'), ('command_type', 'TEXT', ''), ('status', 'TEXT', ''),
    ('result_message', 'TEXT', ''), ('requested_at', 'TEXT', ''), ('accepted_at', 'TEXT', ''),
    ('started_at', 'TEXT', ''), ('finished_at', 'TEXT', ''),
], 0, '요청됨→수락됨→진행중→완료/실패', live=False)

t_run = table('patrol_runs', 800, 790, [
    ('patrol_id', 'TEXT', 'PK'), ('robot_id', 'TEXT', 'FK'), ('command_id', 'TEXT', 'FK'),
    ('status', 'TEXT', ''), ('started_at', 'TEXT', ''), ('ended_at', 'TEXT', ''),
], 0, live=False)

t_visit = table('patrol_visits', 1170, 790, [
    ('id', 'INTEGER', 'PK'), ('patrol_id', 'TEXT', 'FK'), ('observation_point', 'TEXT', ''),
    ('visited_at', 'TEXT', ''), ('event_id', 'TEXT', 'FK'),
], 0, 'observation_point CHECK: P1~P7', live=False)

t_hand = table('handovers', 1540, 790, [
    ('handover_id', 'TEXT', 'PK'), ('from_robot_id', 'TEXT', 'FK'), ('to_robot_id', 'TEXT', 'FK'),
    ('reason', 'TEXT', ''), ('status', 'TEXT', ''), ('requested_at', 'TEXT', ''),
    ('completed_at', 'TEXT', ''),
], 0, 'from ≠ to 제약', live=False)


def rt(t):    # 오른쪽 변 중앙
    return (t[0] + t[2], t[1] + t[3] / 2)


def lf(t):
    return (t[0], t[1] + t[3] / 2)


def tp(t, ratio=0.5):
    return (t[0] + t[2] * ratio, t[1])


def bt(t, ratio=0.5):
    return (t[0] + t[2] * ratio, t[1] + t[3])


# robots → robot_latest_status (1:1)
arrow([rt(t_robots), (770, rt(t_robots)[1]), (800, 200)], GREEN, 2, text='1 : 1', toffset=(-13, -50))
# robots → robot_status_history (1:N)  위쪽으로 우회
arrow([tp(t_robots, 0.8), (670, 92), (1290, 92), tp(t_hist, 0.4)], GREEN, 2, text='1 : N', toffset=(-160, -20))
# robots → events
arrow([bt(t_robots, 0.35), (535, 430)], GRAY, 2, dashed=True, text='1 : N', toffset=(8, -30))
# events → event_evidence (1:1)
arrow([rt(t_events), (800, rt(t_events)[1])], GRAY, 2, dashed=True, text='1 : 1', toffset=(-14, -36))
# events → event_changes (1:N)
arrow([bt(t_events, 0.9), (700, 745), (1310, 745), bt(t_chg, 0.45)], GRAY, 2, dashed=True, text='events 1 : N', toffset=(-52, 44))
# users → event_changes (1:N)
arrow([bt(t_users, 0.5), (210, 775), (1250, 775), bt(t_chg, 0.25)], GRAY, 2, dashed=True, text='users 1 : N', toffset=(-427, 305))
# events → commands
arrow([bt(t_events, 0.35), (535, 790)], GRAY, 2, dashed=True)
# robots → commands (좌측 우회)
arrow([lf(t_robots), (395, 155), (395, 860), (430, 860)], GRAY, 2, dashed=True)
# users → commands.requested_by
arrow([bt(t_users, 0.25), (135, 905), (430, 905)], GRAY, 2, dashed=True)
# robots → patrol_runs (우측 우회)
arrow([rt(t_robots), (760, 147), (760, 840), (800, 840)], GRAY, 2, dashed=True)
# commands → patrol_runs
arrow([rt(t_cmd), (800, rt(t_cmd)[1])], GRAY, 2, dashed=True)
# patrol_runs → patrol_visits
arrow([rt(t_run), (1170, rt(t_run)[1])], GRAY, 2, dashed=True, text='1 : N', toffset=(-14, -22))
# robots → handovers (상단 우회)
arrow([tp(t_robots, 0.6), (610, 80), (1700, 80), tp(t_hand, 0.55)], GRAY, 2, dashed=True, text='robots → from / to 2개 FK', toffset=(-4, -383))

label('읽는 법: PK는 그 행을 구분하는 값, FK는 다른 표의 행을 가리키는 값, U는 같은 값이 두 번 들어올 수 없는 열이다.',
      60, 1180, 1300, 22, 13, TEXT)
label('설계 근거로 쓰는 제약: message_id UNIQUE = 같은 메시지 재수신 시 행이 중복 생기지 않음 · event_evidence.event_id UNIQUE = 사건당 증거 사진 1장 · status 기본값 NEW = 저장 즉시 신규 상태',
      60, 1206, 1800, 22, 12, MUTED)
label('robot_status_history의 1013행은 임시 HTTP API로 상태를 반복 수신하며 쌓인 실제 기록이다. 최신 1행만 화면에 쓰고 나머지는 이력으로 남긴다.',
      60, 1232, 1800, 22, 12, MUTED)
im.save(OUT / '01-erd.png')

# ════════════════════════════════════════════════════════════════
# PAGE 2 — 빈 DB → 데이터 삽입 → 화면 반영
# ════════════════════════════════════════════════════════════════
W2, H2 = 1720, 1180
page('02 빈 DB → 데이터 → 화면 반영', '02-data-flow', W2, H2)
title_bar('빈 데이터셋에서 시작해 화면에 값이 나타나기까지',
          '설계 요구사항의 "시작 → 페이지 생성, 빈 데이터셋 생성 → DB에 content 삽입 → 웹페이지 반영" 로직 · 실제 저장값 기준', W2)

steps = [
    ('1', '서버 시작 — 빈 데이터셋 생성', GREEN, [
        'CREATE TABLE IF NOT EXISTS × 11개 실행',
        '기존 데이터는 지우지 않음 (DELETE 없음)',
        '최초 실행 시 모든 테이블 0행',
    ], 'app/database.py · app/schema.sql'),
    ('2', '화면 접속 — 빈 상태 표시', GREEN, [
        'SELECT … LEFT JOIN robot_latest_status → 0행',
        '배터리 "—%", 카메라 "신호 없음(연결 대기 중)"',
        '없는 값을 0%로 표시하지 않음',
    ], 'routes/dashboard.py · templates/index.html'),
    ('3', '데이터 수신 — content 삽입 요청', ORANGE, [
        'POST /api/robots/status  (X-Robot-Token 검사)',
        '{"robot_id":"AMR1","battery":82.0,',
        ' "x":12.4,"y":8.7,"mission_status":"PATROLLING"}',
    ], 'routes/robots.py'),
    ('4', '검증 — 형식·중복·순서', ORANGE, [
        'validate_status(): 값 범위·타임존 검사',
        'message_id 같고 내용 다르면 409 충돌',
        'observed_at이 더 과거면 409 무시',
    ], 'services/robot_service.py · models/robot.py'),
    ('5', 'DB 저장 — 한 트랜잭션', BLUE, [
        'BEGIN IMMEDIATE',
        'INSERT robot_status_history  (이력 1행 추가)',
        'UPSERT robot_latest_status   (로봇당 1행 갱신)',
        'COMMIT / 실패 시 ROLLBACK',
    ], 'models/robot.py store_status()'),
    ('6', '조회 API', BLUE, [
        'GET /api/robots/status (로그인 세션 필요)',
        'JSON: battery 82.0, mission_label "순찰 중"',
        '15초 무수신이면 OFFLINE으로 판정',
    ], 'routes/robots.py · robot_service.py'),
    ('7', '웹페이지 반영', GREEN, [
        'dashboard.js 2초 폴링 → renderRobot()',
        '카드: 배터리 82% · 순찰 중 · map (12.40, 8.70)',
        '조회 실패 시 마지막 값 유지',
    ], 'static/js/dashboard.js'),
]

x, y = 60, 100
cw, chh, gap = 1180, 128, 14
for i, (num, title, color, lines, src) in enumerate(steps):
    cy = y + i * (chh + gap)
    box('', x, cy, cw, chh, PANEL, color)
    box(num, x + 14, cy + 14, 34, 34, color, color, 17, BG, bold=True)
    label(title, x + 60, cy + 12, 500, 24, 15, TEXT, bold=True)
    label(src, x + cw - 430, cy + 14, 420, 20, 11, MUTED, 'right')
    for k, ln in enumerate(lines):
        label(ln, x + 62, cy + 44 + k * 20, cw - 100, 20, 12, MUTED)
    if i < len(steps) - 1:
        arrow([(x + 60, cy + chh), (x + 60, cy + chh + gap)], color, 2)

# 우측: 화면 표시 결과
rx = 1290
box('', rx, 100, 370, 300, PANEL2, GREEN)
label('7단계 결과 — 화면 카드', rx + 14, 108, 340, 22, 14, GREEN, bold=True)
box('', rx + 16, 140, 338, 110, PANEL, BORDER)
label('로봇 1  (AMR1)', rx + 28, 148, 200, 22, 13, TEXT, bold=True)
label('● 온라인', rx + 250, 148, 90, 22, 12, GREEN, 'right')
label('배터리', rx + 28, 176, 60, 24, 12, MUTED)
label('82%', rx + 82, 172, 90, 28, 20, GREEN, bold=True)
box('', rx + 190, 180, 150, 16, '#02080f', '#9fb3c8', rounded=1, sw=1)
box('', rx + 192, 182, 123, 12, GREEN, GREEN, rounded=0)
label('순찰 중', rx + 28, 210, 100, 22, 12, TEXT)
label('map (12.40, 8.70)', rx + 190, 210, 150, 22, 12, BLUE, 'right')
label('↑ 이 값들의 출처는 robot_latest_status 1행', rx + 16, 258, 338, 20, 11, MUTED)
box('', rx + 16, 284, 338, 100, GRAY_FILL, GRAY, dashed=True)
label('이벤트 로그 (0행)', rx + 28, 292, 200, 20, 12, MUTED, bold=True)
label('표시할 이벤트가 없습니다', rx + 28, 316, 320, 20, 12, MUTED)
label('events 0행 → 빈 로그 안내가 정상 동작', rx + 28, 340, 320, 20, 11, ORANGE)

# 우측 하단: 이벤트 경로(예정)
box('', rx, 420, 370, 420, GRAY_FILL, GRAY, dashed=True)
label('이벤트 경로 (다음 단계 · 같은 구조)', rx + 14, 428, 340, 22, 14, MUTED, bold=True)
ev = ['POST /api/events + 증거 이미지',
      '검증: 형식·좌표·위험도',
      'message_id 중복 확인',
      'instance/evidence/ 에 사진 파일 저장',
      'INSERT events (status=NEW)',
      'INSERT event_evidence (경로만 저장)',
      '이벤트 로그 표 1행 추가 표시']
for k, t in enumerate(ev):
    box(t, rx + 16, 460 + k * 52, 338, 40, GRAY_FILL, GRAY, 12, MUTED, dashed=True)
    if k < len(ev) - 1:
        arrow([(rx + 40, 500 + k * 52), (rx + 40, 512 + k * 52)], GRAY, 2, dashed=True)

label('핵심: 3~5단계는 로봇 상태에서 이미 검증된 경로다. 이벤트는 같은 구조를 그대로 복제하고 파일 저장 단계만 추가한다.',
      60, 1108, 1600, 22, 13, TEXT)
label('원본 영상·이미지 바이너리는 DB에 넣지 않는다. 파일로 저장하고 DB에는 경로(image_path)만 기록한다.',
      60, 1134, 1600, 22, 12, MUTED)
im.save(OUT / '02-data-flow.png')

# ════════════════════════════════════════════════════════════════
E.indent(doc)
E.ElementTree(doc).write(OUT / 'sysmon-db-schema.drawio', encoding='utf-8', xml_declaration=True)
total = 0
for d, slug in pages:
    ids = [c.get('id') for c in d.findall('.//mxCell')]
    assert len(ids) == len(set(ids)), f'중복 ID: {slug}'
    total += len(ids)
print('OK', len(pages), 'pages,', total, 'cells')
