from pathlib import Path
import subprocess, json, re, copy, xml.etree.ElementTree as E

OUT=Path(__file__).parent
doc=E.Element('mxfile',host='app.diagrams.net',type='device')
graphs=[]

def graph(name,slug,body,direction='TB'):
    dot='digraph G { graph [rankdir='+direction+', bgcolor="white", pad="0.4", nodesep="0.55", ranksep="0.65", splines=polyline]; node [shape=box, style="filled", fillcolor="#edf3f8", color="#597185", fontname="Noto Sans CJK KR", fontsize=17, margin="0.2,0.15"]; edge [color="#597185", fontname="Noto Sans CJK KR", fontsize=13, arrowsize=0.8];\n'+body+'\n}'
    src=OUT/(slug+'.dot');src.write_text(dot)
    subprocess.run(['dot','-Tpng','-Gdpi=110',str(src),'-o',str(OUT/(slug+'.png'))],check=True)
    data=json.loads(subprocess.check_output(['dot','-Tjson',str(src)]))
    _,_,W,H=map(float,data['bb'].split(',')); pad=35
    d=E.SubElement(doc,'diagram',name=name,id=slug)
    m=E.SubElement(d,'mxGraphModel',grid='1',gridSize='10',page='1',pageScale='1',pageWidth=str(round(W+pad*2)),pageHeight=str(round(H+pad*2)))
    root=E.SubElement(m,'root');E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0')
    nodes={}
    for n in data['objects']:
        if 'pos' not in n: continue
        idx=n['_gvid'];nodes[idx]=n
        x,y=map(float,n['pos'].split(','));w=float(n['width'])*72;h=float(n['height'])*72
        shape={'diamond':'rhombus','ellipse':'ellipse','cylinder':'cylinder3','note':'note'}.get(n.get('shape'),'rectangle')
        c=E.SubElement(root,'mxCell',id='n'+str(idx),parent='1',vertex='1',value=n.get('label','').replace('\\n','\n'),style=f'shape={shape};whiteSpace=wrap;html=0;fillColor={n.get("fillcolor","#edf3f8")};strokeColor=#597185;fontColor=#172434;fontFamily=Noto Sans CJK KR;fontSize=17;spacing=8;')
        E.SubElement(c,'mxGeometry',x=str(x-w/2+pad),y=str(H-y-h/2+pad),width=str(w),height=str(h),**{'as':'geometry'})
    for i,e in enumerate(data.get('edges',[])):
        # Graphviz routes become explicit, editable draw.io connector waypoints.
        coords=[];end=None
        for token in e['pos'].split():
            parts=token.split(',')
            if parts[0]=='e':end=tuple(map(float,parts[1:]));continue
            if parts[0]=='s':continue
            pt=tuple(map(float,parts))
            if not coords or pt!=coords[-1]:coords.append(pt)
        if end:coords.append(end)
        def anchor(pt,idx):
            n=nodes[idx];cx,cy=map(float,n['pos'].split(','));w=float(n['width'])*72;h=float(n['height'])*72
            return max(0,min(1,(pt[0]-cx+w/2)/w)),max(0,min(1,(cy+h/2-pt[1])/h))
        ex,ey=anchor(coords[0],e['tail']);ix,iy=anchor(coords[-1],e['head'])
        c=E.SubElement(root,'mxCell',id='e'+str(i),parent='1',edge='1',source='n'+str(e['tail']),target='n'+str(e['head']),value=e.get('label','').replace('\\n','\n'),style=f'endArrow=block;html=0;rounded=0;strokeColor=#597185;fontFamily=Noto Sans CJK KR;fontSize=13;labelBackgroundColor=#ffffff;exitX={ex};exitY={ey};entryX={ix};entryY={iy};')
        geom=E.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
        pts=E.SubElement(geom,'Array',**{'as':'points'})
        for x,y in coords[1:-1]:E.SubElement(pts,'mxPoint',x=str(x+pad),y=str(H-y+pad))
        if 'dashed' in e.get('style',''): c.set('style', c.get('style')+'dashed=1;')
    graphs.append((name,slug))

