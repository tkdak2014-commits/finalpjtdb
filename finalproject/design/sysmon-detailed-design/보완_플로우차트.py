from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET
import re

source = Path('/home/hun/Downloads/플로우차트(15:22).drawio')
target = Path('/home/hun/finalproject/design/sysmon-detailed-design/플로우차트(15_22)_보완.drawio')

tree = ET.parse(source)
root = tree.getroot()
graph_root = root.find('.//root')

def plain(value):
    value = re.sub(r'<[^>]+>', '', value or '')
    return value.replace('&nbsp;', ' ').replace('\xa0', ' ').replace('\n', ' ').strip()

def cells(value):
    needle = plain(value)
    return [c for c in graph_root.findall('mxCell') if plain(c.get('value')) == needle]

def first(value):
    found = cells(value)
    if not found:
        raise KeyError(value)
    return found[-1]

def rename(old, new):
    first(old).set('value', new)

def add_box(cid, text, x, y, w=190, h=48, decision=False):
    style = ('shape=rhombus;perimeter=rhombusPerimeter;whiteSpace=wrap;html=1;'
             'rounded=0;fillColor=#fff2cc;strokeColor=#7f6000;fontSize=13;') if decision else (
             'rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;fontSize=13;')
    cell = ET.Element('mxCell', {'id': cid, 'value': text, 'style': style, 'vertex': '1', 'parent': '1'})
    ET.SubElement(cell, 'mxGeometry', {'x': str(x), 'y': str(y), 'width': str(w), 'height': str(h), 'as': 'geometry'})
    graph_root.append(cell)
    return cell

def add_connector(cid, x, y):
    cell = ET.Element('mxCell', {
        'id': cid, 'value': 'A',
        'style': 'ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;fontSize=14;',
        'vertex': '1', 'parent': '1'
    })
    ET.SubElement(cell, 'mxGeometry', {'x': str(x), 'y': str(y), 'width': '34', 'height': '34', 'as': 'geometry'})
    graph_root.append(cell)
    return cell

edge_no = 1000
def add_edge(src, dst, label='', extra_style=''):
    global edge_no
    edge_no += 1
    attrs = {'id': f'fix-edge-{edge_no}', 'edge': '1', 'parent': '1', 'source': src, 'target': dst,
             'style': 'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeWidth=1.5;' + extra_style}
    if label:
        attrs['value'] = label
    cell = ET.Element('mxCell', attrs)
    ET.SubElement(cell, 'mxGeometry', {'relative': '1', 'as': 'geometry'})
    graph_root.append(cell)

def label_existing_edge(source_text, target_text, label):
    source_id = first(source_text).get('id')
    target_id = first(target_text).get('id')
    for edge in graph_root.findall('mxCell'):
        if edge.get('edge') == '1' and edge.get('source') == source_id and edge.get('target') == target_id:
            edge.set('value', label)
            edge.set('style', (edge.get('style') or '') + ';rounded=0;endArrow=block;endFill=1;strokeWidth=1.5;')
            return
    raise KeyError((source_text, target_text))

# Terminology corrections, preserving all original nodes and edges.
rename('로봇(?) 증거 사진 확인', '이벤트 감지 로봇(1 또는 2)\n증거 사진 확인')
rename('로봇(?) 증거 사진 파일 저장', '이벤트 감지 로봇의\n증거 사진 파일 저장')
rename('1.서버 ,DB 초기화', '1. 서버·DB 초기화')

node = {label: first(label).get('id') for label in [
    '로그인 페이지 표시', '로그인 실패 메시지 표시', '빈 이벤트 로그 표시',
    '데이터 수신 대기', '메시지 ID·순서가 유효한가?', '오류·중복·오래된 데이터 기록',
    '로봇 상태 이력 저장', '해당 영상 연결에 성공했는가?',
    '해당 영상 영역에 최신 화면 표시', '메시지 형식이 유효한가?', '이벤트 감지 로봇의 증거 사진 파일 저장',
    'DB 저장에 성공했는가?', '이벤트 로그 한 행 표시', '이벤트 로그에 표시하지 않음',
    '재처리 대상으로 보관'
]}

# The source contains two dashboard-refresh boxes. Keep each branch connected to its own box.
state_refresh = 'PkncQJFMpK3l9RmYT8Xo-134'
video_refresh = 'PkncQJFMpK3l9RmYT8Xo-155'

# 1. Authentication and normal dashboard loop.
add_edge(node['로그인 실패 메시지 표시'], node['로그인 페이지 표시'], '재입력')
add_edge(node['로봇 상태 이력 저장'], state_refresh)
first('데이터 수신 대기').set('value', 'A. 데이터 수신 대기')
wait_note = add_box('fix-wait-note', '연결기 A → 데이터 수신 대기', 625, 515, 205, 36)
wait_note.set('style', 'rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;')
empty_a = add_connector('fix-empty-a', 465, 625)
state_error_a = add_connector('fix-state-error-a', 2035, 457)
state_done_a = add_connector('fix-state-done-a', 2495, 617)
add_edge(node['빈 이벤트 로그 표시'], empty_a.get('id'))
add_edge(node['오류·중복·오래된 데이터 기록'], state_error_a.get('id'))
add_edge(state_refresh, state_done_a.get('id'))

