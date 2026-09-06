"""Sysmon 기능 플로우차트 — 현재 구현(1~10단계) 기준 갱신본.

원본 `플로우차트(15_22)_보완1111(4).drawio`의 클래식 스타일을 유지하면서
다음 세 가지를 반영한다.
  1) 수신 분기를 4개(로봇 상태·지도·영상·화재 이벤트)로 확장
  2) 이벤트 분기의 사진 저장 / DB 중복 확인 순서를 실제 코드대로 교정
  3) 관제자 처리 상태 변경과 통합 이력 검색 흐름 추가

기준 코드: sysmon/app (2026-09-06, 테스트 55개 통과)
출력: sysmon-flow-current.drawio + preview.png
"""
from pathlib import Path
import math
import xml.etree.ElementTree as E
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
FONTB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'

W, H = 2900, 2300
BG = '#ffffff'
INK = '#000000'
GRAYINK = '#555555'

# 구간별 연한 채움색 (draw.io 기본 팔레트)
C_INIT = '#f5f5f5'
C_LOGIN = '#dae8fc'
C_ROBOT = '#d5e8d4'
C_MAP = '#ffe6cc'
C_CAM = '#e1d5e7'
C_EVENT = '#f8cecc'
C_OPS = '#fff2cc'
C_HIST = '#dae8fc'
C_EXC = '#ffffff'

doc = E.Element('mxfile', host='app.diagrams.net', type='device')
diagram = E.SubElement(doc, 'diagram', name='Sysmon 기능 플로우 (현재 구현)', id='sysmon-current')
model = E.SubElement(diagram, 'mxGraphModel', grid='1', gridSize='10', guides='1', tooltips='1',
                     connect='1', arrows='1', fold='1', page='1', pageScale='1',
                     pageWidth=str(W), pageHeight=str(H), math='0', shadow='0')
root = E.SubElement(model, 'root')
E.SubElement(root, 'mxCell', id='0')
E.SubElement(root, 'mxCell', id='1', parent='0')

im = Image.new('RGB', (W, H), BG)
draw = ImageDraw.Draw(im)
_n = [0]


def nid(p='n'):
    _n[0] += 1
    return f'{p}{_n[0]}'


def _wrap(text, font, maxw):
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


def _text(t, x, y, w, h, size, color=INK, bold=False, pad=10, align='center'):
    if not t:
        return
    f = ImageFont.truetype(FONTB if bold else FONT, size, index=1)
    tt = _wrap(t.replace('<br>', '\n'), f, w - pad * 2)
    b = draw.multiline_textbbox((0, 0), tt, font=f, spacing=3)
    tx = x + pad if align == 'left' else x + (w - b[2] + b[0]) / 2
    ty = y + (h - b[3] + b[1]) / 2 - b[1]
    draw.multiline_text((tx, ty), tt, font=f, fill=color, spacing=3,
                        align='left' if align == 'left' else 'center')


SHAPES = {
    'proc': 'rounded=0;whiteSpace=wrap;html=1;',
    'dec': 'rhombus;whiteSpace=wrap;html=1;shapeInside=1;',
    'term': 'rounded=1;arcSize=50;whiteSpace=wrap;html=1;',
    'conn': 'ellipse;whiteSpace=wrap;html=1;',
    'pre': 'shape=process;whiteSpace=wrap;html=1;backgroundOutline=1;size=0.06;',
    'note': 'rounded=0;whiteSpace=wrap;html=1;dashed=1;',
}