graph('01 시스템 아키텍처','01-architecture',r'''
 browser [label="웹 대시보드 / 관리자·운영자·조회자\n지도 · 상태 · 영상 · 이벤트 · 명령 · 이력",fillcolor="#eaf5ec"];
 routes [label="Flask routes / 인증·권한 검사\nauth · dashboard · robots · maps\nevents · commands · history"];
 services [label="services / 업무 규칙\n이벤트 전이 · 명령 요청 · 순찰·교대 기록"];
 repository [label="repositories / DB 접근\n트랜잭션 · 검색 · 중복·순서 검증"];
 db [label="SQLite\n사용자·권한 / 로봇·상태 / 지도\n이벤트·변경 이력 / 명령·상태 이력\n순찰·관측점 방문 / 교대 이력",shape=cylinder,fillcolor="#fff2d9"];
 media [label="증거 이미지 파일 저장소\nDB에는 경로와 메타데이터",shape=folder,fillcolor="#fff2d9"];
 adapter [label="연동 어댑터 / 공통 내부 데이터 형식\n현재: Mock + 임시 HTTP\n추후: ros_adapter.py"];
 ext [label="감지 / 로봇·미션 관리 모듈\n상태·이벤트 전송 / 명령 수락·실행·결과 판단",fillcolor="#eeeeee"];
 camera [label="camera_service\nAMR1·AMR2 / 고정 웹캠 1·2\n영상 중계 · 소스별 연결 상태"];
 browser -> routes [label="조회 / 요청"];
 routes -> services;
 services -> repository;
 repository -> db;
 services -> media [label="증거 저장·조회"];
 services -> adapter [label="저장된 명령 요청 전송"];
 adapter -> services [label="정규화된 상태·결과 수신"];
 adapter -> ext [label="요청 ID + 명령"];
 ext -> adapter [label="수락 / 진행 / 완료 / 실패"];
 ext -> camera [label="영상 스트림"];
 camera -> browser [label="인증 후 영상 표시"];
''')

graph('02 시작 및 화면 흐름','02-user-flow',r'''
 start [label="Sysmon 시작",shape=ellipse,fillcolor="#eaf5ec"];
 init [label="Flask / DB 스키마 / 어댑터 준비\n페이지 구성 · 빈 화면 데이터셋 준비\n시연: 계정·지도·관측점 7개 등록 / 이벤트 0건"];
 receive [label="백그라운드 수신 시작\n로그인과 무관하게 계속 동작\n03 데이터 수신 흐름 참조",fillcolor="#eeeeee"];
 login [label="로그인 화면 → 계정 입력"];
 auth [label="인증 성공?",shape=diamond,fillcolor="#fff2d9"];
 err [label="오류 표시 / 재입력",fillcolor="#fce9e5"];
 ui [label="권한에 맞는 대시보드 표시\n지도·7관측점 / AMR1·2 상태 / 영상 4개\n이벤트 0건 → 빈 목록 표시"];
 action [label="사용자 선택",shape=diamond,fillcolor="#fff2d9"];
 detail [label="이벤트 상세 / 상태 변경\n04 이벤트 처리 흐름 참조"];
 command [label="운영 명령 요청 / 진행 조회\n05 명령 요청 흐름 참조"];
 history [label="사건·명령·순찰·교대 이력 검색\n06 순찰·교대 흐름 참조"];
 logout [label="로그아웃 / 세션 종료",shape=ellipse,fillcolor="#eaf5ec"];
 start -> init;init -> receive;init -> login;
 login -> auth;auth -> err [label="아니오"];err -> login;
 auth -> ui [label="예"];ui -> action;
 action -> detail [label="이벤트"];action -> command [label="명령"];
 action -> history [label="이력"];action -> logout [label="로그아웃"];
 detail -> ui [label="복귀"];command -> ui [label="복귀"];history -> ui [label="복귀"];
''')

