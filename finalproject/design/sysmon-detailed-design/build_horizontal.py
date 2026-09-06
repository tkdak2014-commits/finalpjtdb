from pathlib import Path
import copy, json, subprocess, xml.etree.ElementTree as E

BASE=Path(__file__).parent.parent
OUT=Path(__file__).parent
doc=E.Element('mxfile',host='app.diagrams.net',type='device')

sources=[
 ('01 전체 플로우차트',BASE/'parking-dashboard-flowchart/01-overall.dot'),
 ('02 이벤트 저장 및 로그 반영',BASE/'parking-dashboard-flowchart/02-event-ingestion.dot'),
 ('03 로그 조회 및 이미지 확대',BASE/'parking-dashboard-flowchart/03-log-detail.dot'),
 ('04 이벤트 처리 상태',BASE/'parking-dashboard-flowchart/04-event-status.dot'),
 ('05 운영 명령 요청',BASE/'parking-dashboard-v2/05-command-flow.dot'),
 ('06 순찰·교대 및 이력',BASE/'parking-dashboard-v2/06-patrol-history.dot'),
 ('07 연동 인터페이스 및 검증',OUT/'07-interface.dot'),
 ('08 지도·상태·영상 갱신',OUT/'08-map-state-video.dot'),
 ('09 DB 및 데이터 연결',OUT/'09-data-model.dot'),
 ('10 크리티컬 항목·통합 검증',OUT/'10-validation.dot'),
]

def add_page(name,source,index):
    dot=source.read_text()
    dot=dot.replace('rankdir=TB','rankdir=LR')
    # Preserve the latest agreed event identity and update semantics.
    if index==2:
        dot=dot.replace('이벤트 ID / 발생 시각','메시지 ID·이벤트 ID / 발생 시각')
        dot=dot.replace('새 이벤트 처리 상태: 신규','신규 저장: 신규 / 보완 갱신: 처리 상태 유지')
    tmp=OUT/f'horizontal-{index:02d}.dot'
    tmp.write_text(dot)
    png=OUT/f'horizontal-{index:02d}.png'
    subprocess.run(['dot','-Tpng','-Gdpi=110',str(tmp),'-o',str(png)],check=True)
    data=json.loads(subprocess.check_output(['dot','-Tjson',str(tmp)]))
    _,_,width,height=map(float,data['bb'].split(','));pad=45
    extra=300 if index==1 else 90
    diagram=E.SubElement(doc,'diagram',name=name,id=f'horizontal-{index:02d}')
    model=E.SubElement(diagram,'mxGraphModel',grid='1',gridSize='10',page='1',pageScale='1',pageWidth=str(round(width+pad*2)),pageHeight=str(round(height+pad*2+extra)),background='#ffffff')
    root=E.SubElement(model,'root');E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0')
    nodes={}
    for n in data.get('objects',[]):
        if 'pos' not in n:continue
        idx=n['_gvid'];nodes[idx]=n
        x,y=map(float,n['pos'].split(','));w=float(n['width'])*72;h=float(n['height'])*72
        original=n.get('shape','rectangle')
        shape='rhombus' if original=='diamond' else ('note' if original=='note' else ('cylinder3' if original=='cylinder' else 'rectangle'))
        style=(f'shape={shape};whiteSpace=wrap;html=0;rounded=0;fillColor={n.get("fillcolor","#edf3f8")};'
               'strokeColor=#597185;strokeWidth=2;fontColor=#172434;fontFamily=Noto Sans CJK KR;fontSize=17;spacing=8;')
        cell=E.SubElement(root,'mxCell',id='n'+str(idx),parent='1',vertex='1',value=n.get('label','').replace('\\n','\n'),style=style)
        E.SubElement(cell,'mxGeometry',x=str(x-w/2+pad),y=str(height-y-h/2+pad),width=str(w),height=str(h),**{'as':'geometry'})
    for i,e in enumerate(data.get('edges',[])):
        style='edgeStyle=orthogonalEdgeStyle;rounded=0;curved=0;orthogonalLoop=1;jettySize=auto;endArrow=block;html=0;strokeColor=#597185;strokeWidth=2;fontFamily=Noto Sans CJK KR;fontSize=13;labelBackgroundColor=#ffffff;'
        if 'dashed' in e.get('style',''):style+='dashed=1;'
        cell=E.SubElement(root,'mxCell',id='e'+str(i),parent='1',edge='1',source='n'+str(e['tail']),target='n'+str(e['head']),value=e.get('label','').replace('\\n','\n'),style=style)
        E.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'})
    if index==1:
        y=height+pad+55
        title=E.SubElement(root,'mxCell',id='detail-title',parent='1',vertex='1',value='부분별 세부 기능 네모박스 추가 영역',style='shape=rectangle;whiteSpace=wrap;html=0;rounded=0;fillColor=#ffffff;strokeColor=none;fontColor=#172434;fontFamily=Noto Sans CJK KR;fontSize=18;fontStyle=1;align=left;')
        E.SubElement(title,'mxGeometry',x=str(pad),y=str(y-42),width=str(width),height='32',**{'as':'geometry'})
        labels=['인증·권한','지도·상태·영상','이벤트·증거사진','운영 명령','순찰·교대·이력']
        gap=18;bw=(width-gap*4)/5
        for j,label in enumerate(labels):
            cell=E.SubElement(root,'mxCell',id=f'detail-{j}',parent='1',vertex='1',value=label+'\n\n세부 기능 박스 추가',style='shape=rectangle;whiteSpace=wrap;html=0;rounded=0;fillColor=#f7f9fb;strokeColor=#8aa0b2;strokeWidth=2;dashed=1;fontColor=#597185;fontFamily=Noto Sans CJK KR;fontSize=16;')
            E.SubElement(cell,'mxGeometry',x=str(pad+j*(bw+gap)),y=str(y),width=str(bw),height='150',**{'as':'geometry'})

for i,(name,source) in enumerate(sources,1):add_page(name,source,i)

# UI pages are already landscape and angular.
ui=E.parse(BASE/'parking-dashboard-ui/parking-dashboard-ui.drawio').getroot()
for i,d in enumerate(ui,11):
    page=copy.deepcopy(d);page.set('id',f'horizontal-ui-{i}');page.set('name',f'{i:02d} '+d.get('name')[3:])
    for cell in page.findall('.//mxCell'):
        if cell.get('edge')=='1':
            parts=[p for p in cell.get('style','').split(';') if p and not p.startswith(('edgeStyle=','rounded=','curved=','orthogonalLoop=','jettySize='))]
            parts.extend(['edgeStyle=orthogonalEdgeStyle','rounded=0','curved=0','orthogonalLoop=1','jettySize=auto'])
            cell.set('style',';'.join(parts)+';')
    doc.append(page)

E.indent(doc)
target=OUT/'플로우차트_가로형_기능박스.drawio'
E.ElementTree(doc).write(target,encoding='utf-8',xml_declaration=True)

check=E.parse(target).getroot()
assert len(check.findall('diagram'))==13
for d in check.findall('diagram'):
    cells=d.findall('.//mxCell');ids={c.get('id') for c in cells}
    for c in cells:
        for key in ('source','target'):
            if c.get(key):assert c.get(key) in ids
        if c.get('edge')=='1':assert 'edgeStyle=orthogonalEdgeStyle' in c.get('style','')
print('Created',target,'with',len(check.findall('diagram')),'landscape pages')
