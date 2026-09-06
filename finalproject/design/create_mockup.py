from pathlib import Path
import xml.etree.ElementTree as E
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
doc = E.Element('mxfile', host='app.diagrams.net', type='device')
font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
pages = []

def page(name, w, h):
    global root, items
    diagram = E.SubElement(doc, 'diagram', id=f'page-{len(pages)+1}', name=name)
    model = E.SubElement(diagram, 'mxGraphModel', dx='1400', dy='900', grid='1', gridSize='10', page='1', pageScale='1', pageWidth=str(w), pageHeight=str(h), background='#ffffff')
    root = E.SubElement(model, 'root')
    E.SubElement(root, 'mxCell', id='0')
    E.SubElement(root, 'mxCell', id='1', parent='0')
    items = []
    pages.append((name, w, h, items))

def box(text, x, y, w, h, fill='#ffffff', size=16, align='center', kind='box'):
    id = str(len(root))
    style = f'whiteSpace=wrap;html=0;rounded=0;fillColor={fill};strokeColor=#526173;fontColor=#172434;fontFamily=Noto Sans CJK KR;fontSize={size};align={align};verticalAlign=middle;spacing=10;'
    if kind == 'text': style += 'strokeColor=none;fillColor=none;'
    if kind == 'db': style += 'shape=cylinder;boundedLbl=1;'
    if kind == 'decision': style += 'rhombus;'
    cell = E.SubElement(root, 'mxCell', id=id, value=text, style=style, vertex='1', parent='1')
    E.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as':'geometry'})
    items.append(('box', text, x,y,w,h,fill,size,align,kind))
    return id

def edge(a,b,label=''):
    cell=E.SubElement(root,'mxCell',id=str(len(root)),value=label,style='edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;endArrow=block;strokeColor=#526173;fontSize=14;labelBackgroundColor=#ffffff;',edge='1',parent='1',source=a,target=b)
    E.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'})

def frame(title,x,y):
    box('',x,y,760,550)
    box(title,x,y,760,42,'#eaf0f6',19,'left')

def nav(x,y,db=False):
    box('지하주차장 안전 관제',x+20,y+53,370,34,size=18,align='left',kind='text')
    box('관리자 | 로그아웃',x+555,y+53,185,34,size=14)
    box('Camera',x+20,y+98,105,34,'#ffffff' if db else '#dce9f5')
    box('DB',x+125,y+98,105,34,'#dce9f5' if db else '#ffffff')

page('01 UI 목업',1660,1310)
box('SYSMON · 지하주차장 관제 UI 목업',40,15,1580,45,size=28,align='left',kind='text')
box('설계 초안 | 영상 2개 기준 · 표시 값은 시연 예시 · 순찰 상태 모니터링 중심',40,65,1580,30,size=16,align='left',kind='text')
frame('01  로그인',40,120)
box('지하주차장 안전 관제',200,215,440,55,size=25,kind='text')
box('관리자 로그인',240,285,360,35,size=19,kind='text')
box('아이디',210,345,100,42,kind='text')
box('admin',320,345,285,42,align='left')
box('비밀번호',210,405,100,42,kind='text')
box('● ● ● ● ● ● ● ●',320,405,285,42,align='left')
box('로그인',235,475,370,45,'#dce9f5',18)
box('실패 시: 아이디 또는 비밀번호를 확인해 주세요.',160,540,520,40,'#fff3ed',15)
box('성공 → Camera 관제 화면',200,602,440,35,size=15,kind='text')

