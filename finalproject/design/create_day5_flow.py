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
    graphs.append((name,slug))

graph('01 전체 구조','sysmon-day5-overview',r'''
 detection [label="감지 모듈 / 카메라\n영상 · 이상 감지 결과",fillcolor="#f2f2f2"];
 amr [label="AMR 모듈 / 로봇 1·2\n영상 · 배터리 · 위치 · 임무 상태",fillcolor="#f2f2f2"];
 rx [label="Sysmon 수신부\n로봇 ID로 데이터 구분"];
 process [label="Flask 서버 / 데이터 처리\n검증 · 중복 확인 · 저장"];
 stream [label="영상 / 최신 상태 전달\n연결 끊김 표시"];
 db [label="SQLite DB\nusers / robot_status / events",shape=cylinder,fillcolor="#fff2d9"];
 auth [label="로그인 / 세션 인증\n관리자 계정 확인"];
 camera [label="Camera 페이지\n영상 2개 · 로봇별 상태 · 최근 알림",fillcolor="#eaf5ec"];
 report [label="DB 페이지\n조건 검색 · 이벤트 목록 · 근거 이미지",fillcolor="#eaf5ec"];
 detection -> rx [label="영상 / 이벤트"];
 amr -> rx [label="영상 / 상태"];
 rx -> stream [label="영상 / 최신 상태"];
 rx -> process [label="상태 / 이벤트"];
 process -> db [label="저장"];
 db -> auth [label="계정 조회"];
 auth -> camera [label="인증 성공"];
 stream -> camera [label="화면 갱신"];
 db -> report [label="서버를 통한 조회"];
 camera -> report [label="DB 탭 / 이벤트 선택"];
 report -> camera [label="Camera 탭"];
''','TB')

graph('02 로그인 및 화면 흐름','sysmon-day5-user-flow',r'''
 start [label="관리자 접속",shape=ellipse,fillcolor="#dcebdc"];
 login [label="로그인 페이지 표시\n아이디 / 비밀번호 입력"];
 check [label="인증 성공?",shape=diamond,fillcolor="#fff2d9"];
 error [label="로그인 오류 표시\n재입력",fillcolor="#fce9e5"];
 home [label="세션 생성 → Camera 페이지 표시\n서버에 최신 상태 / 이벤트 조회"];
 count [label="이벤트가 있는가?",shape=diamond,fillcolor="#fff2d9"];
 empty [label="빈 목록 표시\n감지 이벤트가 없습니다"];
 rows [label="최근 이벤트 / 알림 표시"];
 monitor [label="영상 2개 / 로봇별 상태 모니터링\n신호 없으면 연결 대기 표시\n수신 데이터로 화면 지속 갱신"];
 select [label="관리자 화면 조작",shape=diamond,fillcolor="#fff2d9"];
 search [label="DB 탭 → 날짜 / 로봇 / 유형 검색\n서버가 SQLite 조회"];
 found [label="검색 결과 존재?",shape=diamond,fillcolor="#fff2d9"];
 none [label="검색 결과 없음 표시"];
 list [label="이벤트 목록 표시 → 행 선택"];
 detail [label="상세 조회\n시간 · 위치 · 위험 등급 · 근거 이미지"];
 logout [label="로그아웃 → 세션 종료",shape=ellipse,fillcolor="#dcebdc"];
 start -> login -> check;
 check -> home [label="예"]; check -> error [label="아니오"];error -> login;
 home -> count;count -> empty [label="아니오"];count -> rows [label="예"];
 empty -> monitor;rows -> monitor;monitor -> select;
 select -> search [label="DB 조회"]; select -> logout [label="로그아웃"];
 select -> monitor [label="계속 관제"];
 search -> found;found -> none [label="아니오"];none -> search [label="조건 변경"];
 found -> list [label="예"];list -> detail;detail -> search [label="다시 검색"];
 detail -> monitor [label="Camera 탭"];
 logout -> login [label="로그인 화면 복귀"];
''')

