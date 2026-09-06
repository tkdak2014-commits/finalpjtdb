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

graph('01 전체 플로우차트','01-overall',r'''
 start [label="시작",shape=ellipse,fillcolor="#e7f3e9"];
 setup [label="Flask 서버 / SQLite / 수신부 준비\n페이지 구성 · 빈 화면 데이터셋 생성\n시연 DB: 계정·지도 등록, 이벤트 0건"];
 login [label="로그인 화면 표시\n아이디 / 비밀번호 입력"];
 auth [label="로그인 성공?",shape=diamond,fillcolor="#fff2d9"];
 err [label="오류 표시 / 재입력",fillcolor="#fce9e5"];
 dash [label="대시보드 표시\nAMR1·AMR2 상태 / 지도·7관측점 / 영상\n이벤트 없으면 빈 로그 표시",fillcolor="#e7f3e9"];
 receive [label="백그라운드 데이터 수신\n샘플 HTTP → 추후 ROS 연동\n로그인 여부와 무관하게 계속 수신"];
 state [label="로봇 상태·위치 / 영상 갱신\n연결 끊김은 소스별로 표시"];
 event [label="화재 이벤트 + 로봇1 증거 이미지 수신\n검증 → 이미지 파일·DB 저장\n상세 흐름: 02 탭"];
 log [label="이벤트 로그 갱신\n발생 시각 / 종류 / 발생 좌표\n위험도 상·중·하 / 로봇1 이미지 1장",fillcolor="#e7f3e9"];
 action [label="사용자 선택",shape=diamond,fillcolor="#fff2d9"];
 detail [label="이벤트 상세 / 이미지 확대\n처리 상태 변경·메모 기록\n03·04 탭"];
 commands [label="운영 명령 요청 / 결과 확인\n05 탭"];
 history [label="사건·명령·순찰·교대 이력 검색\n06 탭"];
 end [label="로그아웃\n사용자 세션만 종료",shape=ellipse,fillcolor="#e7f3e9"];
 start -> setup;
 setup -> login [label="사용자 화면"];
 setup -> receive [label="독립 수신 작업"];
 login -> auth;auth -> err [label="아니오"];err -> login;
 auth -> dash [label="예"];
 receive -> state [label="상태 / 영상"];state -> dash [label="최신값 반영"];
 receive -> event [label="감지 이벤트"];event -> log [label="저장 성공 후"];
 dash -> log [label="DB 조회 / 빈 목록 또는 저장 이력"];
 log -> action;
 action -> detail [label="사건 / 이미지"];
 action -> commands [label="로봇 관리"];
 action -> history [label="이력"];
 action -> end [label="로그아웃"];
''')

graph('02 이벤트 저장 및 로그 반영','02-event-ingestion',r'''
 start [label="화재 이벤트 수신",shape=ellipse,fillcolor="#e7f3e9"];
 payload [label="이벤트 ID / 발생 시각 / 종류 / 발생 좌표\n위험도: 상·중·하\n동일 이벤트에 연결된 로봇1 증거 이미지 1장"];
 idcheck [label="ID·출처·메시지 형식 유효?",shape=diamond,fillcolor="#fff2d9"];
 bad [label="오류 기록 / 보완 요청\n유효한 이벤트처럼 표시하지 않음",fillcolor="#fce9e5"];
 duplicate [label="이미 처리한 메시지?",shape=diamond,fillcolor="#fff2d9"];
 skip [label="중복 행 생성 생략\n다음 메시지 대기"];
 enrich [label="좌표·위험도·증거 수신 여부 확인\n좌표: 이벤트 위치 / 지도 좌표계 확인\n이미지: event_id 일치 확인"];
 complete [label="필수 표시 정보가 모두 있는가?",shape=diamond,fillcolor="#fff2d9"];
 partial [label="받은 증거 이미지는 파일 저장\n누락만 표시: 좌표 미확정 / 등급 미수신 / 이미지 대기\n일부 누락만으로 화재 기록을 버리지 않음",fillcolor="#fce9e5"];
 full [label="증거 이미지 파일 저장\n기존 실시간 영상과 별개로 보존"];
 db [label="SQLite 이벤트 저장 / 보완 갱신\n시각·종류·좌표·위험도·로봇 ID·이미지 경로\n새 이벤트 처리 상태: 신규"];
 ok [label="저장 성공?",shape=diamond,fillcolor="#fff2d9"];
 fail [label="실패 기록 / 재처리 대상으로 보관\n저장 완료로 표시하지 않음",fillcolor="#fce9e5"];
 api [label="Flask API로 최신 DB 내용 조회"];
 log [label="웹 이벤트 로그에 한 행 표시\n14:32 | 화재 발생 | (12.4, 8.1) | 상 | 사진 1장\n시연 예시 / 누락 정보는 대기 표시",fillcolor="#e7f3e9"];
 wait [label="다음 수신 / 누락 정보 보완 대기",shape=ellipse,fillcolor="#e7f3e9"];
 start -> payload -> idcheck;
 idcheck -> bad [label="아니오"];idcheck -> duplicate [label="예"];
 duplicate -> skip [label="예"];duplicate -> enrich [label="아니오"];
 enrich -> complete;complete -> full [label="예"];complete -> partial [label="아니오"];
 full -> db;partial -> db [label="가능한 정보 우선 보존"];
 db -> ok;ok -> fail [label="아니오"];ok -> api [label="예"];
 api -> log -> wait;
 bad -> wait;skip -> wait;fail -> wait;
''')

