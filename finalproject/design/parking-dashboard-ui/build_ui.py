from pathlib import Path
import copy, math, xml.etree.ElementTree as E
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).parent
W,H=1680,1040
BG='#041321';PANEL='#0a2033';BORDER='#294156';TEXT='#e4edf5';MUTED='#a2b4c6';BLUE='#57b3ff';GREEN='#54d577';ORANGE='#ffc25a'
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
doc=E.Element('mxfile',host='app.diagrams.net',type='device')
pages=[]
def page(title,slug):
 global root,im,draw
 d=E.SubElement(doc,'diagram',name=title,id=slug)
 m=E.SubElement(d,'mxGraphModel',grid='1',gridSize='10',page='1',pageWidth=str(W),pageHeight=str(H),background=BG)
 root=E.SubElement(m,'root');E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0')
 im=Image.new('RGB',(W,H),BG);draw=ImageDraw.Draw(im)
 pages.append((d,slug))
 box('',0,0,W,H,BG,BG)
def box(t,x,y,w,h,fill=PANEL,stroke=BORDER,size=18,color=TEXT,left=False,shape='rectangle'):
 c=E.SubElement(root,'mxCell',id='n'+str(len(root)),parent='1',vertex='1',value=t,style=f'shape={shape};whiteSpace=wrap;html=0;rounded=0;fillColor={fill};strokeColor={stroke};fontFamily=Noto Sans CJK KR;fontSize={size};fontColor={color};align={"left" if left else "center"};spacing=12;')
 E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
 if shape=='ellipse':draw.ellipse((x,y,x+w,y+h),fill=fill,outline=stroke)
 else:draw.rectangle((x,y,x+w,y+h),fill=fill,outline=stroke)
 f=ImageFont.truetype(FONT,size,index=1)
 b=draw.multiline_textbbox((0,0),t,font=f,spacing=5)
 tx=x+12 if left else x+(w-b[2]+b[0])/2
 draw.multiline_text((tx,y+(h-b[3]+b[1])/2-b[1]),t,font=f,fill=color,spacing=5,align='left' if left else 'center')
 return c
def label(t,x,y,w,h,size=18,color=TEXT,fill=PANEL,left=True):
 return box(t,x,y,w,h,fill,fill,size,color,left)
def line(points,color=BORDER,width=2):
 draw.line(points,fill=color,width=width)
 c=E.SubElement(root,'mxCell',id='e'+str(len(root)),parent='1',edge='1',style=f'endArrow=none;strokeColor={color};strokeWidth={width};')
 g=E.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
 E.SubElement(g,'mxPoint',x=str(points[0][0]),y=str(points[0][1]),**{'as':'sourcePoint'})
 E.SubElement(g,'mxPoint',x=str(points[-1][0]),y=str(points[-1][1]),**{'as':'targetPoint'})
 a=E.SubElement(g,'Array',**{'as':'points'})
 for x,y in points[1:-1]:E.SubElement(a,'mxPoint',x=str(x),y=str(y))
def shell(active='대시보드'):
 box('지하주차장 로봇 관제 시스템',0,0,1680,70,'#06101b',BORDER,27,left=True)
 label('시스템 정상',1110,20,150,35,16,GREEN,'#06101b')
 label('시연 데이터',1280,20,150,35,16,ORANGE,'#06101b')
 label('관리자  |  로그아웃',1440,20,220,35,16,TEXT,'#06101b')
 box('',0,70,205,970,'#051625')
 for i,t in enumerate(['대시보드','로봇 관리','지도 모니터링','이벤트 로그','이력 조회','사용자·권한']):
  box(t,10,92+i*65,185,48,'#12314b' if t==active else '#051625','#12314b' if t==active else '#051625',20,BLUE if t==active else TEXT,True)
 box('시스템 연결 상태\n\nAMR1  온라인\n\nAMR2  온라인',12,760,181,230,PANEL,BORDER,17,GREEN)
def camera(title,x,y,w,h):
 box('',x,y,w,h)
 label(title,x+10,y+5,w-110,34,17)
 label('● LIVE',x+w-100,y+5,90,34,14,'#ff786e')
 # Editable schematic placeholders, not fabricated live photographs.
 box('',x+12,y+45,w-24,h-60,'#112a3a','#385264')
 label('실시간 영상 영역',x+70,y+80,w-140,40,22,MUTED,'#112a3a',False)
 label('연동 전: 연결 대기 표시',x+70,y+123,w-140,28,14,MUTED,'#112a3a',False)