graph('03 데이터 수신 및 저장','03-data-flow',r'''
 input [label="수신 대기\n임시 HTTP / 추후 ROS 어댑터",shape=ellipse,fillcolor="#eaf5ec"];
 normalize [label="공통 형식 변환\nsource_id · message_id · observed_at\nrobot_id · map_id / frame_id"];
 valid [label="형식·참조·중복·순서 검증",shape=diamond,fillcolor="#fff2d9"];
 reject [label="중복은 처리 생략\n오류·역순은 기록 / 최신값 덮어쓰기 방지",fillcolor="#fce9e5"];
 type [label="수신 종류",shape=diamond,fillcolor="#fff2d9"];
 status [label="상태: 최신값 + 상태 이력 저장\n배터리·위치·연결·임무 상태\n좌표 미확정 시 지도 위치 미표시"];
 event [label="감지: 이벤트 + 증거 이미지 저장\n초기 처리 상태 신규\n04 이벤트 흐름으로 연결"];
 cmd [label="명령 결과: request_id 매칭\n상태 이력 기록 / 05 흐름 참조"];
 patrol [label="순찰·관측점 방문·교대 기록\n06 흐름 참조"];
 commit [label="DB 트랜잭션 성공?",shape=diamond,fillcolor="#fff2d9"];
 fail [label="오류 기록 / 미처리 입력 보관\n재처리 정책에 따라 복구",fillcolor="#fce9e5"];
 update [label="UI API 최신값 조회 → 화면 갱신\n지도·상태·경고·이력에 반영",fillcolor="#eaf5ec"];
 next [label="다음 메시지 수신 대기",shape=ellipse,fillcolor="#eaf5ec"];
 input -> normalize -> valid;
 valid -> reject [label="거부 / 중복"];reject -> next;
 valid -> type [label="통과"];
 type -> status [label="상태"];type -> event [label="이벤트"];
 type -> cmd [label="명령 결과"];type -> patrol [label="순찰·교대"];
 status -> commit;event -> commit;cmd -> commit;patrol -> commit;
 commit -> update [label="예"];commit -> fail [label="아니오"];
 update -> next;fail -> next;
''')

graph('04 이벤트 처리','04-event-flow',r'''
 rx [label="감지 이벤트 수신\n유형·시각·좌표·위험등급·증거",shape=ellipse,fillcolor="#eaf5ec"];
 create [label="중복 검증 → 증거 파일·DB 저장\n이벤트 상태: 신규"];
 alert [label="대시보드 경고 목록 / 지도에 표시\n좌표 불명: 목록에 표시 + 위치 미확정"];
 open [label="관리자 상세 열기\n이미지·측정값·좌표·시각 확인"];
 request [label="권한 있는 사용자가 상태 변경 요청\n신규 → 확인중 → 작업요청 → 조치완료\n각 단계에서 동일 검증 수행"];
 check [label="권한·현재 상태·버전 유효?",shape=diamond,fillcolor="#fff2d9"];
 deny [label="거부 이유 / 최신 상태 표시\n무권한 또는 다른 사용자와 충돌",fillcolor="#fce9e5"];
 save [label="동일 트랜잭션으로 저장\n현재 상태 갱신 + 변경 이력 추가\n변경자·시각·이전/새 상태·메모"];
 refresh [label="목록·상세·이력 갱신",fillcolor="#eaf5ec"];
 note [label="작업요청은 사건 처리 단계\n로봇 명령 전송과 별개\n외부 작업 시스템 연동은 미확정",shape=note,fillcolor="#fff2d9"];
 rx -> create -> alert -> open -> request -> check;
 check -> deny [label="아니오"];check -> save [label="예"];save -> refresh;
 deny -> open [label="새로고침 후 확인"];
 note -> request [style=dashed,label="의미 구분"];
''')

