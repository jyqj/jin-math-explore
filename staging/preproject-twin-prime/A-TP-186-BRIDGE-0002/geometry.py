"""Exact reconstruction of the read Python schedule and Lean scalar geometry.

This checks transcribed finite definitions, not the integral algorithms or Lean.
Source: PrimeGaps186@61340d0b, Python build_inputs/_schedule; Challenge.lean.
"""
from fractions import Fraction as F
import hashlib
import json
import math

GROUP_NAMES = ['outer_h2','outer_h25','old_inner_h2','old_inner_h25','new_inner_h2','new_inner_h25']
TABLE_NAMES = ['outer_2','outer_5_2','inner_base_2','inner_base_5_2','inner_enlarged_2','inner_enlarged_5_2']
LOW_COUNTS = [10,22,5,7,6,11]
RANK_COUNTS = [6,12,1,2,4,5]


def require(test, message):
    if not test:
        raise ValueError(message)


def exact_json(x):
    if isinstance(x,F): return str(x)
    if isinstance(x,dict): return {str(k):exact_json(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [exact_json(v) for v in x]
    return x


def digest(x):
    return hashlib.sha256(json.dumps(exact_json(x),sort_keys=True,separators=(',',':')).encode()).hexdigest()


def build_geometry(targets):
    k,N = 40,98304
    gap,tau = F(1,10**7),F(1,10**10)
    rho = F(262499,10**6)
    rs = rho-gap
    S = F(2742997,10**7)/rs
    T0,T1 = 2-F(3,1000)-S,F(251,1000)/rs
    h,e,zeta = S/N,gap/rho,F(19037,100000)/rho
    sigmas = [F(100001,10**6),F(1,2)-F(40481,100000)+tau]
    cs = [(((1-5*s)/15,F(18,5)),((1-4*s)/16,F(7,2)),
           (F(3,80),F(3)) if family==0 else ((1-2*s)/20,F(16,5)))
          for family,s in enumerate(sigmas)]
    ladders=[]
    # Python's forward recurrence and termination predicate.
    for f,(T,eps,limit) in enumerate([(T0,F(1,10**6),F(12499,10**6)),(T1,F(1,10**7),F(253,20000))]):
        prev=F(0); E=rho*(S+T)-F(1,2); rows=[]
        for i in range(100):
            order=min(i//12+1,3); c,slope=cs[f][order-1]
            omega=min(limit,(c-eps-E+2*prev-gap)/slope)
            delta=c-slope*omega-eps; B=(F(1,2)+2*prev)/rho
            xi,a,b=delta/rho,B-T,B-S
            eta=xi if order<3 else (xi+S+T-B)/2
            require(prev<omega<=limit and delta>0,'ladder advance')
            rows.append(dict(family=f,index=i,order=order,previous=prev,omega=omega,
                             B=B,upper_B=(F(1,2)+2*omega)/rho,xi=xi,a=a,b=b,A=a+eta,C=b+eta))
            if omega==limit: break
            prev=omega
        else: raise ValueError('ladder did not terminate')
        ladders.append(rows)
    old,new=ladders
    require([len(old),len(new)]==[29,43],'ladder counts')
    shells = {
      'outer':[(new[0]['a'],zeta),(new[24]['a'],(S+e)/2),(S,S+e/2-23*(T1+e/2)/40)],
      'base':[(old[12]['b'],zeta),(old[24]['b'],(T0+e)/2),(T0,63*(T0+e/2)/160)],
      'enlarged':[(new[12]['b'],zeta),(new[24]['b'],(T1+e)/2),(T1,63*(T1+e/2)/160)],
      'full':[(S,zeta)]}
    cells={}
    for name,layers in shells.items():
        d=40 if name=='outer' else 39; lower=F(0); pieces=[]
        for upper,cap in layers:
            first=max(0,lower//h-d+1); last=min(N-k-1,upper//h-d)
            if first<=last: pieces.append([first,last,cap//h])
            lower=upper
        cells[name]=pieces
    # Explicit cutoffs in Challenge.lean; not generated from the Python cells.
    lean_cells={'outer':[[0,89196,68225],[89197,95598,49152],[95599,98263,46580]],
      'base':[[0,84930,68225],[84931,87194,44781],[87195,89524,35265]],
      'enlarged':[[0,85161,68225],[85162,87249,44976],[87250,89914,35419]],
      'full':[[0,98263,68225]]}
    require(cells==lean_cells,'Python/Lean cell masks differ')
    maxima={name:max((b+(40 if name=='outer' else 39))*h for a,b,c in pieces)
            for name,pieces in cells.items()}
    active_old=[r for r in old if r['B']<maxima['outer']+maxima['base']]
    active_new=[r for r in new if r['B']<maxima['outer']+maxima['enlarged']]
    require([len(active_old),len(active_new)]==[28,39],'active row count')
    groups=[]
    for role,rows,core,threshold,cellkey in [('outer',active_old+active_new,'a','A','outer'),
            ('old_inner',active_old,'b','C','base'),('new_inner',active_new,'b','C','enlarged')]:
        two=[r for r in rows if r['order']<3 and (role=='outer' or r['order']==2)]
        higher=[r for r in rows if r['order']==3]
        c2,c25=min(r[core] for r in two),min(r[core] for r in higher)
        d=40 if role=='outer' else 39
        for m,selected,lower,upper in [(F(2),two,c2,c25),(F(5,2),higher,c25,maxima[cellkey])]:
            pieces=[]
            for first,last,cap in cells[cellkey]:
                a=max(first,lower//h-d+1); b=min(last,upper//h)
                if a<=b:pieces.append([a,b,cap])
            U=min(r[threshold] for r in selected); xi=min(r['xi'] for r in selected)
            cap=max(c*h for a,b,c in pieces)
            p=min(max(xi//h+1,(U/(2*m))//h),min(cap//h,(U/m)//h))*h
            groups.append(dict(id=GROUP_NAMES[len(groups)],role=role,dimension=d,order=m,
                       activation=xi,threshold=U,lower=lower,upper=upper,cap=cap,split=p,
                       rows=[(r['family'],r['index']) for r in selected],pieces=pieces))
    # Directly transcribed Lean group definitions, a separate computation path.
    lean_groups=[
      (40,F(2),old[23]['xi'],S+e,new[0]['a'],new[24]['a'],49152*h,24576*h),
      (40,F(5,2),new[38]['xi'],S+e/2,new[24]['a'],98303*h,46580*h,19660*h),
      (39,F(2),old[23]['xi'],T0+e,old[12]['b'],old[24]['b'],44781*h,22390*h),
      (39,F(5,2),old[27]['xi'],T0+e/2,old[24]['b'],89563*h,35265*h,17912*h),
      (39,F(2),new[23]['xi'],T1+e,new[12]['b'],new[24]['b'],44976*h,22488*h),
      (39,F(5,2),new[38]['xi'],T1+e/2,new[24]['b'],89953*h,35419*h,17990*h)]
    fields=['dimension','order','activation','threshold','lower','upper','cap','split']
    for g,values in zip(groups,lean_groups):
        require(tuple(g[f] for f in fields)==values,'Python/Lean group parameters differ: '+g['id'])
    x=[g['activation'] for g in groups]; p=[g['split'] for g in groups]
    a=[F(1,20)*F(6,5)**j for j in range(10)]
    lows=[
      [x[0],3*x[0]/2,a[0],a[4],a[5],a[6],a[7],a[8],(a[8]+a[9])/2,a[9],p[0]],
      [x[1]*2**j for j in range(9)]+[F(1,100),F(3,200),F(9,400),F(27,800)]+a[:8]+[(a[7]+p[1])/2,p[1]],
      [x[2],a[0],a[4],a[6],a[8],p[2]],
      [x[3],2*x[3],F(1,100),F(27,800),a[3],a[5],a[6],p[3]],
      [x[4],a[1],a[4],a[5],a[7],a[8],p[4]],
      [x[5],2*x[5],16*x[5],64*x[5],256*x[5],F(9,400),a[1],a[3],a[5],a[6],a[7],p[5]]]
    ranks=[[F(j,6) for j in range(7)],[F(j,16) for j in range(9)]+[F(5,8),F(3,4),F(7,8),F(1)],
      [F(0),F(1)],[F(0),F(1,2),F(1)],[F(0),F(1,6),F(1,2),F(2,3),F(1)],
      [F(0),F(1,8),F(3,8),F(1,2),F(3,4),F(1)]]
    tasks=[]
    ah=F(*targets['a_h']);bh=F(*targets['b_h'])
    for gi,(g,low,rank) in enumerate(zip(groups,lows,ranks)):
        require(len(low)-1==LOW_COUNTS[gi] and len(rank)-1==RANK_COUNTS[gi],'schedule counts')
        require(all(u<v for u,v in zip(low,low[1:])),'low bins unordered')
        q0=g['threshold']/(g['order']+1)
        require(q0>=max(g['activation'],g['split']) and q0<g['cap'],'rank interval')
        for kind,boundaries in [('low',low),('rank_two',[q0+v*(g['cap']-q0) for v in rank]),('high',[g['split'],g['cap']])]:
            for i,(lo,hi) in enumerate(zip(boundaries,boundaries[1:])):
                local_index=len([t for t in tasks if t['group']==g['id']])
                parameters={} if kind=='high' else ({'low':str(lo),'high':str(hi),'slope':str(120 if gi==0 and i==2 else math.ceil(F(9 if gi==5 else 7)/hi))}
                        if kind=='low' else {'q_low':str(lo),'q_high':str(hi)})
                task=dict(group=g['id'],kind=kind,index=i,label=(f'L_{{{i+1}}}' if kind=='low' else f'P_{{{i+1}}}' if kind=='rank_two' else 'H'),parameters=parameters,source_group_id=g['id'])
                if gi<2:
                    q=targets[TABLE_NAMES[gi]][local_index][0]
                    task.update(young_q=q,young_denominator=10**6,young=str(F(q,10**6)))
                else:task['restoration_coefficient']=str(1-ah-bh if gi<4 else 1-bh)
                tasks.append(task)
    require(len(tasks)==97,'task count')
    clipping=[]
    for gi,g in enumerate(groups):
        for t in (t for t in tasks if t['group']==g['id'] and t['kind']=='low'):
            u=F(t['parameters']['high'])
            eligible=[ladders[f][j] for f,j in g['rows'] if ladders[f][j]['xi']<u]
            core='a' if gi<2 else 'b'; th='A' if gi<2 else 'C'
            py=max(g['lower'],min(max(r[core],r[th]-(g['order']-1)*u) for r in eligible)) if eligible else None
            extra=groups[gi-1]['rows'] if gi in (1,3,5) else []
            allrows=set(g['rows'])|set(extra)
            eligible2=[ladders[f][j] for f,j in allrows if ladders[f][j]['xi']<u]
            le=max(g['lower'],min(max(r[core],r[th]-((F(2) if r['order']<=2 else F(5,2))-1)*u) for r in eligible2)) if eligible2 else None
            clipping.append(dict(group=gi,low_index=t['index'],python_cutoff=py,lean_cutoff=le,
                equal=py==le,python_first=None if py is None else py//h-g['dimension']+1,
                lean_first=None if le is None else le//h-g['dimension']+1))
    require(all(c['equal'] for c in clipping),'low clipping mismatch')
    # Radius beyond 98263 makes all three inner masks zero. For each earlier
    # radius compare cap thresholds; inclusion then holds for ALL measures.
    def cap_at(name,r):
        return next((cap for lo,hi,cap in cells[name] if lo<=r<=hi),None)
    nested=0
    for r in range(98265):
        cb,ce,cf=(cap_at(name,r) for name in ('base','enlarged','full'))
        require(cb is None or (ce is not None and cb<=ce),'base not inside enlarged')
        require(ce is None or (cf is not None and ce<=cf),'enlarged not inside full')
        nested+=1
    require(0<abs(bh)<ah+bh<1,'face-envelope order')
    require(T0//h-39==89524 and T1//h-39==89914,'radial face cutoffs')
    return exact_json(dict(parameters=dict(h=h,rho=rho,rho_star=rs,S=S,T0=T0,T1=T1,e=e,zeta=zeta),
            cells=cells,groups=groups,tasks=tasks,clipping=clipping,
            checks=dict(all_ladder_counts=[len(old),len(new)],active_ladder_counts=[len(active_old),len(active_new)],
             matched_cell_shells=sum(map(len,cells.values())),matched_group_fields=48,matched_low_clippings=len(clipping),nested_radius_checks=nested,face_envelope_order_checked=True,task_count=97,
             low_count=sum(LOW_COUNTS),rank_count=sum(RANK_COUNTS),high_count=6)))
