"""스크린샷 기반 지하주차장 로봇 관제 대시보드 draw.io 목업 생성기.
출력: parking-dashboard-mockup.drawio (draw.io 편집용) + 01-dashboard.png (미리보기)
"""
from pathlib import Path
import xml.etree.ElementTree as E
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
W, H = 1680, 940
BG = '#04101c'; TOP = '#061524'; SIDE = '#051423'; PANEL = '#0a1e30'; PANEL2 = '#0d2438'
BORDER = '#1f3a52'; TEXT = '#e6eef7'; MUTED = '#9db0c4'
BLUE = '#5cb8ff'; GREEN = '#3ddc72'; ORANGE = '#ffb020'; RED = '#e5484d'; YELLOW = '#d4a72c'
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
FONTB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'

doc = E.Element('mxfile', host='app.diagrams.net', type='device')
d = E.SubElement(doc, 'diagram', name='01 메인 대시보드', id='dashboard')
m = E.SubElement(d, 'mxGraphModel', grid='1', gridSize='10', page='1', pageWidth=str(W), pageHeight=str(H), background=BG)
root = E.SubElement(m, 'root'); E.SubElement(root, 'mxCell', id='0'); E.SubElement(root, 'mxCell', id='1', parent='0')
im = Image.new('RGB', (W, H), BG); draw = ImageDraw.Draw(im)
_n = [0]
def nid(p='n'):
    _n[0] += 1; return f'{p}{_n[0]}'

def box(t, x, y, w, h, fill=PANEL, stroke=BORDER, size=16, color=TEXT, align='center', bold=False, rounded=1, dashed=False, shape='rectangle', sw=1):
    st = (f'shape={shape};whiteSpace=wrap;html=1;rounded={rounded};arcSize=8;fillColor={fill};strokeColor={stroke};strokeWidth={sw};'
          f'fontFamily=Noto Sans CJK KR;fontSize={size};fontColor={color};align={align};verticalAlign=middle;spacing=8;'
          f'{"fontStyle=1;" if bold else ""}{"dashed=1;" if dashed else ""}')
    c = E.SubElement(root, 'mxCell', id=nid(), parent='1', vertex='1', value=t, style=st)
    E.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as': 'geometry'})
    pf = None if fill == 'none' else fill; ps = None if stroke == 'none' else stroke
    if pf or ps:
        if shape == 'ellipse': draw.ellipse((x, y, x+w, y+h), fill=pf, outline=ps, width=sw)
        else: draw.rounded_rectangle((x, y, x+w, y+h), radius=6 if rounded else 0, fill=pf, outline=ps, width=sw)
    if t:
        f = ImageFont.truetype(FONTB if bold else FONT, size, index=1)
        tt = t.replace('<br>', '\n')
        b = draw.multiline_textbbox((0, 0), tt, font=f, spacing=4)
        tx = x+8 if align == 'left' else (x+w-8-(b[2]-b[0]) if align == 'right' else x+(w-b[2]+b[0])/2)
        draw.multiline_text((tx, y+(h-b[3]+b[1])/2-b[1]), tt, font=f, fill=color, spacing=4, align=align)
    return c

def label(t, x, y, w, h, size=16, color=TEXT, align='left', bold=False, fill=None):
    return box(t, x, y, w, h, fill or 'none', 'none', size, color, align, bold, 0)

def line(points, color=BORDER, width=2, dashed=False):
    draw.line(points, fill=color, width=width)
    c = E.SubElement(root, 'mxCell', id=nid('e'), parent='1', edge='1',
                     style=f'endArrow=none;strokeColor={color};strokeWidth={width};{"dashed=1;dashPattern=6 6;" if dashed else ""}rounded=1;')
    g = E.SubElement(c, 'mxGeometry', relative='1', **{'as': 'geometry'})
    E.SubElement(g, 'mxPoint', x=str(points[0][0]), y=str(points[0][1]), **{'as': 'sourcePoint'})
    E.SubElement(g, 'mxPoint', x=str(points[-1][0]), y=str(points[-1][1]), **{'as': 'targetPoint'})
    a = E.SubElement(g, 'Array', **{'as': 'points'})
    for x, y in points[1:-1]: E.SubElement(a, 'mxPoint', x=str(x), y=str(y))

# ───────── 상단 바 ─────────
box('', 0, 0, W, 70, TOP, TOP, rounded=0)
label('≡', 30, 15, 40, 40, 30)
label('지하주차장 로봇 관제 시스템', 95, 15, 500, 40, 26, TEXT, bold=True)
label('✓ 시스템 정상', 1150, 20, 150, 30, 15, GREEN)
line([(1305, 20), (1305, 50)], BORDER)
label('◎ 2025-05-24 14:32:47', 1320, 20, 210, 30, 15, MUTED)
line([(1545, 20), (1545, 50)], BORDER)
label('◉ 관제자 ▼', 1560, 20, 110, 30, 15)