graph('05 운영 명령 요청','05-command-flow',r'''
 select [label="운영자가 대상 로봇·명령 선택\n순찰 시작 / 일시정지 / 재개 / 복귀 / 대피",shape=ellipse,fillcolor="#eaf5ec"];
 pre [label="권한·요청 항목·중복 요청 키 확인",shape=diamond,fillcolor="#fff2d9"];
 deny [label="요청 오류 / 권한 없음 표시",fillcolor="#fce9e5"];
 persist [label="명령 요청 + 요청 이력 저장\nrequest_id / 요청자 / 로봇 / 파라미터\n초기 상태: 요청됨"];
 dispatch [label="DB 저장 성공 후 어댑터가 전달\nMockMission 또는 로봇·미션 관리 모듈"];
 uncertain [label="응답 지연 / 전송 결과 불명\n결과 확인 필요 표시\n동일 요청 ID 조회·조정 (새 명령 자동 발급 금지)",fillcolor="#fce9e5"];
 ack [label="미션 모듈의 수락 판단",shape=diamond,fillcolor="#fff2d9"];
 rejected [label="거절됨 + 사유 기록\n거절 상태 추가는 설계 제안",fillcolor="#fce9e5"];
 accepted [label="수락됨 → 진행중\n모듈 피드백으로만 상태 변경"];
 result [label="실행 결과 수신",shape=diamond,fillcolor="#fff2d9"];
 done [label="완료 기록",fillcolor="#eaf5ec"];
 failed [label="실패 + 사유 기록",fillcolor="#fce9e5"];
 ui [label="상태 전이 이력 저장 / UI 갱신\n순찰·교대 성공은 별도 임무 결과로 확인"];
 select -> pre;pre -> deny [label="불가"];pre -> persist [label="가능"];
 persist -> dispatch;dispatch -> uncertain [label="통신 오류 / 지연"];
 dispatch -> ack [label="응답 수신"];ack -> rejected [label="거절"];ack -> accepted [label="수락"];
 accepted -> result;result -> done [label="성공"];result -> failed [label="실패"];
 done -> ui;failed -> ui;rejected -> ui;uncertain -> ui;
''')

graph('06 순찰·교대 및 이력','06-patrol-history',r'''
 rx [label="미션 모듈의 수행 기록 수신\n샘플 시연도 같은 내부 형식",shape=ellipse,fillcolor="#eaf5ec"];
 type [label="기록 종류",shape=diamond,fillcolor="#fff2d9"];
 patrol [label="순찰 ID로 시작·진행·종료 갱신\n로봇 / 경로 버전 / 시작·종료 시각\n결과 / 연관 명령 ID (없을 수 있음)"];
 visit [label="관측점 방문 기록\n순찰 ID / P1~P7 / 방문 시각·결과\n재방문과 중복 메시지 구분"];
 handover [label="교대 ID로 교대 기록\n인계 로봇 → 인수 로봇 / 사유\n인계 전·후 순찰 ID / 시각·결과"];
 db [label="SQLite 이력 저장\n순찰 / 방문 / 교대",shape=cylinder,fillcolor="#fff2d9"];
 user [label="관리자 이력 검색\n사건 / 명령 / 순찰 / 교대 선택\n기간·로봇·유형·상태 필터"];
 result [label="검색 결과 존재?",shape=diamond,fillcolor="#fff2d9"];
 empty [label="검색 결과 없음 표시"];
 detail [label="목록 → 상세 / 시간순 변경 이력\n관련 사건·명령·순찰·교대 연결 확인",fillcolor="#eaf5ec"];
 rx -> type;type -> patrol [label="순찰"];type -> visit [label="방문"];type -> handover [label="교대"];
 patrol -> db;visit -> db;handover -> db;
 db -> result [label="서버 조회"];user -> result [label="검색 요청"];
 result -> empty [label="아니오"];result -> detail [label="예"];
''')

