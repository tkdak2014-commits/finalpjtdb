from pathlib import Path
import json, subprocess, xml.etree.ElementTree as E

OUT=Path(__file__).parent
doc=E.Element('mxfile',host='app.diagrams.net',type='device')

def diagram(name, slug, body):
    dot='''digraph G {
      graph [rankdir=LR, bgcolor="white", pad="0.45", nodesep="0.55", ranksep="0.7", splines=ortho];
      node [shape=box, style="filled", fillcolor="#edf3f8", color="#597185", penwidth=2, fontname="Noto Sans CJK KR", fontsize=17, margin="0.22,0.16"];
      edge [color="#597185", penwidth=2, fontname="Noto Sans CJK KR", fontsize=14, arrowsize=0.8];
    '''+body+'\n}'
    dot_path=OUT/(slug+'.dot');dot_path.write_text(dot)
    png_path=OUT/(slug+'.png')
    subprocess.run(['dot','-Tpng','-Gdpi=110',str(dot_path),'-o',str(png_path)],check=True)
    data=json.loads(subprocess.check_output(['dot','-Tjson',str(dot_path)]))
    _,_,W,H=map(float,data['bb'].split(','));pad=45
    d=E.SubElement(doc,'diagram',name=name,id=slug)
    model=E.SubElement(d,'mxGraphModel',grid='1',gridSize='10',page='1',pageScale='1',pageWidth=str(round(W+pad*2)),pageHeight=str(round(H+pad*2)),background='#ffffff')
    root=E.SubElement(model,'root');E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0')
    nodes={}
    for n in data['objects']:
        if 'pos' not in n:continue
        idx=n['_gvid'];nodes[idx]=n
        x,y=map(float,n['pos'].split(','));w=float(n['width'])*72;h=float(n['height'])*72
        source_shape=n.get('shape','box')
        shape='rhombus' if source_shape=='diamond' else 'rectangle'
        style=(f'shape={shape};whiteSpace=wrap;html=0;rounded=0;fillColor={n.get("fillcolor","#edf3f8")};'
               'strokeColor=#597185;strokeWidth=2;fontColor=#172434;fontFamily=Noto Sans CJK KR;fontSize=17;spacing=8;')
        c=E.SubElement(root,'mxCell',id='n'+str(idx),parent='1',vertex='1',value=n.get('label','').replace('\\n','\n'),style=style)
        E.SubElement(c,'mxGeometry',x=str(x-w/2+pad),y=str(H-y-h/2+pad),width=str(w),height=str(h),**{'as':'geometry'})
    for i,e in enumerate(data.get('edges',[])):
        c=E.SubElement(root,'mxCell',id='e'+str(i),parent='1',edge='1',source='n'+str(e['tail']),target='n'+str(e['head']),value=e.get('label','').replace('\\n','\n'),style='edgeStyle=orthogonalEdgeStyle;rounded=0;curved=0;orthogonalLoop=1;jettySize=auto;endArrow=block;html=0;strokeColor=#597185;strokeWidth=2;fontFamily=Noto Sans CJK KR;fontSize=14;labelBackgroundColor=#ffffff;')
        E.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})

diagram('01 서버·DB 초기화','01-server-db',r'''
 start [label="시작",fillcolor="#e7f3e9"];
 flask [label="Flask 앱 실행\ncreate_app() 호출"];
 config [label="DB 파일 경로 설정\ninstance/sysmon.sqlite3"];
 folder [label="instance 폴더 존재 확인"];
 makefolder [label="폴더 생성"];
 init [label="init_db() 호출"];
 connect [label="sqlite3.connect() 실행\nSQLite DB 연결"];
 connected [label="DB 연결 성공?",shape=diamond,fillcolor="#fff2d9"];
 fail [label="DB 오류 기록\n서버 시작 중단 또는 재시도",fillcolor="#fce9e5"];
 foreign [label="외래 키 활성화\nPRAGMA foreign_keys = ON"];
 tables [label="필수 테이블 존재 확인"];
 exists [label="모든 테이블 존재?",shape=diamond,fillcolor="#fff2d9"];
 create [label="users·robots·events 등\n테이블 생성"];
 seed [label="관리자 계정·지도·P1~P7\n도크·안전구역 초기 데이터 확인"];
 receiver [label="샘플 HTTP / 수신부 시작"];
 login [label="로그인 페이지 표시",fillcolor="#e7f3e9"];
 start -> flask -> config -> folder;
 folder -> makefolder [label="없음"];folder -> init [label="있음"];makefolder -> init;
 init -> connect -> connected;connected -> fail [label="아니오"];connected -> foreign [label="예"];
 foreign -> tables -> exists;exists -> create [label="아니오"];exists -> seed [label="예"];create -> seed;
 seed -> receiver -> login;
''')