# ───────── 좌측 메뉴 ─────────
box('', 0, 70, 205, H-70, SIDE, SIDE, rounded=0)
menu = [('▣', '대시보드'), ('◉', '로봇 관리'), ('▤', '지도 모니터링'), ('▦', '이벤트 로그'), ('▲', '알림'), ('◆', '시스템 설정')]
for i, (ic, t) in enumerate(menu):
    act = i == 0
    box('', 8, 85 + i*60, 190, 50, '#0f2a44' if act else SIDE, BLUE if act else SIDE, rounded=1)
    label(ic, 20, 90 + i*60, 36, 40, 20, BLUE if act else MUTED)
    label(t, 62, 90 + i*60, 130, 40, 17, BLUE if act else TEXT, bold=act)
box('', 12, 675, 182, 240, PANEL, BORDER)
label('● 시스템 연결 상태', 22, 685, 170, 30, 14, MUTED)
label('모든 로봇 온라인', 22, 715, 170, 30, 16, GREEN)
for i, n in enumerate(['로봇 1', '로봇 2']):
    box('R'+str(i+1), 26, 775 + i*62, 32, 30, PANEL2, BORDER, 13, TEXT, bold=True)
    label(n, 66, 765 + i*62, 100, 24, 15)
    label('온라인', 66, 789 + i*62, 100, 22, 14, GREEN)
    label('▲▲', 150, 776 + i*62, 36, 30, 13, GREEN)

# ───────── 지도 패널 ─────────
MX, MY, MW, MH = 220, 85, 390, 555
box('', MX, MY, MW, MH, PANEL, BORDER)
label('지하 주차장 지도', MX+12, MY+8, 200, 34, 18, TEXT, bold=True)
label('▤  ≡', MX+MW-80, MY+8, 70, 34, 18, MUTED, 'right')
box('', MX+15, MY+50, MW-30, MH-115, '#071a2c', '#2a4a66')
label('B2', MX+30, MY+90, 50, 30, 20, MUTED)
label('B1', MX+30, MY+360, 50, 30, 20, MUTED)
# 주차칸 그리드
for r, yy in enumerate([MY+70, MY+140, MY+250, MY+320, MY+430]):
    for c, xx in enumerate(range(MX+75, MX+330, 36)):
        if (r, c) in [(0, 3), (2, 6), (4, 2)]: continue
        box('', xx, yy, 28, 44, '#0a2338', '#1e3a52', rounded=0)
# 시설 아이콘
box('WC', MX+330, MY+380, 32, 28, '#0a2338', '#33506a', 12, MUTED, rounded=0)
box('EXIT', MX+325, MY+135, 40, 28, '#12331f', GREEN, 11, GREEN, rounded=0)
box('충전', MX+300, MY+255, 36, 28, '#0f2a44', BLUE, 12, BLUE, rounded=0)
box('안전구역', MX+250, MY+470, 80, 28, '#173c34', GREEN, 12)
# 로봇 1 경로 (실선, 초록)
r1 = [(MX+140, MY+175), (MX+140, MY+240), (MX+70, MY+240), (MX+70, MY+320)]
line(r1, GREEN, 4)
box('', MX+120, MY+150, 40, 40, '#123a24', GREEN, shape='ellipse', sw=3)
label('R1', MX+120, MY+150, 40, 40, 15, GREEN, 'center', True)
box('로봇 1', MX+168, MY+155, 66, 30, '#1e7a3e', GREEN, 14, TEXT, bold=True)
# 로봇 2 경로 (점선, 주황)
r2 = [(MX+140, MY+340), (MX+140, MY+400), (MX+190, MY+400), (MX+190, MY+480), (MX+240, MY+480)]
line(r2, ORANGE, 4, dashed=True)
box('', MX+170, MY+345, 40, 40, '#3a2c10', ORANGE, shape='ellipse', sw=3)
label('R2', MX+170, MY+345, 40, 40, 15, ORANGE, 'center', True)
box('로봇 2', MX+220, MY+320, 66, 30, '#a16a14', ORANGE, 14, TEXT, bold=True)
# 범례 및 줌
box('', MX+15, MY+455, 150, 70, '#071a2c', '#2a4a66')
line([(MX+25, MY+470), (MX+50, MY+470)], GREEN, 3); label('로봇 1 경로', MX+55, MY+458, 100, 24, 12, MUTED)
line([(MX+25, MY+492), (MX+50, MY+492)], ORANGE, 3, dashed=True); label('로봇 2 경로', MX+55, MY+480, 100, 24, 12, MUTED)
box('', MX+30, MY+506, 12, 12, BLUE, BLUE, shape='ellipse'); label('충전 스테이션', MX+55, MY+500, 100, 24, 12, MUTED)
box('+', MX+MW-52, MY+MH-80, 36, 32, PANEL2, BORDER, 20)
box('−', MX+MW-52, MY+MH-48, 36, 32, PANEL2, BORDER, 20)

