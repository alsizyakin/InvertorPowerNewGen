"""Clearances < 0.5 mm on the outer layers between exposed copper of different voltage domains (VDC, nodes, HS gate
domain, GND/logic) with the worst-case voltage at an 84 V bus. Written by the power reviewer (docs/reviews/05, P5).
Usage: hv.py board.kicad_pcb"""
import sys,math,re,numpy as np
sys.path.insert(0,"/home/alexey/Git/KiCad/InvertorPowerNewGen/tools/rev01_layout"); sys.dont_write_bytecode=True
import geom
fn=sys.argv[1]; Bd=geom.Board(fn)
import kpcb; K=kpcb.load(fn)
PH={'3':'C','2':'B','1':'A'}
HSG={'C100':'C','C101':'C','C104':'B','C105':'B','C108':'A','C109':'A'}
def dom(n):
    if n=='' : return None
    if n=='VDC': return ('VDC',)
    if n=='GND': return ('GND',)
    m=re.match(r'/Current_Sensor_(\d)/Phase_(IN|OUT)',n)
    if m: return ('node',PH[m.group(1)])
    m=re.match(r'/Driver_(\d)/(HO|HO_DRV|SW)$',n)
    if m: return ('hs',PH[m.group(1)])
    m=re.match(r'Net-\((C1\d\d)-Pad1\)',n)
    if m and m.group(1) in HSG: return ('hs',HSG[m.group(1)])
    m=re.match(r'Net-\(D([123])-K\)',n)
    if m: return ('hs',{'1':'C','2':'B','3':'A'}[m.group(1)])
    # snubber middle point X: at DC it sits on the far end of R - GND for the LS chains, the node for the HS chains (07 P9)
    m=re.match(r'Net-\(C11([2-7])-Pad2\)',n)
    if m: return ('GND',) if m.group(1) in '234' else ('node',{'5':'C','6':'B','7':'A'}[m.group(1)])
    return ('lv',)
def dv(a,b):
    if a is None or b is None or a==b: return 0
    t={a[0],b[0]}
    if a[0]==b[0]=='node': return 84
    if a[0]==b[0]=='hs': return 96
    if t=={'node','hs'}: return 12 if a[1]==b[1] else 96
    if t=={'VDC','GND'} or t=={'VDC','lv'}: return 84
    if 'VDC' in t and ('node' in t): return 84
    if 'VDC' in t and 'hs' in t: return 84
    if t=={'GND','lv'}: return 15
    if t=={'lv'}: return 15
    if 'node' in t: return 84
    if 'hs' in t: return 96
    return 0
# collect exposed pads on outer layers in window
win=(110,60,175,125)
pads=[]
for f in Bd.fps.values():
    pp,_=f.placed()
    for p in pp:
        if not (win[0]<p['x']<win[2] and win[1]<p['y']<win[3]): continue
        lays=['F.Cu','B.Cu'] if p['tht'] else [f.layer]
        for l in lays:
            rc=min(p['aw'],p['ah'])/2 if p['shape'] in ('circle','oval') else (0.25*min(p['aw'],p['ah']) if p['shape']=='roundrect' else 0)
            pads.append(dict(ref=f.ref,name=p['name'],l=l,net=p['net'],r=(p['x']-p['aw']/2+rc,p['y']-p['ah']/2+rc,p['x']+p['aw']/2-rc,p['y']+p['ah']/2-rc),rc=rc,circ=p['shape']=='circle',x=p['x'],y=p['y'],rad=p['aw']/2))
def rr(a,b): return geom.d_rect_rect(a,b)
res=[]
# pad-pad
for i,a in enumerate(pads):
    for b in pads[i+1:]:
        if a['l']!=b['l'] or a['net']==b['net']: continue
        v=dv(dom(a['net']),dom(b['net']))
        if v<50: continue
        d=rr(a['r'],b['r'])-a['rc']-b['rc']
        if d<0.6: res.append((round(d,3),v,a['l'],f"{a['ref']}.{a['name']}",a['net'][-14:],f"{b['ref']}.{b['name']}",b['net'][-14:],'pad-pad'))
# pad-track and pad-zone
segs=[s for s in K['segs'] if s['layer'] in ('F.Cu','B.Cu')]
for a in pads:
    for s in segs:
        if s['layer']!=a['l'] or s['net']==a['net']: continue
        v=dv(dom(a['net']),dom(s['net']))
        if v<50: continue
        d=geom.d_seg_rect(s['x1'],s['y1'],s['x2'],s['y2'],a['r'])-s['w']/2-a['rc']
        if d<0.6: res.append((round(d,3),v,a['l'],f"{a['ref']}.{a['name']}",a['net'][-14:],'track',s['net'][-14:],'pad-trk(mask)'))
for z in K['zones']:
    for l,pts in z['fills']:
        if l not in ('F.Cu','B.Cu') or len(pts)<3: continue
        P=np.array(pts); P2=np.roll(P,-1,axis=0)
        for a in pads:
            if a['l']!=l or a['net']==z['net']: continue
            v=dv(dom(a['net']),dom(z['net']))
            if v<50: continue
            r=a['r']
            m=(np.minimum(P[:,0],P2[:,0])<r[2]+0.7)&(np.maximum(P[:,0],P2[:,0])>r[0]-0.7)&(np.minimum(P[:,1],P2[:,1])<r[3]+0.7)&(np.maximum(P[:,1],P2[:,1])>r[1]-0.7)
            for (x1,y1),(x2,y2) in zip(P[m],P2[m]):
                d=geom.d_seg_rect(x1,y1,x2,y2,r)-a['rc']
                if d<0.6: res.append((round(d,3),v,l,f"{a['ref']}.{a['name']}",a['net'][-14:],'zone',z['net'][-14:],'pad-zone(mask)'))
best={}
for r in res:
    k=(r[3],r[5] if r[5]!='zone' and r[5]!='track' else r[5]+r[6])
    if k not in best or r[0]<best[k][0]: best[k]=r
for r in sorted(best.values()):
    if r[0]<0.5: print(r)
print('total flagged <0.5:',sum(1 for r in best.values() if r[0]<0.5))