def camera(x,y,live):
    frame('03  Camera · 데이터 수신 후' if live else '02  Camera · 초기 / 연결 대기',x,y)
    nav(x,y)
    box('연결: 정상     배터리: 78%     순찰 상태: 순찰 중' if live else '연결: 대기     배터리: —     순찰 상태: 알 수 없음',x+20,y+148,720,42,'#edf5ef' if live else '#f3f5f7',16)
    box('카메라 1 · 전방 영상' if live else '카메라 1\n신호 없음 (연결 대기 중)',x+20,y+208,350,175,'#f3f5f7')
    box('카메라 2 · 보조 영상' if live else '카메라 2\n신호 없음 (연결 대기 중)',x+390,y+208,350,175,'#f3f5f7')
    if live:
        box('누수 의심 영역',x+105,y+265,180,55,'#fff3ed',15)
        box('※ 영상 자리 표시용 목업',x+410,y+318,310,32,size=13,kind='text')
    box('최근 감지 이벤트',x+20,y+397,720,32,size=17,align='left',kind='text')
    box('시간          위치          유형          위험 등급          확인 상태',x+20,y+435,720,32,'#eaf0f6',14)
    box('14:32        B구역       누수 의심          주의             미확인' if live else '감지 이벤트가 없습니다.',x+20,y+467,720,38,size=14)
    box('행 선택 → DB 탭에서 상세 확인' if live else '이벤트 0건 | 새 데이터 수신 시 목록 갱신',x+20,y+511,720,27,size=13,align='left',kind='text')

camera(860,120,False)
camera(40,720,True)
frame('04  DB · 이벤트 조회 / 상세 확인',860,720)
nav(860,720,True)
box('날짜: 전체 ▼     유형: 전체 ▼     상태: 전체 ▼',880,868,600,38,size=14,align='left')
box('조회',1490,868,110,38,'#dce9f5',15)
box('감지 이벤트 목록',880,923,365,35,'#eaf0f6')
box('ID     시간     위치     유형     상태',880,958,365,35,'#f3f5f7',13)
box('101   14:32   B구역   누수   미확인',880,993,365,42,'#dce9f5',13)
box('선택한 이벤트의 상세 정보 →',880,1060,365,40,size=14,kind='text')
box('검색 결과 1건',880,1178,365,30,size=14,kind='text')
box('근거 이미지 미리보기\n(event_101.jpg)',1265,923,335,150,'#f3f5f7',16)
box('이벤트 ID: 101\n감지 시간: 2026-09-05 14:32\n위치: B구역 / 좌표 (12.4, 8.1)\n유형: 누수 의심 · 위험 등급: 주의',1265,1083,335,105,size=13,align='left')
box('확인 처리',1265,1203,335,38,'#dce9f5',15)

page('02 동작 흐름',1300,1130)
box('SYSMON · 시작부터 DB 저장 및 화면 반영까지',40,20,1200,50,size=26,align='left',kind='text')
labels=[('시작',480,100),('웹 서버 시작 / 페이지 구성 준비\nDB 테이블 준비 (기존 데이터 보존)',480,200),('시연 초기 상태: 이벤트 0건\n관리자 계정은 사전 준비',480,310),('로그인 페이지 표시 / 계정 입력',480,420),('인증 성공?',480,530),('관제 페이지 생성·표시 / DB 조회\n초기 목록: 감지 이벤트 없음',480,650),('수신 데이터 검증 → 이벤트 DB 저장',480,800),('최신 이벤트 전달 → 웹 목록 갱신',480,920),('DB 탭 → 행 선택 → 상세 조회\n확인 처리 → DB 상태 갱신 → 화면 반영',480,1030)]
ids=[]
for i,(t,x,y) in enumerate(labels): ids.append(box(t,x,y,410,65,'#eaf0f6' if i in [0,4] else '#ffffff',16))
for a,b in zip(ids,ids[1:]): edge(a,b,'성공' if a==ids[4] else '')
fail=box('오류 메시지 표시',100,530,260,65,'#fff3ed')
edge(ids[4],fail,'실패');edge(fail,ids[3],'재입력')
source=box('로봇 감지 데이터 수신\n또는 시연 데이터 입력',40,800,330,65,'#edf5ef')
edge(source,ids[6],'시간·위치·유형·이미지 등')
bad=box('검증 실패: 저장 제외\n오류 기록',960,800,280,65,'#fff3ed')
edge(ids[6],bad,'유효하지 않은 데이터')
box('설계 제안: 웹은 서버 API를 통해 DB 조회·갱신\n화면 갱신 방식(주기 조회 / 실시간 알림)은 구현 시 확정',930,920,330,110,'#f3f5f7',14)