# ───────── 로봇 상태 카드 + 카메라 ─────────
def robot_card(x, w, name, bat, bcol, pos):
    box('', x, 85, w, 120, PANEL, BORDER)
    label(f'◉ {name}', x+12, 92, 200, 34, 18, TEXT, bold=True)
    label('● 온라인', x+w-100, 92, 90, 34, 14, GREEN, 'right')
    box('', x+12, 130, w-24, 40, PANEL2, PANEL2)
    label('배터리', x+22, 133, 70, 34, 14, MUTED)
    label(bat, x+82, 128, 100, 42, 26, bcol, bold=True)
    box('', x+w-105, 138, 80, 24, '#02080f', '#9fb3c8', rounded=1, sw=2)
    pct = int(bat.rstrip('%'))
    box('', x+w-102, 141, int(74*pct/100), 18, bcol, bcol, rounded=0)
    box('', x+w-25, 145, 5, 10, '#9fb3c8', '#9fb3c8', rounded=0)
    label('상태', x+22, 172, 40, 26, 14, MUTED); label('순찰 중', x+62, 172, 80, 26, 14, bcol)
    label('위치', x+w-150, 172, 40, 26, 14, MUTED, 'right'); label(pos, x+w-100, 172, 88, 26, 14, BLUE)

def camera(title, x, y, w, h, tag):
    box('', x, y, w, h, PANEL, BORDER)
    label(title, x+12, y+6, 260, 30, 16, TEXT, bold=True)
    label('● LIVE', x+w-90, y+6, 80, 30, 14, RED, 'right')
    box('', x+10, y+40, w-20, h-92, '#0f2233', '#2a4a66', rounded=1)
    label('실시간 영상 영역', x+10, y+h/2-40, w-20, 30, 20, MUTED, 'center')
    label('(스트림 URL 연동 자리)', x+10, y+h/2-10, w-20, 26, 13, MUTED, 'center')
    box(tag, x+22, y+52, 44, 40, '#233d54', '#3d5a74', 12, TEXT)
    label('⊕', x+14, y+h-46, 30, 34, 18, MUTED)
    label('▣    ▶    ●    ◑', x+w/2-80, y+h-46, 160, 34, 16, MUTED, 'center')
    label('◆', x+w-44, y+h-46, 30, 34, 18, MUTED, 'right')

robot_card(625, 470, '로봇 1', '82%', GREEN, 'B2-14')
robot_card(1113, 547, '로봇 2', '41%', ORANGE, 'B1-07')
camera('로봇 1 현재 카메라', 625, 212, 470, 222, 'B2<br>14')
camera('로봇 2 현재 카메라', 1113, 212, 547, 222, 'B1')
camera('고정 웹캠 1', 625, 447, 470, 205, 'B2<br>16')
camera('고정 웹캠 2', 1113, 447, 547, 205, 'B2<br>OUT')

# ───────── 이벤트 로그 ─────────
LX, LY, LW, LH = 220, 668, 1440, 245
box('', LX, LY, LW, LH, PANEL, BORDER)
label('이벤트 로그', LX+12, LY+10, 200, 36, 18, TEXT, bold=True)
box('▤  전체 기간   ▼', LX+1085, LY+10, 165, 36, PANEL2, BORDER, 14)
box('▼  필터   ▼', LX+1262, LY+10, 165, 36, PANEL2, BORDER, 14)
cols = [(LX+15, 190, '시간'), (LX+205, 260, '로봇'), (LX+465, 350, '이벤트'), (LX+815, 180, '위치'), (LX+995, 200, '위험도'), (LX+1195, 230, '상태')]
box('', LX+15, LY+55, LW-30, 40, PANEL2, PANEL2)
for x, w, t in cols: label(t, x, LY+55, w, 40, 15, MUTED, 'center')
rows = [('14:32', '로봇 1', '누수 의심 감지', 'B2-14', 68, RED, '확인 필요', TEXT),
        ('14:28', '로봇 2', '조도 기준 미달', 'B1-07', 45, YELLOW, '확인 필요', TEXT),
        ('14:16', '로봇 1', '비상구 앞 적치물', 'B2-E3', 82, RED, '조치 필요', RED)]
for i, (tm, rb, ev, loc, rk, rc, stt, sc) in enumerate(rows):
    y = LY+100 + i*46
    line([(LX+15, y+45), (LX+LW-15, y+45)], BORDER, 1)
    label(tm, cols[0][0], y, cols[0][1], 44, 15, TEXT, 'center')
    label(f'◉ {rb}  ●', cols[1][0], y, cols[1][1], 44, 15, TEXT, 'center')
    label(ev, cols[2][0], y, cols[2][1], 44, 15, TEXT, 'center')
    label(loc, cols[3][0], y, cols[3][1], 44, 15, TEXT, 'center')
    box(f'위험도 {rk}', cols[4][0]+40, y+8, 120, 28, rc, rc, 14, TEXT, bold=True)
    label(stt, cols[5][0], y, cols[5][1], 44, 15, sc, 'center')

# 하단 주석
label('UI 목업 · 영상/수치/지도는 자리 표시 예시 · draw.io에서 개별 요소 편집 가능', 220, 918, 1440, 20, 12, MUTED, 'center')

E.indent(doc)
E.ElementTree(doc).write(OUT/'parking-dashboard-mockup.drawio', encoding='utf-8', xml_declaration=True)
im.save(OUT/'01-dashboard.png')
ids = [c.get('id') for c in doc.findall('.//mxCell')]; assert len(ids) == len(set(ids))
print('OK', len(ids), 'cells')