graph('03 초기화 및 데이터 처리','sysmon-day5-data-flow',r'''
 start [label="Sysmon 시작",shape=ellipse,fillcolor="#dcebdc"];
 init [label="Flask / 수신부 시작\n페이지 템플릿 · 빈 화면 데이터셋 준비\nSQLite 테이블 준비 (기존 DB 보존)"];
 setup [label="시연 준비\n관리자 계정 사전 등록\n이벤트 0건인 시연용 DB 사용",shape=note,fillcolor="#fff2d9"];
 wait [label="데이터 수신 대기 / 반복\n로그인 여부와 무관하게 동작"];
 input [label="외부 입력\n감지 모듈 / AMR 모듈\n또는 시연 데이터",fillcolor="#f2f2f2"];
 kind [label="수신 데이터 종류",shape=diamond,fillcolor="#fff2d9"];
 video [label="영상 전달 / 최신 프레임 갱신\n웹의 해당 영상 영역에 표시"];
 status [label="로봇 ID별 상태 저장·갱신\n배터리 · 위치 · 임무 · 마지막 수신 시각"];
 valid [label="이벤트 필수값 유효?",shape=diamond,fillcolor="#fff2d9"];
 reject [label="오류 기록\n잘못된 데이터 저장 제외",fillcolor="#fce9e5"];
 duplicate [label="이미 저장한 이벤트 ID?",shape=diamond,fillcolor="#fff2d9"];
 skip [label="중복 저장 생략"];
 save [label="근거 이미지 저장\nSQLite events INSERT\n시간 · 로봇 · 위치 · 유형 · 측정값 · 위험 등급"];
 ok [label="저장 성공?",shape=diamond,fillcolor="#fff2d9"];
 failed [label="저장 실패 기록 / 오류 표시\n재시도 대기열 보관 (설계 제안)",fillcolor="#fce9e5"];
 update [label="DB에서 최신 목록 조회 → 웹에 전달\n접속 중인 관제 화면 / 알림 갱신\n미접속이면 다음 로그인 시 저장 이력 조회",fillcolor="#eaf5ec"];
 start -> init;setup -> init [style=dashed,label="초기 시연 조건"];
 init -> wait;input -> wait [label="영상 / 상태 / 이벤트"];
 wait -> kind [label="수신됨"];
 kind -> video [label="영상"];video -> wait [label="다음 프레임"];
 kind -> status [label="상태"];status -> update;
 kind -> valid [label="감지 이벤트"];
 valid -> reject [label="아니오"];reject -> wait;
 valid -> duplicate [label="예"];duplicate -> skip [label="예"];skip -> wait;
 duplicate -> save [label="아니오"];save -> ok;
 ok -> failed [label="아니오"];failed -> save [label="재시도"];
 ok -> update [label="예"];update -> wait [label="계속 수신"];
''')

# Include earlier mockups as editable supporting pages, without retaining the superseded flow.
old=E.parse(OUT/'sysmon-ui-mockup.drawio').getroot()
for original,title,ident in [(old[0],'04 UI 목업 (화면 구성 참고)','ui-reference'),(old[2],'05 DB 구조 (프로젝트 초안)','db-reference')]:
    d=copy.deepcopy(original);d.set('name',title);d.set('id',ident)
    for c in d.findall('.//mxCell'):
        v=c.get('value','')
        v=v.replace('robots · 로봇 최신 상태','robot_status · 로봇 최신 상태').replace('FK → robots','FK → robot_status').replace('robots 1 : N events','robot_status 1 : N events').replace('robots 최신 상태','robot_status 최신 상태')
        v=v.replace('연결: 정상     배터리: 78%     순찰 상태: 순찰 중','로봇 1: 정상 / 78% / 순찰 중     로봇 2: 정상 / 65% / 대기')
        v=v.replace('연결: 대기     배터리: —     순찰 상태: 알 수 없음','로봇 1: 연결 대기 / 상태 미수신     로봇 2: 연결 대기 / 상태 미수신')
        v=v.replace('영상 2개 기준','영상 2개 · 로봇별 상태 기준')
        v=v.replace('카메라 1 · 전방 영상','영상 소스 1 (팀 협의)').replace('카메라 2 · 보조 영상','영상 소스 2 (팀 협의)')
        v=v.replace('확인 처리','확인 처리 (선택 기능)')
        if v:c.set('value',v)
    doc.append(d)
E.indent(doc)
target=OUT/'sysmon-day5-flow-concept.drawio'
E.ElementTree(doc).write(target,encoding='utf-8',xml_declaration=True)
for d in doc:
    cells=d.findall('.//mxCell');ids=[c.get('id') for c in cells]
    assert len(ids)==len(set(ids))
    for c in cells:
        for k in ('source','target'):
            if c.get(k):assert c.get(k) in ids
print('Created 5-page draw.io document and 3 flow PNGs. XML IDs and edge references checked.')