def save(slug):im.save(OUT/(slug+'.png'))

page('01 메인 대시보드','01-dashboard')
shell()
box('',220,90,395,590)
label('지하 주차장 지도',230,98,370,40,21)
box('',240,152,355,420,'#071a29','#466076')
# Parking-space grid beneath illustrative route.
for xx in range(260,580,40):
 for yy in [172,220,465,510]: box('',xx,yy,28,30,'#0b2335','#243e52')
route=[(275,280),(400,280),(540,280),(540,370),(400,370),(275,370),(275,440)]
line(route,GREEN,4)
for i,(xx,yy) in enumerate(route):box('P'+str(i+1),xx-19,yy-16,38,32,'#193b46',GREEN,13)
box('R1',338,264,44,34,'#183c2a',GREEN,14,GREEN)
box('R2',450,353,44,34,'#3b3020',ORANGE,14,ORANGE)
box('E1',520,310,44,32,'#512420','#ff786e',14,'#ffb3ad')
box('안전구역',335,416,100,42,'#173c34',GREEN,14)
box('도크',455,465,90,40,'#18354e',BLUE,15)
label('실제 지도·좌표 확정 전 배치 예시',248,536,330,25,13,MUTED,'#071a29',False)
label('P1~P7 관측점  /  녹색 선: 순찰 경로\nR1·R2: 로봇  /  E1: 화재 이벤트',235,590,365,64,15,MUTED)
for x,name,battery,state,pos in [(630,'AMR1','82%','순찰 중','P3 인근'),(1150,'AMR2','41%','대기','도크 인근')]:
 box('',x,90,510,105)
 label(name,x+12,98,160,35,22)
 label('● 온라인',x+382,99,112,32,15,GREEN)
 label('배터리  '+battery,x+12,142,230,38,23,GREEN if name=='AMR1' else ORANGE)
 label(state+'  |  '+pos,x+243,146,255,30,16,MUTED)
 camera(name+' 현재 카메라',x,207,510,221)
 camera('고정 웹캠 '+('1' if name=='AMR1' else '2'),x,445,510,235)
box('',220,700,1440,300)
label('이벤트 로그',232,712,270,42,23)
box('기간: 전체  ▼',1220,715,190,38,size=15)
box('위험도: 전체  ▼',1425,715,220,38,size=15)
columns=[(235,190,'발생 시각'),(425,200,'이벤트 종류'),(625,335,'발생 위치 (좌표)'),(960,180,'위험도'),(1140,505,'로봇1 증거 이미지')]
for x,w,t in columns:box(t,x,771,w,42,'#10283c',BORDER,17)
for x,w,t in [(235,190,'14:32:10'),(425,200,'화재 발생'),(625,335,'X: 12.4, Y: 8.1')]:box(t,x,813,w,114,size=20)
box('',960,813,180,114)
box('상',1000,846,100,46,'#542421','#f47468',21,'#ffb3ad')
box('',1140,813,505,114)
box('증거 사진 1장',1158,827,160,86,'#223a4a','#577084',15,MUTED)
label('로봇1 · 사건 E1\n클릭하여 이미지 확대',1335,831,290,78,17)
label('사건 행 클릭 → 상세 정보·처리 상태·메모    |    위험도: 상 · 중 · 하',237,943,1400,38,16,MUTED)
label('UI 설계 목업 · 지도/수치/영상 자리 표시는 예시 · 운영 명령 요청은 로봇 관리 화면에서 제공',220,1008,1440,24,13,MUTED,BG)
save('01-dashboard')