page('03 DB 테이블 초안',1420,930)
box('SYSMON · DB 테이블 구조 초안',40,20,1300,50,size=26,align='left',kind='text')
box('PK: 기본 키 / FK: 참조 키 | 계정 인증, 최신 로봇 상태, 감지 이벤트 저장',40,80,1320,40,size=17,align='left',kind='text')
tables=[('users · 관리자 계정',40,170,390,[('user_id','INTEGER · PK'),('username','VARCHAR · UNIQUE'),('password_hash','VARCHAR'),('created_at','DATETIME')]),('robots · 로봇 최신 상태',500,170,390,[('robot_id','INTEGER · PK'),('robot_name','VARCHAR'),('battery_pct','INTEGER · NULL 허용'),('patrol_status','VARCHAR'),('last_seen_at','DATETIME · NULL 허용')]),('events · 감지 이벤트',960,170,420,[('event_id','INTEGER · PK'),('robot_id','INTEGER · FK → robots'),('detected_at','DATETIME'),('event_type','VARCHAR'),('location_label','VARCHAR'),('position_x / position_y','REAL · 지도 좌표'),('image_path','VARCHAR'),('measurement_json','JSON · 측정값'),('severity','VARCHAR'),('status','VARCHAR · 기본: 미확인'),('reviewed_by','INTEGER · FK → users · NULL'),('reviewed_at','DATETIME · NULL')])]
for title,x,y,w,fields in tables:
    box(title,x,y,w,48,'#eaf0f6',18)
    for j,(name,typ) in enumerate(fields):
        box(name+'\n'+typ,x,y+48+j*45,w,45,'#ffffff' if j%2 else '#f3f5f7',13,'left')
box('관계\nrobots 1 : N events — 로봇별 감지 이력\nusers 1 : N events — 관리자가 확인한 이벤트',40,560,850,110,'#edf5ef',18,'left')
box('화면 연결\n로그인 → users 조회 / 비밀번호 해시 검증\nCamera → robots 최신 상태 + events 최근 목록\nDB 탭 → events 검색 / 상세 조회 / 확인 상태 갱신',40,700,850,145,'#f3f5f7',18,'left')
box('연결 상태는 last_seen_at 기준으로 판단 (시간 기준 추후 확정).\n실시간 영상은 스트림으로 표시하고, 이벤트 근거 이미지 경로를 DB에 저장.\n초기 이벤트 0건은 시연 조건이며 서버 시작 시 DB를 삭제하지 않음.',960,790,420,110,'#fff3ed',13,'left')

E.indent(doc)
E.ElementTree(doc).write(OUT/'sysmon-ui-mockup.drawio',encoding='utf-8',xml_declaration=True)

# Raster preview uses the same coordinates and labels as the editable UI page.
name,w,h,items=pages[0]
im=Image.new('RGB',(w,h),'white'); draw=ImageDraw.Draw(im)
for _,text,x,y,bw,bh,fill,size,align,kind in items:
    if kind!='text': draw.rectangle((x,y,x+bw,y+bh),fill=fill,outline='#526173',width=1)
    font=ImageFont.truetype(font_path,size,index=1)
    bounds=draw.multiline_textbbox((0,0),text,font=font,spacing=5)
    tw,th=bounds[2]-bounds[0],bounds[3]-bounds[1]
    tx=x+10 if align=='left' else x+(bw-tw)/2
    draw.multiline_text((tx,y+(bh-th)/2-bounds[1]),text,font=font,fill='#172434',spacing=5,align=align)
im.save(OUT/'sysmon-ui-mockup-preview.png')
print('Saved editable draw.io document (3 pages) and UI preview.')
