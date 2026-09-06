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

# Current agreed functional flows, without older UI tabs.
flow=E.parse(OUT.parent/'parking-dashboard-flowchart/parking-dashboard-flowchart.drawio').getroot()
for i,d in enumerate(list(flow)[:6]):
    c=copy.deepcopy(d)
    if i==1:
        for cell in c.findall('.//mxCell'):
            v=cell.get('value','')
            if 'ID / 발생 시각' in v:
                cell.set('value',v.replace('이벤트 ID / 발생 시각','메시지 ID·이벤트 ID / 발생 시각'))
            if '새 이벤트 처리 상태: 신규' in v:
                cell.set('value',v.replace('새 이벤트 처리 상태: 신규','신규 저장: 신규 / 보완 갱신: 처리 상태 유지'))
    doc.append(c)

graph('07 연동 인터페이스 및 검증','07-interface',r'''
 start [label="연동 데이터 형식 협의 시작",shape=ellipse,fillcolor="#e7f3e9"];
 contract [label="공통 내부 데이터 계약 작성\n상태·이벤트·명령 결과·순찰·교대\nID / 발생·수신 시각 / 지도·좌표계"];
 event [label="화재 이벤트 계약\nevent_id / message_id / occurred_at\nx,y / map_id / 위험도 상·중·하\n로봇1 증거 이미지 1장과 연결 ID"];
 mission [label="미션 계약\nrequest_id / robot_id / 실행 상태·사유\npatrol_id / visit_id / handover_id"];
 agree [label="필드·의미·생성 주체 합의?",shape=diamond,fillcolor="#fff2d9"];
 draft [label="미결정 항목·담당자 기록\n필드 정의 수정 후 다시 협의",fillcolor="#fce9e5"];
 sample [label="샘플 JSON·이미지 준비\n임시 HTTP / Mock 어댑터로 입력"];
 service [label="동일 서비스 함수에서 검증·저장\nDB·UI API·화면 연동 확인"];
 ros [label="ROS 토픽·메시지 확정?",shape=diamond,fillcolor="#fff2d9"];
 mock [label="샘플 기반 기능 개발·검증 계속\n실연동 완료와 구분해 기록"];
 adapter [label="ros_adapter에서 원본 → 내부 형식 변환\n수신: 상태·이벤트·결과 / 송신: 명령 요청"];
 verify [label="실제 데이터·샘플 결과 일치 검증\n좌표·사진 매칭 / 중복·역순 / 결과 상태"];
 end [label="인터페이스 버전·샘플·검증 결과 기록",shape=ellipse,fillcolor="#e7f3e9"];
 start -> contract;contract -> event;contract -> mission;
 event -> agree;mission -> agree;
 agree -> draft [label="아니오"];draft -> contract;
 agree -> sample [label="예"];sample -> service -> ros;
 ros -> mock [label="아니오"];ros -> adapter [label="예"];
 adapter -> verify -> end;mock -> end [label="샘플 검증 결과"];
''')

graph('08 지도·상태·영상 갱신','08-map-state-video',r'''
 start [label="로그인된 대시보드 초기 조회",shape=ellipse,fillcolor="#e7f3e9"];
 map [label="지도 버전·원점·해상도·좌표계 조회\n경로 / P1~P7 / 안전구역(polygon) / 도크"];
 rx [label="AMR1·AMR2 상태 수신\n배터리·임무 상태·좌표·수신 시각"];
 valid [label="ID·시각·순서 유효?",shape=diamond,fillcolor="#fff2d9"];
 discard [label="오류 기록 / 중복·오래된 값 반영 제외"];
 save [label="최신 상태 갱신·상태 이력 저장"];
 coord [label="좌표계·지도 버전 일치?",shape=diamond,fillcolor="#fff2d9"];
 yes [label="지도 좌표 → 화면 좌표 변환\n해당 로봇 / 사건 마커 표시"];
 no [label="위치 미확정 표시\n임의 좌표로 대체하지 않음",fillcolor="#fce9e5"];
 screen [label="배터리·임무·마지막 수신 시각 표시\n미수신 기준 초과 시 연결 끊김 표시"];
 video [label="영상 소스 4개 각각 연결\nAMR1 / AMR2 / 고정 웹캠1 / 웹캠2"];
 connected [label="해당 영상 수신 성공?",shape=diamond,fillcolor="#fff2d9"];
 stream [label="영상 영역에 최신 프레임 표시\n원본 영상 DB 저장 없음"];
 waiting [label="해당 영상만 연결 대기·단절 표시\n다른 영상과 상태 갱신 계속",fillcolor="#fce9e5"];
 loop [label="주기 조회 / 새 데이터 수신 때 갱신 반복",shape=ellipse,fillcolor="#e7f3e9"];
 start -> map;start -> rx;start -> video;
 rx -> valid;valid -> discard [label="아니오"];valid -> save [label="예"];
 save -> coord;map -> coord;coord -> yes [label="예"];coord -> no [label="아니오"];
 save -> screen;yes -> loop;no -> loop;screen -> loop;discard -> loop;
 video -> connected;connected -> stream [label="예"];connected -> waiting [label="아니오"];
 stream -> loop;waiting -> loop;
''')