graph('07 DB 관계 초안','07-database',r'''
 users [label="users\nPK user_id / role / password_hash",fillcolor="#fff2d9"];
 robots [label="robots\nPK robot_id / name"];
 latest [label="robot_latest_status\nPK·FK robot_id / 상태·배터리·좌표\nmap_id / frame_id / observed_at / last_seen"];
 logs [label="robot_status_history\nPK id / FK robot_id / 수신 상태·시각"];
 maps [label="maps / map_features / routes\n지도 버전·좌표 변환 정보\nP1~P7 / 안전구역 / 도크 / 경로"];
 events [label="events / event_evidence\nPK event_id / source_event_id UNIQUE\nFK robot_id(선택) / camera_id / map_id\n유형·위험등급·좌표·처리상태·version\n증거 경로·측정값",fillcolor="#fff2d9"];
 changes [label="event_changes\nFK event_id / actor_id\n이전·다음 상태 / 메모 / 시각"];
 commands [label="commands / command_updates\nPK request_id / FK robot_id·requested_by\n요청 종류·인자·현재 상태 / 결과 이력",fillcolor="#fff2d9"];
 patrols [label="patrol_runs / patrol_visits\n순찰 ID·로봇·경로 버전·명령 ID\n관측점 방문 시각·결과",fillcolor="#fff2d9"];
 handovers [label="handovers\n교대 ID / 인계·인수 robot_id\n이전·다음 patrol_id / 사유·상태·시각",fillcolor="#fff2d9"];
 users -> commands [label="1:N 요청"];users -> changes [label="1:N 변경"];
 robots -> latest [label="1:0..1"];robots -> logs [label="1:N"];
 robots -> events [label="1:N"];robots -> commands [label="1:N"];
 maps -> latest [label="좌표계"];maps -> events [label="위치"];maps -> patrols [label="경로"];
 events -> changes [label="1:N"];
 commands -> patrols [label="선택 연결"];
 robots -> patrols [label="1:N"];patrols -> handovers [label="인계 전·후 연결"];
''')

# Editable wireframe reflecting the user's four-video dashboard reference.
from PIL import Image, ImageDraw, ImageFont
W,H=1700,1130
d=E.SubElement(doc,'diagram',name='08 대시보드 목업',id='08-wireframe')
m=E.SubElement(d,'mxGraphModel',grid='1',gridSize='10',page='1',pageWidth=str(W),pageHeight=str(H))
root=E.SubElement(m,'root');E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0')
im=Image.new('RGB',(W,H),'#ffffff');draw=ImageDraw.Draw(im)
fontpath='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def rect(t,x,y,w,h,fill='#ffffff',size=17,left=False):
    c=E.SubElement(root,'mxCell',id='u'+str(len(root)),parent='1',vertex='1',value=t,style=f'whiteSpace=wrap;html=0;fillColor={fill};strokeColor=#597185;fontFamily=Noto Sans CJK KR;fontSize={size};align={"left" if left else "center"};spacing=12;')
    E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
    draw.rectangle((x,y,x+w,y+h),fill=fill,outline='#597185',width=1)
    f=ImageFont.truetype(fontpath,size,index=1);b=draw.multiline_textbbox((0,0),t,font=f,spacing=6)
    tx=x+12 if left else x+(w-b[2]+b[0])/2
    draw.multiline_text((tx,y+(h-b[3]+b[1])/2-b[1]),t,font=f,fill='#172434',spacing=6,align='left' if left else 'center')