graph('03 로그 조회 및 이미지 확대','03-log-detail',r'''
 start [label="대시보드 이벤트 로그",shape=ellipse,fillcolor="#e7f3e9"];
 rows [label="발생 시각 / 이벤트 종류 / 발생 좌표\n위험도 상·중·하 / 로봇1 증거 이미지 1장"];
 click [label="사용자 선택",shape=diamond,fillcolor="#fff2d9"];
 photo [label="이미지 클릭\n해당 이벤트의 증거 이미지 확대"];
 event [label="행 클릭 → 이벤트 상세 조회\n기본 정보·처리 상태·메모·변경 이력"];
 op [label="상세 화면 동작",shape=diamond,fillcolor="#fff2d9"];
 status [label="처리 상태 변경 요청\n04 상태 처리 흐름 적용"];
 memo [label="메모 입력 → 권한 확인\n메모·작성자·시각 저장"];
 refresh [label="DB 저장 후 상세 화면 재조회\n처리 결과·변경 이력 표시"];
 back [label="닫기 / 로그로 돌아가기",shape=ellipse,fillcolor="#e7f3e9"];
 note [label="위험도와 처리 상태는 다른 항목\n로그: 위험도 상·중·하\n상세: 신규·확인중·작업요청·조치완료",shape=note,fillcolor="#fff2d9"];
 start -> rows -> click;
 click -> photo [label="이미지"];photo -> back [label="확대 닫기"];
 click -> event [label="사건 행"];event -> op;
 op -> status [label="상태 변경"];op -> memo [label="메모"];
 op -> back [label="닫기"];
 status -> refresh;memo -> refresh;refresh -> back;
 note -> event [style=dashed];
''')

graph('04 이벤트 처리 상태','04-event-status',r'''
 new [label="신규\n화재 이벤트 저장 시 생성",shape=ellipse,fillcolor="#fce9e5"];
 request1 [label="담당자가 확인 시작 요청"];
 check1 [label="권한·현재 상태·버전 유효?",shape=diamond,fillcolor="#fff2d9"];
 reviewing [label="확인중\n상태 + 변경 이력 저장",fillcolor="#fff2d9"];
 request2 [label="담당자가 작업요청 등록\n조치 요청 내용 입력"];
 check2 [label="권한·현재 상태·버전 유효?",shape=diamond,fillcolor="#fff2d9"];
 requested [label="작업요청\n상태 + 변경 이력 저장",fillcolor="#fff2d9"];
 request3 [label="담당자가 조치 결과 입력\n조치완료 요청"];
 check3 [label="권한·현재 상태·버전 유효?",shape=diamond,fillcolor="#fff2d9"];
 completed [label="조치완료\n상태 + 변경 이력 저장",shape=ellipse,fillcolor="#e7f3e9"];
 reject [label="요청 거부 / 이유 표시\n현재 상태 유지 · 최신 상태 재조회",fillcolor="#fce9e5"];
 note [label="매 변경마다 담당자·시각·이전/새 상태·메모 기록\n작업요청은 시설 조치 기록이며 로봇 명령과 별개\n각 저장 성공 후 상세 UI 갱신",shape=note,fillcolor="#edf3f8"];
 new -> request1 -> check1;
 check1 -> reviewing [label="예"];check1 -> reject [label="아니오"];
 reviewing -> request2 -> check2;
 check2 -> requested [label="예"];check2 -> reject [label="아니오"];
 requested -> request3 -> check3;
 check3 -> completed [label="예"];check3 -> reject [label="아니오"];
 note -> requested [style=dashed];
''')

# Carry forward still-applicable operating-command and patrol/handover subflows.
previous=E.parse(OUT.parent/'parking-dashboard-v2/parking-dashboard-design-v2.drawio').getroot()
for index,title,slug,png in [
    (4,'05 운영 명령 요청','05-commands','05-command-flow.png'),
    (5,'06 순찰·교대 및 이력','06-history','06-patrol-history.png'),
]:
    d=copy.deepcopy(previous[index]);d.set('name',title);d.set('id',slug);doc.append(d)
    (OUT/(slug+'.png')).write_bytes((OUT.parent/'parking-dashboard-v2'/png).read_bytes())
E.indent(doc)
E.ElementTree(doc).write(OUT/'parking-dashboard-flowchart.drawio',encoding='utf-8',xml_declaration=True)
for d in doc:
    cells=d.findall('.//mxCell');ids=[c.get('id') for c in cells]
    assert len(ids)==len(set(ids))
    for c in cells:
        for k in ('source','target'):
            if c.get(k):assert c.get(k) in ids
print('Created 6-page draw.io flowchart and PNG previews; XML references validated.')