def node(kind, t, x, y, w, h, fill='#ffffff', size=11, bold=False, color=INK, align='center'):
    style = (SHAPES[kind] + f'fillColor={fill};strokeColor={INK if kind != "note" else "#777777"};'
             f'fontFamily=Noto Sans CJK KR;fontSize={size};fontColor={color};'
             f'align={align};verticalAlign=middle;{"fontStyle=1;" if bold else ""}')
    c = E.SubElement(root, 'mxCell', id=nid(), parent='1', vertex='1', value=t, style=style)
    E.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as': 'geometry'})
    outline = INK if kind != 'note' else '#777777'
    if kind == 'dec':
        draw.polygon([(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)],
                     fill=fill, outline=outline)
    elif kind == 'conn':
        draw.ellipse((x, y, x + w, y + h), fill=fill, outline=outline)
    elif kind == 'term':
        draw.rounded_rectangle((x, y, x + w, y + h), radius=h / 2, fill=fill, outline=outline)
    elif kind == 'note':
        for xx in range(int(x), int(x + w), 10):
            draw.line((xx, y, min(xx + 5, x + w), y), fill=outline)
            draw.line((xx, y + h, min(xx + 5, x + w), y + h), fill=outline)
        for yy in range(int(y), int(y + h), 10):
            draw.line((x, yy, x, min(yy + 5, y + h)), fill=outline)
            draw.line((x + w, yy, x + w, min(yy + 5, y + h)), fill=outline)
    else:
        draw.rectangle((x, y, x + w, y + h), fill=fill, outline=outline)
        if kind == 'pre':
            draw.line((x + 14, y, x + 14, y + h), fill=outline)
            draw.line((x + w - 14, y, x + w - 14, y + h), fill=outline)
    _text(t, x, y, w, h, size, color, bold, align=align)
    return {'x': x, 'y': y, 'w': w, 'h': h, 'kind': kind}


