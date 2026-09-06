from pathlib import Path
import copy, xml.etree.ElementTree as E
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).parent
W,H=4300,980
doc=E.Element('mxfile',host='app.diagrams.net',type='device')
d=E.SubElement(doc,'diagram',name='00 시작부터 전체 구현 흐름',id='implementation-overview')
m=E.SubElement(d,'mxGraphModel',grid='1',gridSize='10',page='1',pageWidth=str(W),pageHeight=str(H),background='#ffffff')
root=E.SubElement(m,'root');E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0')
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
im=Image.new('RGB',(W,H),'white');draw=ImageDraw.Draw(im)

def box(id_,text,x,y,w,h,fill='#edf3f8',stroke='#597185',size=18,diamond=False):
    shape='rhombus' if diamond else 'rectangle'
    c=E.SubElement(root,'mxCell',id=id_,parent='1',vertex='1',value=text,style=f'shape={shape};whiteSpace=wrap;html=0;rounded=0;fillColor={fill};strokeColor={stroke};strokeWidth=2;fontColor=#172434;fontFamily=Noto Sans CJK KR;fontSize={size};spacing=8;')
    E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
    if diamond:
        draw.polygon([(x+w/2,y),(x+w,y+h/2),(x+w/2,y+h),(x,y+h/2)],fill=fill,outline=stroke)
    else:draw.rectangle((x,y,x+w,y+h),fill=fill,outline=stroke,width=2)
    f=ImageFont.truetype(font,size,index=1);b=draw.multiline_textbbox((0,0),text,font=f,spacing=5)
    draw.multiline_text((x+(w-(b[2]-b[0]))/2,y+(h-(b[3]-b[1]))/2-b[1]),text,font=f,fill='#172434',spacing=5,align='center')
def edge(id_,a,b,label=''):
    c=E.SubElement(root,'mxCell',id=id_,parent='1',edge='1',source=a,target=b,value=label,style='edgeStyle=orthogonalEdgeStyle;rounded=0;curved=0;orthogonalLoop=1;jettySize=auto;endArrow=block;html=0;strokeColor=#597185;strokeWidth=2;fontFamily=Noto Sans CJK KR;fontSize=14;labelBackgroundColor=#ffffff;')
    E.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})

title='지하주차장 시스템 모니터 - 시작부터 구현 흐름'
box('title',title,40,25,4220,55,'#ffffff','#ffffff',27)
steps=[
 ('s0','시작'),
 ('s1','Flask 서버 실행\nSQLite 연결'),
 ('s2','DB 테이블·계정\n지도·P1~P7 준비'),
 ('s3','데이터 수신부 실행\n샘플 HTTP → ROS'),
 ('s4','로그인·권한 확인'),
 ('s5','대시보드 생성\n빈 이벤트 로그 표시'),
 ('s6','AMR 상태·위치\n지도·영상 갱신'),
 ('s7','화재 이벤트 수신\n좌표·위험도·사진 검증'),
 ('s8','사진 파일 저장\n이벤트 DB 저장'),
 ('s9','웹 이벤트 로그 반영\n시각·좌표·상중하·사진'),
 ('s10','이벤트 상세 조회\n사진 확대·메모'),
 ('s11','처리 상태 변경\n신규→확인중→작업요청→조치완료'),
 ('s12','운영 명령 요청\n결과 상태 표시'),
 ('s13','사건·명령·순찰·교대\n이력 저장·검색'),
 ('s14','로그아웃\n수신·저장은 계속'),
]
x=45;y=120;bw=245;bh=105;gap=38
for i,(id_,text) in enumerate(steps):
    fill='#e7f3e9' if i in (0,14) else ('#fff2d9' if i in (7,11,12) else '#edf3f8')
    box(id_,text,x+i*(bw+gap),y,bw,bh,fill=fill,size=16)
    if i:edge('main-'+str(i),steps[i-1][0],id_)

# Functional detail boxes, intentionally roomy and editable.
groups=[
 ('g1','초기화·인증','서버/DB 시작\n테이블·계정 준비\n로그인 검증\n세션·권한 관리',45,340,620),
 ('g2','관제 화면','AMR1·AMR2 상태\n지도·경로·P1~P7\n영상 4개\n연결 끊김 표시',710,340,620),
 ('g3','화재 이벤트','메시지·이벤트 ID\n발생 시각·좌표\n위험도 상·중·하\n로봇1 사진 한 장',1375,340,620),
 ('g4','저장·로그','사진 파일 저장\nDB에 경로·메타데이터\n로그 한 행 표시\n검색·이미지 확대',2040,340,620),
 ('g5','처리·명령','이벤트 상태·메모 이력\n명령 요청 ID 저장\n수락·진행·완료·실패\n응답 지연 표시',2705,340,620),
 ('g6','순찰·교대·검증','순찰·P1~P7 방문\n교대 이력\n샘플 검증→ROS 연동\n실제 환경 검증·촬영',3370,340,845),
]
for id_,heading,detail,gx,gy,gw in groups:
    box(id_,heading+'\n\n'+detail,gx,gy,gw,250,'#f7f9fb','#8aa0b2',18)

# Show ownership boundaries below the functional boxes.
box('boundary-web','웹 담당\n표시·요청·기록',45,690,1330,100,'#e8f2fb','#4e8eb8',19)
box('boundary-shared','공통 인터페이스\nID·시간·좌표·상태·이미지 연결 규칙',1485,690,1330,100,'#fff2d9','#b28b45',19)
box('boundary-ext','로봇·인식·미션 모듈\n화재 판정·로봇 실행·완료 결과 제공',2925,690,1290,100,'#fce9e5','#b5746c',19)
box('note','※ 위험도와 처리 상태는 별도 관리 / 원본 영상은 DB에 저장하지 않음 / 웹 명령은 실행 요청이며 실제 판단은 미션 모듈 담당',45,850,4170,65,'#ffffff','#ffffff',16)

im.save(OUT/'시작부터_전체구현흐름_미리보기.png')

# Append the focused horizontal detail pages from the latest design.
source=E.parse(OUT/'플로우차트_가로형_기능박스.drawio').getroot()
detail_names=[
    (0,'01 시작·로그인·대시보드'),
    (1,'02 화재 이벤트 저장·로그 반영'),
    (2,'03 로그 조회·사진 확대'),
    (3,'04 이벤트 처리 상태'),
    (4,'05 운영 명령 요청·결과'),
    (5,'06 순찰·교대·이력'),
    (6,'07 임시 HTTP·ROS 연동'),
    (7,'08 지도·상태·영상 갱신'),
    (9,'09 통합 검증·영상 촬영'),
]
for idx,name in detail_names:
    page=copy.deepcopy(source.findall('diagram')[idx]);page.set('id','implementation-'+str(idx+1));page.set('name',name);doc.append(page)

E.indent(doc)
target=OUT/'시작부터_세부구현_플로우차트.drawio'
E.ElementTree(doc).write(target,encoding='utf-8',xml_declaration=True)

check=E.parse(target).getroot()
assert len(check.findall('diagram'))==10
for page in check.findall('diagram'):
    cells=page.findall('.//mxCell');ids={c.get('id') for c in cells}
    for cell in cells:
        for key in ('source','target'):
            if cell.get(key):assert cell.get(key) in ids
print('Created',target,'pages=',len(check.findall('diagram')))