page('02 이벤트 상세 및 사진','02-event-detail')
shell('이벤트 로그')
label('이벤트 상세  /  E1 · 화재 발생',230,95,1200,55,26,TEXT,BG)
box('목록으로',1480,101,170,40,size=16)
box('로봇1 증거 이미지 · 해당 이벤트의 사진 1장',230,165,760,55,size=20)
box('증거 이미지 표시 영역\n\n사진 클릭 시 원본 크기로 확대',230,220,760,420,'#112a3a',BORDER,25,MUTED)
box('발생 시각   2026-09-06 14:32:10\n\n이벤트 종류   화재 발생\n\n발생 좌표   X: 12.4, Y: 8.1\n\n위험도   상\n\n촬영 소스   로봇1',1010,165,640,350,size=20,left=True)
box('처리 상태   신규',1010,535,640,60,'#30251f',BORDER,22,ORANGE,True)
label('위험도와 처리 상태는 별개로 관리',1010,605,640,35,16,MUTED,BG)
box('처리 상태 변경',230,665,1420,50,size=21,left=True)
for x,t in [(250,'신규'),(595,'확인중'),(940,'작업요청'),(1285,'조치완료')]:
 box(t,x,730,310,47,'#15384e' if t=='신규' else PANEL,BLUE if t=='신규' else BORDER,19)
box('메모 입력 / 조치 요청 내용 / 처리 결과',250,797,1040,72,'#071a29',BORDER,18,MUTED,True)
box('변경 저장',1310,797,315,72,'#15384e',BLUE,20)
box('변경 이력   |   14:32:10  시스템: 신규 사건 등록\n저장 시 담당자·시각·이전/새 상태·메모를 함께 기록',230,890,1420,100,size=18,left=True)
label('상태는 허용된 다음 단계로 변경 · 저장 전 서버에서 권한·현재 상태 확인',230,1008,1420,24,13,MUTED,BG)
save('02-event-detail')

page('03 로봇 관리 및 명령 요청','03-robot-management')
shell('로봇 관리')
label('로봇 관리 / 운영 명령 요청',230,95,1420,55,26,TEXT,BG)
for x,n,s,b in [(230,'AMR1','순찰 중','82%'),(950,'AMR2','대기','41%')]:
 box(f'{n}   |   온라인\n\n배터리 {b}    상태: {s}\n\n위치·마지막 상태 수신 시각 표시',x,170,700,185,size=23,left=True)
box('대상 로봇: AMR1  ▼',230,390,1420,65,'#10283c',BORDER,22,left=True)
for x,t in [(245,'순찰 시작 요청'),(530,'일시정지 요청'),(815,'재개 요청'),(1100,'복귀 요청'),(1385,'대피 요청')]:
 box(t,x,485,250,65,'#15384e',BLUE,20)
box('웹은 요청을 생성·기록합니다. 실제 수락·실행·완료 판단은 로봇/미션 모듈이 담당합니다.',230,580,1420,70,'#302b20',BORDER,19,ORANGE,True)
box('명령 요청 이력',230,685,1420,55,size=22,left=True)
box('요청 ID        로봇        명령               현재 상태         요청 시각         결과/사유',230,740,1420,55,'#10283c',BORDER,18,left=True)
box('C-001         AMR1       순찰 시작          진행중             14:30:00         수락 후 진행 중',230,795,1420,90,size=19,left=True)
box('요청됨  →  수락됨  →  진행중  →  완료 / 실패\n응답 지연은 결과 미확인으로 표시하며 실행 실패로 단정하지 않음',230,910,1420,90,size=18,left=True)
save('03-robot-management')

E.indent(doc)
E.ElementTree(doc).write(OUT/'parking-dashboard-ui.drawio',encoding='utf-8',xml_declaration=True)
# Keep the current flowchart and these UI pages together for design review.
flowpath=OUT.parent/'parking-dashboard-flowchart/parking-dashboard-flowchart.drawio'
flow=E.parse(flowpath).getroot()
for d in list(flow):
 if d.get('id','').startswith('ui-'):flow.remove(d)
for i,(d,slug) in enumerate(pages):
 c=copy.deepcopy(d);c.set('id','ui-'+slug);c.set('name',f'{7+i:02d} '+d.get('name')[3:]);flow.append(c)
E.indent(flow);E.ElementTree(flow).write(flowpath,encoding='utf-8',xml_declaration=True)
for d in doc:
 ids=[c.get('id') for c in d.findall('.//mxCell')];assert len(ids)==len(set(ids))
print('Created editable UI with 3 pages; appended UI tabs 07–09 to latest flowchart.')