diagram('02 로그인·대시보드 표시','02-login-dashboard',r'''
 login [label="로그인 페이지 표시",fillcolor="#e7f3e9"];
 input [label="아이디·비밀번호 입력"];
 request [label="로그인 요청 전송"];
 users [label="users 테이블에서\n사용자 계정 조회"];
 valid [label="계정·비밀번호 유효?",shape=diamond,fillcolor="#fff2d9"];
 error [label="로그인 오류 메시지 표시",fillcolor="#fce9e5"];
 session [label="세션 생성\n사용자 역할 저장"];
 permission [label="대시보드 조회 권한 확인"];
 loadmap [label="지도·경로·P1~P7\n안전구역·도크 조회"];
 loadrobot [label="AMR1·AMR2 최신 상태 조회"];
 loadevents [label="최근 이벤트 로그 조회"];
 dashboard [label="대시보드 표시\n이벤트 0건이면 빈 로그 표시",fillcolor="#e7f3e9"];
 login -> input -> request -> users -> valid;valid -> error [label="아니오"];error -> login;
 valid -> session [label="예"];session -> permission -> loadmap -> loadrobot -> loadevents -> dashboard;
''')

diagram('03 로봇 상태·지도·영상 갱신','03-status-map-video',r'''
 wait [label="상태·영상 데이터 수신 대기",fillcolor="#e7f3e9"];
 kind [label="수신 종류 확인",shape=diamond,fillcolor="#fff2d9"];
 status [label="상태 메시지 수신\nrobot_id·배터리·좌표·임무·시각"];
 video [label="영상 프레임 수신\nAMR1·AMR2·웹캠1·웹캠2"];
 valid [label="ID·시각·순서 유효?",shape=diamond,fillcolor="#fff2d9"];
 stale [label="오류·중복·오래된 값 기록\n화면 갱신 제외",fillcolor="#fce9e5"];
 save [label="robot_latest_status 갱신\n상태 이력 저장"];
 coord [label="지도 좌표계·버전 일치?",shape=diamond,fillcolor="#fff2d9"];
 mark [label="지도에 로봇 위치 표시"];
 unknown [label="위치 미확정 표시",fillcolor="#fce9e5"];
 card [label="배터리·임무·마지막 수신 시각\n연결 상태 카드 갱신"];
 stream [label="해당 영상 연결 성공?",shape=diamond,fillcolor="#fff2d9"];
 show [label="해당 영상 영역에\n최신 프레임 표시"];
 waiting [label="해당 영상만\n연결 대기·단절 표시",fillcolor="#fce9e5"];
 refresh [label="대시보드 갱신",fillcolor="#e7f3e9"];
 wait -> kind;kind -> status [label="상태"];kind -> video [label="영상"];
 status -> valid;valid -> stale [label="아니오"];valid -> save [label="예"];
 save -> coord;coord -> mark [label="예"];coord -> unknown [label="아니오"];
 mark -> card;unknown -> card;card -> refresh;stale -> wait;
 video -> stream;stream -> show [label="예"];stream -> waiting [label="아니오"];show -> refresh;waiting -> refresh;
 refresh -> wait [label="다음 데이터"];
''')

diagram('04 화재 이벤트·사진·로그 저장','04-fire-event',r'''
 wait [label="화재 이벤트 수신 대기",fillcolor="#e7f3e9"];
 receive [label="화재 이벤트 수신\nmessage_id·event_id·발생 시각\n좌표·위험도·로봇1 사진"];
 format [label="메시지 형식 검증"];
 valid [label="필수 ID·종류 유효?",shape=diamond,fillcolor="#fff2d9"];
 invalid [label="오류 기록\n이벤트 로그 미표시",fillcolor="#fce9e5"];
 dup [label="message_id 중복?",shape=diamond,fillcolor="#fff2d9"];
 skip [label="중복 행 생성 생략"];
 check [label="발생 시각·좌표·위험도·로봇 ID\n사진의 event_id 연결 확인"];
 photo [label="로봇1 증거 사진 파일 저장\nevidence/event_id.jpg"];
 db [label="events 테이블 저장\n시각·종류·좌표·상/중/하\n처리 상태: 신규"];
 path [label="사진 경로를 DB에 저장"];
 saved [label="DB 저장 성공?",shape=diamond,fillcolor="#fff2d9"];
 failed [label="저장 실패 기록\n재처리 대상 보관",fillcolor="#fce9e5"];
 log [label="이벤트 로그 한 행 표시\n시각·화재 발생·좌표·상중하·사진 1장",fillcolor="#e7f3e9"];
 map [label="지도에 화재 위치 마커 표시"];
 wait -> receive -> format -> valid;valid -> invalid [label="아니오"];valid -> dup [label="예"];
 dup -> skip [label="예"];dup -> check [label="아니오"];
 check -> photo -> db -> path -> saved;saved -> failed [label="아니오"];saved -> log [label="예"];
 log -> map -> wait [label="다음 이벤트"];invalid -> wait;skip -> wait;failed -> wait;
''')