# 2. Video failure branch that was missing.
video_wait = add_box('fix-video-wait', '해당 영상 연결 대기\n· 단절 표시', 1940, 1045, 190, 55)
video_fail_a = add_connector('fix-video-fail-a', 2170, 1055)
video_done_a = add_connector('fix-video-done-a', 2640, 872)
add_edge(node['해당 영상 연결에 성공했는가?'], video_wait.get('id'), '아니오')
add_edge(video_wait.get('id'), video_fail_a.get('id'))
add_edge(node['해당 영상 영역에 최신 화면 표시'], video_refresh)
add_edge(video_refresh, video_done_a.get('id'))

# 3. Fire-event duplicate protection and failure recovery.
dup = add_box('fix-event-duplicate', '이미 처리한\nmessage_id인가?', 2180, 950, 145, 80, decision=True)
skip = add_box('fix-event-skip', '중복 이벤트\n행 생성 생략', 2180, 1090, 155, 48)
event_duplicate_a = add_connector('fix-event-duplicate-a', 2380, 1097)
event_invalid_a = add_connector('fix-event-invalid-a', 2225, 1267)
event_retry_a = add_connector('fix-event-retry-a', 3410, 1307)
event_valid = node['메시지 형식이 유효한가?']
photo_save = node['이벤트 감지 로봇의 증거 사진 파일 저장']

# Redirect the original valid-event path through the duplicate check.
for edge in graph_root.findall('mxCell'):
    if edge.get('edge') == '1' and edge.get('source') == event_valid and edge.get('target') == photo_save:
        edge.set('target', dup.get('id'))
add_edge(dup.get('id'), skip.get('id'), '예')
add_edge(skip.get('id'), event_duplicate_a.get('id'))
add_edge(dup.get('id'), photo_save, '아니오')
add_edge(node['이벤트 로그에 표시하지 않음'], event_invalid_a.get('id'))
add_edge(node['재처리 대상으로 보관'], event_retry_a.get('id'))

# 4. Make the log display fields explicit boxes rather than only a multiline note.
rename('발생 시각 표시]→ [화재 발생 표시]→ [발생 좌표 표시]→ [위험도 상·중·하 표시]→ [로봇1 증거 사진 한 장 표시]', '이벤트 로그 표시 항목')
show_time = add_box('fix-show-time', '발생 시각 표시', 3450, 550, 135, 42)
show_type = add_box('fix-show-type', '이벤트 종류 표시', 3620, 550, 135, 42)
show_coord = add_box('fix-show-coord', '좌표 표시', 3790, 550, 120, 42)
show_risk = add_box('fix-show-risk', '위험도 상·중·하 표시', 3945, 550, 155, 42)
show_photo = add_box('fix-show-photo', '감지 로봇(1 또는 2)\n증거 사진 표시·확대', 4140, 540, 190, 60)
event_refresh = add_box('fix-event-refresh', '이벤트 로그·대시보드 갱신', 4370, 545, 190, 50)
event_return = add_connector('fix-event-return', 4610, 553)
add_edge(node['이벤트 로그 한 행 표시'], show_time.get('id'))
add_edge(show_time.get('id'), show_type.get('id'))
add_edge(show_type.get('id'), show_coord.get('id'))
add_edge(show_coord.get('id'), show_risk.get('id'))
add_edge(show_risk.get('id'), show_photo.get('id'))
add_edge(show_photo.get('id'), event_refresh.get('id'))
add_edge(event_refresh.get('id'), event_return.get('id'))

# Put branch labels on the arrows themselves, then remove the old floating labels.
for source_text, target_text, label in [
    ('DB연결 성공?', 'DB 연결 오류 기록', '아니오'),
    ('DB연결 성공?', '외래 키 기능 활성화', '예'),
    ('필수 테이블이 존재하는가?', '초기 관리자 계정확인', '예'),
    ('필수 테이블이 존재하는가?', '→ [users 테이블 생성]→ [robots 테이블 생성]→ [robot_latest_status 테이블 생성]→ [events 테이블 생성]→ [event_evidence 테이블 생성]→ [event_changes 테이블 생성]→ [commands 테이블 생성]→ [patrol_runs 테이블 생성]→ [patrol_visits 테이블 생성]→ [handovers 테이블 생성]', '아니오'),
    ('로그인 정보가 유효한가?', '로그인 실패 메시지 표시', '아니오'),
    ('로그인 정보가 유효한가?', '사용자 세션 생성', '예'),
    ('이벤트가 존재하는가?', '빈 이벤트 로그 표시', '아니오'),
    ('이벤트가 존재하는가?', '이벤트 로그 표시', '예'),
    ('메시지 ID·순서가 유효한가?', '오류·중복·오래된 데이터 기록', '아니오'),
    ('메시지 ID·순서가 유효한가?', 'robot_latest_status DB 갱신', '예'),
    ('해당 영상 연결에 성공했는가?', '해당 영상 영역에 최신 화면 표시', '예'),
    ('메시지 형식이 유효한가?', '이벤트 오류 기록', '아니오'),
    ('메시지 형식이 유효한가?', '이미 처리한 message_id인가?', '예'),
    ('DB 저장에 성공했는가?', '저장 실패 기록', '아니오'),
    ('DB 저장에 성공했는가?', '이벤트 로그 한 행 표시', '예'),
]:
    label_existing_edge(source_text, target_text, label)

referenced = {c.get(a) for c in graph_root.findall('mxCell') for a in ('source', 'target') if c.get(a)}
for cell in list(graph_root.findall('mxCell')):
    if cell.get('vertex') == '1' and plain(cell.get('value')) in {'예', '네', '아니오', '아니요'} and cell.get('id') not in referenced:
        graph_root.remove(cell)

tree.write(target, encoding='utf-8', xml_declaration=True)
print(target)