rect('지하주차장 로봇 관제 시스템 | 상세 설계 목업',25,20,1650,65,'#e7eff6',25,True)
rect('시연 데이터 / 실연동 구분 표시                         사용자: 운영담당 · 권한: 운영자 · 로그아웃',25,95,1650,36,'#f6f8fa',16,True)
rect('대시보드\n\n지도 모니터링\n\n로봇 / 운영 명령\n\n이벤트\n\n이력 조회\n\n사용자·권한',25,145,195,830,'#f2f5f8',19)
rect('지하주차장 지도 / 경로 버전',240,145,430,45,'#e7eff6',19)
rect('',240,190,430,415,'#f6f8fa')
path=[(305,250),(430,250),(585,250),(585,355),(430,355),(305,355),(305,450)]
draw.line(path,fill='#82a38b',width=3)
c=E.SubElement(root,'mxCell',id='route-line',parent='1',edge='1',style='endArrow=block;strokeColor=#82a38b;strokeWidth=3;')
g=E.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
E.SubElement(g,'mxPoint',x=str(path[0][0]),y=str(path[0][1]),**{'as':'sourcePoint'})
E.SubElement(g,'mxPoint',x=str(path[-1][0]),y=str(path[-1][1]),**{'as':'targetPoint'})
points=E.SubElement(g,'Array',**{'as':'points'})
for x,y in path[1:-1]:E.SubElement(points,'mxPoint',x=str(x),y=str(y))
rect('P1',270,230,70,40);rect('P2',395,230,70,40);rect('P3',550,230,70,40)
rect('P4',550,335,70,40);rect('P5',395,335,70,40);rect('P6',270,335,70,40)
rect('P7',270,430,70,40)
rect('E1',570,285,50,30,'#fce9e5',14)
rect('AMR1\n현재 위치',380,425,100,60,'#e7f3e9',15)
rect('AMR2\n현재 위치',515,425,100,60,'#fff2d9',15)
rect('안전구역',270,530,140,45,'#e7f3e9',15);rect('도크',450,530,170,45,'#e7eff6',15)
rect('P1→P2→P3→P4→P5→P6→P7\n예시 경로 / 실제 지도·좌표는 추후 적용\n이벤트 마커 선택 → 상세 정보',240,615,430,95,'#ffffff',15)
rect('선택 로봇: AMR1 | 운영 명령 요청',240,725,430,42,'#e7eff6',16)
rect('순찰 시작 요청',250,783,195,40);rect('일시정지 요청',465,783,195,40)
rect('재개 요청',250,833,125,40);rect('복귀 요청',390,833,125,40);rect('대피 요청',530,833,130,40)
rect('요청 C-001: 수락됨 → 진행중\n실행 판단: 로봇 / 미션 모듈',240,893,430,72,'#fff2d9',16)
for x,robot,battery,state in [(690,'AMR1','82%','순찰'),(1190,'AMR2','41%','대기')]:
    rect(f'{robot} | 연결 정상 | 배터리 {battery}\n상태: {state} | 위치·수신 시각 표시',x,145,485,85,'#e7f3e9',18)
    rect(f'{robot} 실시간 영상',x,245,485,205,'#f2f5f8',20)
    rect('고정 웹캠 '+('1' if robot=='AMR1' else '2'),x,465,485,205,'#f2f5f8',20)
rect('이벤트 경고 | 신규 1 · 확인중 1 · 작업요청 0 · 조치완료 0',690,690,985,45,'#e7eff6',18,True)
rect('시각     소스       유형         위치      위험등급      처리상태',690,745,985,40,'#f2f5f8',17,True)
rect('14:32   AMR1    누수 의심      P3         주의           신규\n14:28   웹캠1    비상구 적치물  출입구     긴급           확인중',690,785,985,80,size=17,left=True)
rect('행 / 지도 마커 선택 → 이미지·좌표·시각·위험등급·메모\n상태 변경: 신규 → 확인중 → 작업요청 → 조치완료',690,880,985,85,'#fff2d9',17,True)
rect('이력: 사건 | 명령 | 순찰 | 교대    /    기간 · 로봇 · 유형 · 상태로 검색',240,985,1435,50,'#e7eff6',19,True)
rect('설계 초안: 버튼은 요청 생성용 · 수치/배치는 예시 · 영상 원본은 DB 저장하지 않음 · 화재 범위 미확정',25,1060,1650,45,'#ffffff',16,True)
im.save(OUT/'08-wireframe.png')

E.indent(doc)
target=OUT/'parking-dashboard-design-v2.drawio'
E.ElementTree(doc).write(target,encoding='utf-8',xml_declaration=True)
for d in doc:
    cells=d.findall('.//mxCell');ids=[c.get('id') for c in cells]
    assert len(ids)==len(set(ids))
    for c in cells:
        for k in ('source','target'):
            if c.get(k): assert c.get(k) in ids
print('Saved 8-page editable design and 8 PNG previews. XML IDs and connectors validated.')