diagram('05 로그 상세·처리 상태·메모','05-event-detail-status',r'''
 log [label="이벤트 로그 표시",fillcolor="#e7f3e9"];
 choice [label="사용자 선택",shape=diamond,fillcolor="#fff2d9"];
 image [label="사진 클릭\n증거 이미지 확대"];
 closeimage [label="이미지 닫기\n로그로 복귀"];
 row [label="이벤트 행 클릭"];
 detail [label="상세 조회\n시각·좌표·위험도·사진\n처리 상태·메모·변경 이력"];
 action [label="상세 화면 동작",shape=diamond,fillcolor="#fff2d9"];
 memo [label="메모 입력"];
 authmemo [label="메모 작성 권한 확인",shape=diamond,fillcolor="#fff2d9"];
 savememo [label="메모·작성자·시각 저장"];
 status [label="다음 처리 상태 선택\n신규→확인중→작업요청→조치완료"];
 authstatus [label="권한·현재 상태·version 확인",shape=diamond,fillcolor="#fff2d9"];
 update [label="events 상태 변경\nevent_changes 이력 추가"];
 reject [label="변경 거부 이유 표시\n최신 상태 다시 조회",fillcolor="#fce9e5"];
 refresh [label="상세·로그 화면 갱신",fillcolor="#e7f3e9"];
 log -> choice;choice -> image [label="사진"];image -> closeimage -> log;
 choice -> row [label="사건 행"];row -> detail -> action;
 action -> memo [label="메모"];memo -> authmemo;authmemo -> savememo [label="예"];authmemo -> reject [label="아니오"];
 action -> status [label="상태 변경"];status -> authstatus;authstatus -> update [label="예"];authstatus -> reject [label="아니오"];
 savememo -> refresh;update -> refresh;reject -> detail;refresh -> detail;
''')

diagram('06 운영 명령·순찰·교대 이력','06-command-history',r'''
 manage [label="로봇 관리 화면 표시",fillcolor="#e7f3e9"];
 select [label="대상 로봇 선택\nAMR1 또는 AMR2"];
 command [label="명령 선택\n순찰 시작·일시정지·재개·복귀·대피"];
 permission [label="명령 요청 권한 확인",shape=diamond,fillcolor="#fff2d9"];
 deny [label="무권한 요청 거부",fillcolor="#fce9e5"];
 requestid [label="request_id 생성\n중복 요청 키 확인"];
 save [label="commands 테이블 저장\n현재 상태: 요청됨"];
 dispatch [label="미션 모듈에 요청 전달"];
 ack [label="수락 결과 수신?",shape=diamond,fillcolor="#fff2d9"];
 accepted [label="수락됨·진행중 저장"];
 rejected [label="거절됨·사유 저장",fillcolor="#fce9e5"];
 result [label="완료 또는 실패 결과 수신"];
 update [label="명령 상태·사유·시각 저장\n명령 이력 화면 갱신"];
 patrol [label="순찰 ID·경로·시작/종료 저장\nP1~P7 방문 결과 저장"];
 handover [label="교대 ID·인계/인수 로봇\n사유·시각·결과 저장"];
 history [label="사건·명령·순찰·교대 이력\n기간·로봇·상태로 검색",fillcolor="#e7f3e9"];
 manage -> select -> command -> permission;permission -> deny [label="아니오"];permission -> requestid [label="예"];
 requestid -> save -> dispatch -> ack;ack -> accepted [label="수락"];ack -> rejected [label="거절/지연"];
 accepted -> result -> update;rejected -> update;update -> patrol -> handover -> history;
''')

E.indent(doc)
target=OUT/'화살표형_세부구현_플로우차트.drawio'
E.ElementTree(doc).write(target,encoding='utf-8',xml_declaration=True)
check=E.parse(target).getroot();assert len(check.findall('diagram'))==6
for d in check.findall('diagram'):
    ids={c.get('id') for c in d.findall('.//mxCell')}
    for c in d.findall('.//mxCell'):
        for k in ('source','target'):
            if c.get(k):assert c.get(k) in ids
print('Created',target,'with 6 detailed arrow-flow pages')