def edge(pts, text=None, dashed=False, tside='right', tseg=None):
    style = ('edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;'
             f'endArrow=block;endFill=1;strokeWidth=1.5;strokeColor={INK};'
             f'fontFamily=Noto Sans CJK KR;fontSize=10;fontColor={INK};'
             f'{"dashed=1;" if dashed else ""}')
    c = E.SubElement(root, 'mxCell', id=nid('e'), parent='1', edge='1', value=text or '', style=style)
    g = E.SubElement(c, 'mxGeometry', relative='1', **{'as': 'geometry'})
    E.SubElement(g, 'mxPoint', x=str(pts[0][0]), y=str(pts[0][1]), **{'as': 'sourcePoint'})
    E.SubElement(g, 'mxPoint', x=str(pts[-1][0]), y=str(pts[-1][1]), **{'as': 'targetPoint'})
    arr = E.SubElement(g, 'Array', **{'as': 'points'})
    for p in pts[1:-1]:
        E.SubElement(arr, 'mxPoint', x=str(p[0]), y=str(p[1]))
    # PIL
    if dashed:
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]; x2, y2 = pts[i + 1]
            d = math.hypot(x2 - x1, y2 - y1)
            if not d:
                continue
            for k in range(int(d // 11) + 1):
                t0, t1 = k * 11 / d, min((k * 11 + 6) / d, 1)
                draw.line((x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0,
                           x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1), fill=INK)
    else:
        draw.line(pts, fill=INK, width=2)
    x2, y2 = pts[-1]; x1, y1 = pts[-2]
    a = math.atan2(y2 - y1, x2 - x1)
    draw.polygon([(x2, y2), (x2 - 9 * math.cos(a - .4), y2 - 9 * math.sin(a - .4)),
                  (x2 - 9 * math.cos(a + .4), y2 - 9 * math.sin(a + .4))], fill=INK)
    if text:
        i = tseg if tseg is not None else max(0, len(pts) // 2 - 1)
        i = min(i, len(pts) - 2)
        mx = (pts[i][0] + pts[i + 1][0]) / 2
        my = (pts[i][1] + pts[i + 1][1]) / 2
        f = ImageFont.truetype(FONT, 10, index=1)
        tw = draw.textlength(text, font=f)
        tx = mx + 5 if tside == 'right' else mx - tw - 5
        ty = my - 12
        draw.rectangle((tx - 2, ty - 1, tx + tw + 2, ty + 13), fill=BG)
        draw.text((tx, ty), text, font=f, fill=INK)


# ────────────────────────────────────────────────────────────────
# 제목
# ────────────────────────────────────────────────────────────────
_text('Sysmon 기능 플로우차트 — 현재 구현 기준 (1~10단계)', 44, 24, 1500, 34, 24, INK, True, align='left')
_text('원본 플로우차트(15_22 보완1111)를 갱신: 수신 분기 4개로 확장 · 이벤트 저장 순서 교정 · 관제 처리와 이력 검색 추가   |   '
      '기준: sysmon/app, 2026-09-06', 46, 60, 1900, 22, 12, GRAYINK, align='left')

COLW = 290
GAP = 32


def column(x, y0, steps):
    """세로 체인을 그리고 각 단계의 위치를 돌려준다."""
    out = []
    y = y0
    for st in steps:
        kind = st.get('k', 'proc')
        h = st.get('h', {'proc': 58, 'dec': 78, 'term': 44, 'conn': 44, 'pre': 58, 'note': 58}[kind])
        w = st.get('w', COLW)
        pos = node(kind, st['t'], x + (COLW - w) / 2, y, w, h, st.get('fill', '#ffffff'),
                   st.get('size', 11), st.get('bold', False))
        pos['kind'] = kind
        out.append(pos)
        y += h + GAP
    for a, b in zip(out, out[1:]):
        edge([(a['x'] + a['w'] / 2, a['y'] + a['h']), (b['x'] + b['w'] / 2, b['y'])],
             '예' if a['kind'] == 'dec' else None)
    return out


def section_title(t, x, y, w, sub=''):
    _text(t, x, y, w, 24, 14, INK, True, align='left')
    if sub:
        _text(sub, x, y + 22, w, 18, 10, GRAYINK, align='left')


def reject_rail(decisions, target, rail_x, labels=None):
    """여러 판단의 거부 경로를 하나의 세로 레일로 모아 예외 상자로 보낸다."""
    for i, d in enumerate(decisions):
        cy = d['y'] + d['h'] / 2
        lab = labels[i] if labels else '아니오'
        edge([(d['x'] + d['w'], cy), (rail_x, cy), (rail_x, target['y'] + target['h'] / 2),
              (target['x'] + target['w'], target['y'] + target['h'] / 2)], lab, tseg=0)


X1, X2, X3, X4, X5, X6 = 300, 660, 1060, 1500, 1940, 2380
TOP = 150

# ────────────────────────────────────────────────────────────────
# ① 서버·DB 초기화
# ────────────────────────────────────────────────────────────────
section_title('① 서버·DB 초기화', X1, TOP - 46, 340, 'run.py · app/__init__.py · database.py')
c1 = column(X1, TOP, [
    {'k': 'term', 't': '시작', 'fill': C_INIT, 'w': 150},
    {'t': 'Flask 서버 실행\ncreate_app()', 'fill': C_INIT},
    {'t': '저장 폴더 준비\ninstance / evidence / maps / live_frames', 'fill': C_INIT},
    {'t': 'SQLite DB 연결 (잠금 대기 5초)', 'fill': C_INIT},
    {'k': 'dec', 't': 'DB 연결 성공?', 'fill': C_INIT},
    {'t': '외래 키 활성화 · WAL 설정\nPRAGMA foreign_keys = ON', 'fill': C_INIT},
    {'t': '필수 테이블 13개 생성\nCREATE TABLE IF NOT EXISTS\n(없는 것만 생성 · 기존 데이터 보존)', 'fill': C_INIT, 'h': 72},
    {'t': '조회 인덱스 생성', 'fill': C_INIT},
    {'t': '초기 관리자 계정 확인\nhas_active_admin()', 'fill': C_INIT},
    {'t': '장치 토큰 확인\nSYSMON_ROBOT_API_KEY', 'fill': C_INIT},
    {'t': '수신 API 4개 등록\nrobots · maps · events · cameras', 'fill': C_INIT},
])
exc1 = node('proc', 'DB 연결 오류 기록\n서버 시작 중단', 30, c1[4]['y'] + 4, 230, 70, C_EXC, 10, color=GRAYINK)
edge([(c1[4]['x'], c1[4]['y'] + c1[4]['h'] / 2), (exc1['x'] + exc1['w'], exc1['y'] + exc1['h'] / 2)], '아니오', tside='left')

# 13개 테이블 목록 주석
node('note', 'users · robots · robot_latest_status · robot_status_history · maps · map_latest · '
             'events · event_evidence · event_changes · commands · patrol_runs · patrol_visits · handovers',
     X1, c1[10]['y'] + c1[10]['h'] + 40, COLW, 96, '#ffffff', 10, color=GRAYINK)

# ────────────────────────────────────────────────────────────────
# ② 로그인 → 대시보드
# ────────────────────────────────────────────────────────────────
section_title('② 로그인 → 대시보드', X2, TOP - 46, 340, 'routes/auth.py · routes/dashboard.py')
c2 = column(X2, TOP, [
    {'t': '로그인 페이지 표시\nGET /login', 'fill': C_LOGIN},
    {'t': '아이디·비밀번호 입력\nPOST /login', 'fill': C_LOGIN},
    {'t': 'users 테이블 계정 조회', 'fill': C_LOGIN},
    {'k': 'dec', 't': '비밀번호 해시 일치 ·\n활성 계정인가?', 'fill': C_LOGIN},
    {'t': '사용자 세션 생성 (8시간)\nCSRF 토큰 발급', 'fill': C_LOGIN},
    {'t': '권한 확인\nADMIN · OPERATOR · VIEWER', 'fill': C_LOGIN},
    {'t': '초기 데이터 4종 조회\nAMR 최신 상태 · 최신 지도 ·\n최근 이벤트 50건 · 카메라 4개 상태', 'fill': C_LOGIN, 'h': 72},
    {'k': 'dec', 't': '이벤트가 존재하는가?', 'fill': C_LOGIN},
    {'t': '이벤트 로그 표 렌더링', 'fill': C_LOGIN},
    {'t': '대시보드 표시', 'fill': C_LOGIN},
    {'k': 'conn', 't': 'A', 'fill': C_LOGIN, 'w': 60, 'size': 15, 'bold': True},
])
exc2 = node('proc', '로그인 실패 401 · 같은 화면에 안내\n비밀번호는 다시 표시하지 않음 → 재입력',
            X2, c2[10]['y'] + c2[10]['h'] + 40, COLW, 66, C_EXC, 10, color=GRAYINK)
edge([(c2[3]['x'] + c2[3]['w'], c2[3]['y'] + c2[3]['h'] / 2), (X2 + COLW + 80, c2[3]['y'] + c2[3]['h'] / 2),
      (X2 + COLW + 80, exc2['y'] + exc2['h'] / 2), (exc2['x'] + exc2['w'], exc2['y'] + exc2['h'] / 2)], '아니오', tseg=0)
edge([(c2[7]['x'] + c2[7]['w'], c2[7]['y'] + c2[7]['h'] / 2), (X2 + COLW + 25, c2[7]['y'] + c2[7]['h'] / 2),
      (X2 + COLW + 25, c2[9]['y'] + c2[9]['h'] / 2),
      (c2[9]['x'] + c2[9]['w'], c2[9]['y'] + c2[9]['h'] / 2)], '아니오 · 빈 로그 안내', tseg=0)
node('note', 'A = 데이터 수신 대기.\n로그아웃 상태에서도 서버 수신·저장은 계속된다.',
     X2, exc2['y'] + exc2['h'] + 30, COLW, 62, '#ffffff', 10, color=GRAYINK)

# ────────────────────────────────────────────────────────────────
# 수신 분기 헤더 (A → 새 데이터 수신 → 토큰 → 종류 분기)
# ────────────────────────────────────────────────────────────────
HY = TOP - 40
hconn = node('conn', 'A', X3, HY, 60, 44, '#ffffff', 15, True)
hrecv = node('proc', '새 데이터 수신', X3 + 100, HY - 6, 200, 56, '#ffffff')
htok = node('dec', '장치 토큰\nX-Robot-Token 유효?', X3 + 340, HY - 18, 230, 78, '#ffffff', 10)
hkind = node('dec', '수신 데이터 종류는?', X3 + 620, HY - 18, 230, 78, '#ffffff', 11)
edge([(hconn['x'] + hconn['w'], HY + 22), (hrecv['x'], HY + 22)])
edge([(hrecv['x'] + hrecv['w'], HY + 22), (htok['x'], HY + 22)])
edge([(htok['x'] + htok['w'], HY + 22), (hkind['x'], HY + 22)], '예')
htokfail = node('proc', '401 거부 · 기록 후 A', X3 + 355, HY + 96, 200, 44, C_EXC, 10, color=GRAYINK)
edge([(htok['x'] + htok['w'] / 2, htok['y'] + htok['h']), (htokfail['x'] + htokfail['w'] / 2, htokfail['y'])], '아니오')

BY = TOP + 210   # 분기 컬럼 시작 y
for cx, lab in ((X3, '로봇 상태'), (X4, '지도'), (X5, '영상'), (X6, '화재 이벤트')):
    edge([(hkind['x'] + hkind['w'] / 2, hkind['y'] + hkind['h']),
          (hkind['x'] + hkind['w'] / 2, BY - 46), (cx + COLW / 2, BY - 46), (cx + COLW / 2, BY)], lab, tseg=1)

# ────────────────────────────────────────────────────────────────
# ③ 로봇 상태 수신
# ────────────────────────────────────────────────────────────────
section_title('③ 로봇 상태 수신', X3, BY - 100, 340, 'routes/robots.py · models/robot.py')
c3 = column(X3, BY, [
    {'t': 'POST /api/robots/status (JSON)', 'fill': C_ROBOT},
    {'t': 'robot_id · 배터리 · 좌표 ·\n임무 상태 · observed_at 확인', 'fill': C_ROBOT},
    {'k': 'dec', 't': '형식·범위가 유효한가?', 'fill': C_ROBOT},
    {'k': 'dec', 't': '이미 받은 message_id인가?', 'fill': C_ROBOT, 'size': 10},
    {'k': 'dec', 't': 'observed_at이\n저장값보다 최신인가?', 'fill': C_ROBOT, 'size': 10},
    {'k': 'pre', 't': 'BEGIN IMMEDIATE\nrobot_status_history INSERT\nrobot_latest_status UPSERT\nCOMMIT (실패 시 ROLLBACK)',
     'fill': C_ROBOT, 'h': 82},
    {'t': 'GET /api/robots/status\n2초 폴링', 'fill': C_ROBOT},
    {'t': '배터리·임무·연결 상태 표시\n(15초 무수신 → OFFLINE)', 'fill': C_ROBOT},
    {'k': 'conn', 't': 'A', 'fill': '#ffffff', 'w': 60, 'size': 15, 'bold': True},
])
exc3 = node('proc', '거부·중복 기록 후 A\n형식 400 · 내용 다른 중복 409\n오래된 상태 409 · 같은 내용 재전송 200',
            X3, c3[8]['y'] + c3[8]['h'] + 40, COLW, 76, C_EXC, 10, color=GRAYINK)
reject_rail([c3[2], c3[3], c3[4]], exc3, X3 + COLW + 46, ['아니오', '예', '아니오'])

# ────────────────────────────────────────────────────────────────
# ④ 지도 수신 [신규]
# ────────────────────────────────────────────────────────────────
section_title('④ 지도 수신  [신규]', X4, BY - 100, 340, 'routes/maps.py · 원본 플로우차트에 없던 분기')
c4 = column(X4, BY, [
    {'t': 'POST /api/maps\n(OccupancyGrid 내부 형식)', 'fill': C_MAP},
    {'t': 'resolution · width · height ·\norigin · frame_id 확인', 'fill': C_MAP},
    {'k': 'dec', 't': '형식·크기가 유효한가?\n(최대 100만 셀)', 'fill': C_MAP, 'size': 10},
    {'t': '점유 격자 → PNG 변환\n지도 이미지 파일 저장', 'fill': C_MAP},
    {'k': 'pre', 't': 'maps INSERT +\nmap_latest 갱신 (한 트랜잭션)', 'fill': C_MAP},
    {'t': '지도 이미지 · 로봇 위치 ·\n최근 이동 경로 표시', 'fill': C_MAP},
    {'k': 'conn', 't': 'A', 'fill': '#ffffff', 'w': 60, 'size': 15, 'bold': True},
])
exc4 = node('proc', '거부 기록 후 A\n형식 400 · 같은 지도 재수신 200\n저장 실패 500',
            X4, c4[6]['y'] + c4[6]['h'] + 40, COLW, 76, C_EXC, 10, color=GRAYINK)
reject_rail([c4[2]], exc4, X4 + COLW + 46)

# ────────────────────────────────────────────────────────────────
# ⑤ 영상 프레임 수신
# ────────────────────────────────────────────────────────────────
section_title('⑤ 영상 프레임 수신', X5, BY - 100, 340, 'routes/cameras.py · 스트림이 아니라 프레임 교체 방식')
c5 = column(X5, BY, [
    {'t': 'POST /api/cameras/{id}/frame', 'fill': C_CAM},
    {'t': 'camera_id 확인\nAMR1 · AMR2 · 고정 웹캠 1 · 2', 'fill': C_CAM},
    {'k': 'dec', 't': 'PNG·JPEG이고\n2MB 이하인가?', 'fill': C_CAM, 'size': 10},
    {'k': 'dec', 't': 'captured_at이 최신인가?', 'fill': C_CAM, 'size': 10},
    {'t': '최신 프레임 파일 원자적 교체\n(누적 저장하지 않음)', 'fill': C_CAM},
    {'t': '카메라 상태 판정 (5초 기준)\nLIVE / 연결 끊김 / 수신 대기', 'fill': C_CAM},
    {'t': '해당 영상 영역만 갱신', 'fill': C_CAM},
    {'k': 'conn', 't': 'A', 'fill': '#ffffff', 'w': 60, 'size': 15, 'bold': True},
])
exc5 = node('proc', '거부 기록 후 A\n형식 400·415 · frame_id 충돌 409\n오래된 프레임 409',
            X5, c5[7]['y'] + c5[7]['h'] + 40, COLW, 76, C_EXC, 10, color=GRAYINK)
reject_rail([c5[2], c5[3]], exc5, X5 + COLW + 46, ['아니오', '아니오'])

# ────────────────────────────────────────────────────────────────
# ⑥ 화재 이벤트 수신 [순서 교정]
# ────────────────────────────────────────────────────────────────
section_title('⑥ 화재 이벤트 수신  [순서 교정]', X6, BY - 100, 400,
              'routes/events.py · 사진 파일 저장이 DB 중복 확인보다 먼저다')
c6 = column(X6, BY, [
    {'t': 'POST /api/events (multipart)\nmetadata + 증거 이미지 1장', 'fill': C_EVENT},
    {'t': 'event_id · message_id · 발생 시각 ·\n좌표 · 위험도 · 감지 로봇 확인', 'fill': C_EVENT},
    {'k': 'dec', 't': '메타데이터 형식이 유효한가?', 'fill': C_EVENT, 'size': 10},
    {'k': 'dec', 't': '실제 PNG·JPEG이고\n5MB 이하인가? (매직바이트)', 'fill': C_EVENT, 'size': 10},
    {'t': '내용 해시로 파일명 생성\nevent-{id}-{hash}.png', 'fill': C_EVENT},
    {'t': '임시 파일 기록 → 원자적 이름 변경\n(같은 파일이 있으면 저장 생략)', 'fill': C_EVENT},
    {'k': 'pre', 't': 'BEGIN IMMEDIATE\nevent_id · message_id 조회', 'fill': C_EVENT},
    {'k': 'dec', 't': '이미 처리한 이벤트인가?', 'fill': C_EVENT, 'size': 10},
    {'k': 'pre', 't': 'events INSERT (status = NEW)\n+ event_evidence INSERT (경로만)\nCOMMIT', 'fill': C_EVENT, 'h': 72},
    {'k': 'dec', 't': 'DB 저장에 성공했는가?', 'fill': C_EVENT, 'size': 10},
    {'t': '이벤트 로그 한 행 추가\n발생시각·이벤트·감지로봇·좌표·\n위험도·처리상태·증거이미지', 'fill': C_EVENT, 'h': 72},
    {'k': 'conn', 't': 'A', 'fill': '#ffffff', 'w': 60, 'size': 15, 'bold': True},
])
exc6 = node('proc', '거부·실패 기록 후 A\n형식 400 · 이미지 400 · 내용 다른 중복 409\n'
                    'ROLLBACK + 이번에 만든 파일 삭제 · 500 (로봇 재시도)',
            X6, c6[11]['y'] + c6[11]['h'] + 40, COLW, 86, C_EXC, 10, color=GRAYINK)
reject_rail([c6[2], c6[3], c6[7], c6[9]], exc6, X6 + COLW + 46, ['아니오', '아니오', '예', '아니오'])
node('note', '원본과 다른 점: 원본은 "중복 확인 → 사진 저장" 이지만\n'
             '실제 코드는 "사진 저장 → DB 중복 확인" 이다.\n'
             '파일명이 내용 해시라 중복 파일은 생기지 않는다.',
     X6, exc6['y'] + exc6['h'] + 24, COLW, 74, '#ffffff', 10, color=GRAYINK)

# ────────────────────────────────────────────────────────────────
# ⑦ 관제자 이벤트 처리 [신규] — 가로 배치
# ────────────────────────────────────────────────────────────────
OY = 1810
section_title('⑦ 관제자 이벤트 처리  [신규]', X1, OY - 40, 700,
              'routes/events.py change_status · 원본 플로우차트에 없던 흐름')
ops = []
ox = X1
specs = [
    ('proc', '이벤트 행 선택', 200, 58),
    ('proc', '상세 열기\n증거 이미지 확대 · 처리 이력', 240, 58),
    ('dec', '권한이 ADMIN ·\nOPERATOR인가?', 220, 78),
    ('proc', '처리 상태 변경 요청\n+ 메모 (500자 이하)', 220, 58),
    ('dec', '순차 전이인가?\n신규→확인중→작업요청→조치완료', 280, 82),
    ('pre', 'events.status UPDATE +\nevent_changes INSERT\n(한 트랜잭션)', 240, 72),
    ('proc', '목록·상세 갱신', 180, 58),
]
for kind, t, w, h in specs:
    ops.append(node(kind, t, ox, OY + (82 - h) / 2, w, h, C_OPS, 10 if kind == 'dec' else 11))
    ox += w + 60
for a, b in zip(ops, ops[1:]):
    edge([(a['x'] + a['w'], a['y'] + a['h'] / 2), (b['x'], b['y'] + b['h'] / 2)],
         '예' if a['kind'] == 'dec' else None)
edge([(ops[2]['x'] + ops[2]['w'] / 2, ops[2]['y'] + ops[2]['h']),
      (ops[2]['x'] + ops[2]['w'] / 2, OY + 130)], '아니오')
node('proc', 'VIEWER는 조회만', ops[2]['x'] - 20, OY + 130, 200, 44, C_EXC, 10, color=GRAYINK)
edge([(ops[4]['x'] + ops[4]['w'] / 2, ops[4]['y'] + ops[4]['h']),
      (ops[4]['x'] + ops[4]['w'] / 2, OY + 130)], '아니오')
node('proc', '409 · 현재 상태 유지', ops[4]['x'] - 10, OY + 130, 200, 44, C_EXC, 10, color=GRAYINK)
node('note', '시스템 모니터는 로봇 운영 명령(순찰 시작·복귀·대피)을 발행하지 않는다. 상태 변경은 DB 관제 기록이다.',
     ops[6]['x'] + ops[6]['w'] + 60, OY + 4, 380, 74, '#ffffff', 10, color=GRAYINK)

# ────────────────────────────────────────────────────────────────
# ⑧ 통합 이력 검색 [신규] — 가로 배치
# ────────────────────────────────────────────────────────────────
HY2 = 2090
section_title('⑧ 통합 이력 검색  [신규]', X1, HY2 - 40, 700, 'routes/history.py · 10단계')
hx = X1
hist = []
for t, w in [('/history 페이지', 200),
             ('조건 입력\n기간 · 유형 · 로봇 · 처리 상태', 240),
             ('5개 테이블 공통 열 SELECT + UNION\nevents · event_changes ·\nrobot_status_history · patrol_runs · handovers', 330),
             ('시간순 페이지 조회', 200),
             ('결과 표 표시', 180)]:
    hist.append(node('proc', t, hx, HY2, w, 76, C_HIST, 10))
    hx += w + 60
for a, b in zip(hist, hist[1:]):
    edge([(a['x'] + a['w'], a['y'] + a['h'] / 2), (b['x'], b['y'] + b['h'] / 2)])
node('note', 'commands 테이블과 일반 카메라 영상은 검색 대상이 아니다.\n'
             '시스템 모니터가 명령을 생성하지 않고 일반 영상은 보존하지 않기 때문이다.',
     hx + 20, HY2, 380, 76, '#ffffff', 10, color=GRAYINK)

# ────────────────────────────────────────────────────────────────
# 범례
# ────────────────────────────────────────────────────────────────
LX, LY = X3, 1380
node('proc', '', LX, LY, 700, 300, '#fbfbfb', 11)
_text('범례 · 원본 플로우차트에서 바뀐 점', LX + 16, LY + 10, 660, 24, 13, INK, True, align='left')
legend_shapes = [('term', '시작 / 끝'), ('proc', '처리'), ('dec', '판단'), ('pre', '트랜잭션'), ('conn', 'A')]
sx = LX + 20
for kind, name in legend_shapes:
    node(kind, '' if kind != 'conn' else 'A', sx, LY + 44, 46, 30 if kind != 'conn' else 30, '#eeeeee', 9)
    _text(name, sx, LY + 78, 46, 16, 9, GRAYINK)
    sx += 74
_text('A = 데이터 수신 대기 (긴 복귀선 대신 연결자 사용)', LX + 400, LY + 50, 290, 20, 10, GRAYINK, align='left')
changes = [
    '1. 수신 분기를 3개 → 4개로 확장했다. 지도(④)가 새로 들어간다.',
    '2. 이벤트 분기의 순서를 교정했다. 사진 파일 저장이 DB 중복 확인보다 먼저 실행된다.',
    '3. 관제자 처리 상태 변경(⑦)과 통합 이력 검색(⑧)을 추가했다.',
    '4. 생성 테이블이 10개 → 13개다. robot_status_history · maps · map_latest가 빠져 있었다.',
    '5. 모든 수신 API에 장치 토큰(X-Robot-Token) 검사가 있다.',
    '6. 영상은 연결 성공/실패 2분기가 아니라 LIVE / 연결 끊김 / 수신 대기 3상태다.',
    '7. 원본의 "재처리 대상으로 보관"은 구현되지 않았다. 실패 시 롤백 후 로봇이 재시도한다.',
]
for i, t in enumerate(changes):
    _text(t, LX + 20, LY + 106 + i * 26, 660, 22, 11, INK, align='left')

E.indent(doc)
E.ElementTree(doc).write(OUT / 'sysmon-flow-current.drawio', encoding='utf-8', xml_declaration=True)
im.save(OUT / 'preview.png')
ids = [c.get('id') for c in doc.findall('.//mxCell')]
assert len(ids) == len(set(ids)), '중복 ID'
print('OK cells:', len(ids))