graph('09 DB 및 데이터 연결','09-data-model',r'''
 users [label="users\n사용자 ID·계정·비밀번호 해시·권한",fillcolor="#fff2d9"];
 robots [label="robots / robot_latest_status\nAMR1·AMR2 기본 정보·최신 상태\nrobot_status_history: 상태 기록"];
 maps [label="maps / map_features / routes\n지도 버전·좌표 변환·P1~P7\n안전구역·도크·순찰 경로"];
 event [label="events\n이벤트 ID / 외부 이벤트 ID / 로봇 ID\n발생 시각·종류·좌표·위험도 상/중/하\n처리 상태·version·대표 이미지 경로",fillcolor="#fff2d9"];
 photo [label="증거 파일 저장소\n로봇1 사진 1장 / event_id 연결\n원본 영상은 저장하지 않음"];
 change [label="event_changes\n사건 ID·변경자·시각\n이전/새 상태·메모"];
 command [label="commands / command_updates\n요청 ID·요청자·로봇·명령·인자\n실행 상태·전송 상태·결과·사유",fillcolor="#fff2d9"];
 patrol [label="patrol_runs / patrol_visits\n순찰 ID·로봇·경로·시작/종료\n관측점 ID·방문 시각·결과"];
 handover [label="handovers / handover_updates\n교대 ID·인계/인수 로봇\n관련 순찰 ID·사유·시각·결과"];
 users -> change [label="변경자"];users -> command [label="요청자"];
 robots -> event [label="발생 소스"];robots -> command [label="대상"];
 maps -> robots [label="위치 참조"];maps -> event [label="사건 위치"];maps -> patrol [label="경로 버전"];
 event -> photo [label="경로 참조: 대표 1장"];event -> change [label="변경 이력"];
 command -> patrol [label="선택적 요청 연결"];robots -> patrol [label="수행 로봇"];
 patrol -> handover [label="교대 전·후 순찰"];
''')

graph('10 크리티컬 항목·통합 검증','10-validation',r'''
 start [label="① 연동 데이터 형식 확정\n상태·화재 좌표·위험도·사진\n명령 결과·순찰·교대 데이터 합의",shape=ellipse,fillcolor="#fff2d9"];
 build [label="② 데이터 저장·웹 표시 구현\n빈 DB → 샘플 입력 → 저장 → 로그 표시\n상세 처리·명령·이력 API 연결"];
 test [label="샘플 기반 검증 통과?",shape=diamond,fillcolor="#fff2d9"];
 fix [label="실패 기능 수정 후 재검증",fillcolor="#fce9e5"];
 live [label="실제 모듈·ROS 연동 준비?",shape=diamond,fillcolor="#fff2d9"];
 blocked [label="샘플 검증 완료 상태로 기록\n연동 담당·미확정 사항·확인 일정 관리"];
 real [label="③ 실제 환경 통합 검증\n로그인·권한 / 영상·상태·지도\n사건·사진 매칭 / 명령 결과 / 순찰·교대"];
 result [label="시나리오별 실제 결과 일치?",shape=diamond,fillcolor="#fff2d9"];
 repair [label="연동 오류 수정 / 담당 모듈과 재검증",fillcolor="#fce9e5"];
 movie [label="동작 영상 촬영·DB 증거 확보\n설계도·API 계약·검증 결과 정리"];
 end [label="구현·통합 검증 산출물 완료",shape=ellipse,fillcolor="#e7f3e9"];
 start -> build -> test;
 test -> fix [label="아니오"];fix -> build;
 test -> live [label="예"];live -> blocked [label="아니오"];live -> real [label="예"];
 real -> result;result -> repair [label="아니오"];repair -> real;
 result -> movie [label="예"];movie -> end;
''')

ui=E.parse(OUT.parent/'parking-dashboard-ui/parking-dashboard-ui.drawio').getroot()
for i,d in enumerate(ui):
    c=copy.deepcopy(d);c.set('id','ui-'+str(i));c.set('name',str(11+i)+' '+d.get('name')[3:]);doc.append(c)

E.indent(doc)
E.ElementTree(doc).write(OUT/'sysmon-detailed-design.drawio',encoding='utf-8',xml_declaration=True)
for d in doc:
    cells=d.findall('.//mxCell');ids=[c.get('id') for c in cells];assert len(ids)==len(set(ids))
    for c in cells:
        for k in ('source','target'):
            if c.get(k):assert c.get(k) in ids
print('Saved 13-page latest detailed design. All page IDs and connector references checked.')
