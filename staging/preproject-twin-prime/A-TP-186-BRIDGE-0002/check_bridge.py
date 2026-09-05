"""152-target conditional endpoint bridge; exact tests, not integral proofs.

Usage: python3 -B check_bridge.py --self-test
       python3 -B check_bridge.py --receipt fresh.json
No network or external libraries. It never reports that Lean axioms are proved.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse
import copy
import hashlib
import json
import math
import sys
from geometry import build_geometry,digest,GROUP_NAMES,TABLE_NAMES,require
from upstream_assembler import round_rows,assemble_model,key

HERE=Path(__file__).resolve().parent
PIN='61340d0b74163003b32756bb16e91d9209a5e330'
TARGETS_SHA256='4f398b1576b29b292a9ab709734ffcd28b95d7ba388e9dd063e11ccfed1a1467'


def read_json(path):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ValueError('duplicate JSON key: '+k)
            d[k]=v
        return d
    return json.loads(path.read_text(),object_pairs_hook=pairs,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))


def rational(v):
    if type(v) not in (str,int):raise ValueError('exact rational string/integer required')
    return F(v)


def interval(v,positive=False):
    require(type(v) is dict and set(v)=={'lower','upper'},'interval shape')
    lo,hi=rational(v['lower']),rational(v['upper'])
    require(lo<=hi and (not positive or lo>=0),'invalid interval order/sign')
    return lo,hi


def as_interval(lo,hi=None):
    return {'lower':str(lo),'upper':str(lo if hi is None else hi)}


def fixed_inventory(targets,geo):
    records=[]
    fixed=F(targets['cap_bounds']['I_lower'],10**24)
    for gi,(name,table) in enumerate(zip(GROUP_NAMES,TABLE_NAMES)):
        tasks=[t for t in geo['tasks'] if t['group']==name]
        require(len(tasks)==len(targets[table]),'table length mismatch')
        for row_index,(task,row) in enumerate(zip(tasks,targets[table])):
            for field,col,lean in ([('root_square',1,'physicalSourceOuterRoot'),('outer_face_square',2,'physicalSourceOuterFace')]
                                  if gi<2 else [('inner_face',0,'physicalSourceInnerMass')]):
                records.append(dict(id=f'G{gi}:R{row_index:02d}:{field}',group=name,kind=task['kind'],
                    task_index=task['index'],lean_group=gi,lean_row=row_index,field=field,
                    lean_expression=f'{lean} {gi} {row_index}',direction='upper',
                    relative_units=row[col],absolute_bound=str(fixed*F(row[col],10**18)),
                    numerical_evidence='not_acquired'))
    for name,expr,direction in [('I_lower','trialIH','lower'),('I_upper','trialIH','upper'),('J_lower','trialJLambdaH','lower')]:
        records.append(dict(id='CAP:'+name,lean_expression=expr,direction=direction,
                    absolute_bound=str(F(targets['cap_bounds'][name],10**24)),numerical_evidence='not_acquired'))
    require(len(records)==152 and len({r['id'] for r in records})==152,'152-target inventory')
    return records


def compact_coverage(targets,geo):
    inv=fixed_inventory(targets,geo)
    return dict(schema='tp152-target-ledger/v1',source_commit=PIN,
       geometry_sha256=digest(geo),targets_sha256=TARGETS_SHA256,
       source_normalizer=str(F(targets['cap_bounds']['I_lower'],10**24)),
       source_scale=10**18,source_direction='upper',
       source_columns=['id','lean_group','lean_row','field','relative_units'],
       source_targets=[[r[k] for k in ['id','lean_group','lean_row','field','relative_units']] for r in inv[:149]],
       lean_functions={'root_square':'physicalSourceOuterRoot','outer_face_square':'physicalSourceOuterFace','inner_face':'physicalSourceInnerMass'},
       cap_columns=['id','lean_expression','direction','absolute_bound'],
       cap_targets=[[r[k] for k in ['id','lean_expression','direction','absolute_bound']] for r in inv[149:]],
       group_task_counts=[[61,30,6], [17,35,7,10,11,17]],
       numerical_evidence='not_acquired_for_all_152')


def validate(receipt,targets,geo):
    """Accepts only arithmetic domination, conditional on genuine enclosures.

    Provenance, masks' analytic meaning and interval algorithm correctness are
    not inferable from a JSON report; those obligations cannot be toggled away.
    """
    problems=[]; failed=[]; inv=fixed_inventory(targets,geo)
    expected={key(t):t for t in geo['tasks']}; rows=receipt['components']; by_key={}
    for row in rows:
        task=row['task']
        require(type(task.get('index')) is int,'task index must be integer')
        k=key(task)
        require(k in expected and task==expected[k] and k not in by_key,'task identity/coverage')
        needed={'root_square','outer_face_square'} if task['group'].startswith('outer') else {'inner_face'}
        require(set(row['raw_forms'])==needed,'raw form identity')
        for v in row['raw_forms'].values():interval(v,True)
        by_key[k]=row
    require(set(by_key)==set(expected),'missing task')
    if 'geometry_sha256' in receipt:require(receipt['geometry_sha256']==digest(geo),'geometry hash')
    if 'source_commit' in receipt:require(receipt['source_commit']==PIN,'source commit')
    cap=receipt['cap']; forms=cap['normalized_forms']
    ilo,ihi=interval(forms['denominator'],True); require(ilo>0,'nonpositive denominator')
    reported_jlo,reported_jhi=interval(cap['hybrid_numerator'])
    # Recombine signed inputs independently: b<0 means UPPER tail endpoint.
    z0lo,z0hi=interval(forms['J0'],True)
    zplo,zphi=interval(forms['Jplus'],True)
    ztlo,zthi=interval(forms['Jtail'],True)
    a,b=F(*targets['a_h']),F(*targets['b_h']); c=a+b
    require(c>0 and b<0,'signed-coefficient contract')
    jlo=z0lo+c*zplo+b*zthi; jhi=z0hi+c*zphi+b*ztlo
    if reported_jhi<jlo or reported_jlo>jhi:problems.append('reported signed numerator disjoint from recomputed enclosure')
    actual_units=cap['rounded_units']
    require(set(actual_units)=={'I_lower','I_upper','J_lower'} and all(type(x) is int for x in actual_units.values()),'cap units shape/type')
    derived_units={'I_lower':math.floor(ilo*10**24),'I_upper':math.ceil(ihi*10**24),'J_lower':math.floor(reported_jlo*10**24)}
    if actual_units!=derived_units:problems.append('cap directed rounding mismatch')
    require(actual_units['I_lower']>0,'fresh normalization positive')
    # Recompute every cached row field from its raw endpoints, never trust passed.
    recomputed=round_rows(cap,rows,targets)
    for old,new in zip(rows,recomputed):
        require(type(old.get('component_relative_units')) is int,'component cache type')
        require(type(old.get('raw_relative_units')) is dict and all(type(u) is int for u in old['raw_relative_units'].values()),'raw cache types')
        for f in ('raw_relative_units','component_relative_units','normalized_loss_upper'):
            if old.get(f)!=new[f]:problems.append('stale row cache: '+str(key(old['task']))+':'+f)
    aggregate=assemble_model(cap,recomputed,geo['tasks'])
    for f,value in aggregate.items():
        if f in receipt and receipt[f]!=value:problems.append('stale aggregate cache: '+f)
    for target in inv:
        if target['id'].startswith('CAP:'):
            actual={'CAP:I_lower':ilo,'CAP:I_upper':ihi,'CAP:J_lower':jlo}[target['id']]
        else:
            k=(target['group'],target['kind'],target['task_index'])
            actual=rational(by_key[k]['raw_forms'][target['field']]['upper'])
        limit=F(target['absolute_bound'])
        good=actual<=limit if target['direction']=='upper' else actual>=limit
        if not good:failed.append(target['id'])
    # Rounded-only normalization transfer, reported separately as sufficient.
    d=F(actual_units['I_lower'],10**24); fixed=F(targets['cap_bounds']['I_lower'],10**24)
    rounded_failed=[]; invariant_count=0
    for t in inv[:149]:
        k=(t['group'],t['kind'],t['task_index']); row=recomputed[rows.index(by_key[k])]
        u=row['raw_relative_units'][t['field']]
        if d*u>fixed*t['relative_units']:rounded_failed.append(t['id'])
        if u<=t['relative_units']:invariant_count+=1
    ok=not problems and not failed
    return dict(endpoint_domination_pass=not failed,arithmetic_integrity_pass=not problems,
        conditional_arithmetic_pass=ok,verdict='CONDITIONAL_ARITHMETIC_PASS' if ok else 'FAIL',
        target_count=152,failed_target_count=len(failed),failed_targets=failed,
        problems=problems,rounded_only_sufficient_failures=rounded_failed,
        naive_relative_units_within_fixed_table=invariant_count,
        recomputed_upstream_aggregate=aggregate,axioms_discharged=False,
        actual_integral_evaluation=False,semantic_binding='unverified_external_obligation')


def synthetic_fixture(targets,geo,scale=F(1)):
    """Dyadic synthetic endpoint fixtures; explicitly NOT real integral values."""
    D=2**256
    down=lambda v:F(math.floor(v*D),D)
    up=lambda v:F(math.ceil(v*D),D)
    I0=F(targets['cap_bounds']['I_lower'],10**24);Ip=F(targets['cap_bounds']['I_upper'],10**24)
    J=F(targets['cap_bounds']['J_lower'],10**24)
    il,iu=scale*up(I0),scale*down(Ip); j=scale*up(J)
    cap=dict(normalized_forms={'denominator':as_interval(il,iu),'J0':as_interval(j),'Jplus':as_interval(0),'Jtail':as_interval(0)},
             hybrid_numerator=as_interval(j),rounded_units={'I_lower':math.floor(il*10**24),'I_upper':math.ceil(iu*10**24),'J_lower':math.floor(j*10**24)})
    inv=fixed_inventory(targets,geo); values={}
    for t in inv[:149]:values.setdefault((t['group'],t['kind'],t['task_index']),{})[t['field']]=as_interval(scale*down(F(t['absolute_bound'])))
    rows=[{'task':copy.deepcopy(t),'raw_forms':values[key(t)]} for t in geo['tasks']]
    rows=round_rows(cap,rows,targets)
    return dict(assemble_model(cap,rows,geo['tasks']),cap=cap,components=rows,
                fixture_kind='SYNTHETIC_NOT_PHYSICAL',source_commit=PIN,geometry_sha256=digest(geo))


def self_test(targets,geo):
    good=synthetic_fixture(targets,geo); base=validate(good,targets,geo)
    require(base['conditional_arithmetic_pass'],'positive fixture did not pass')
    doubled=synthetic_fixture(targets,geo,F(2)); double=validate(doubled,targets,geo)
    require(doubled['passed'] and not double['conditional_arithmetic_pass'],'scale separation failed')
    require(double['failed_target_count']==150 and double['naive_relative_units_within_fixed_table']==149,'scale fixture counts')
    require(doubled['final_margin_lower']==good['final_margin_lower'],'scale invariance failed')
    require([r['raw_relative_units'] for r in doubled['components']]==[r['raw_relative_units'] for r in good['components']],'relative units changed under scale')
    tests=[]
    def bad(name,mutate):
        r=copy.deepcopy(good);mutate(r)
        try: rejected=not validate(r,targets,geo)['conditional_arithmetic_pass']
        except (ValueError,KeyError,TypeError,ZeroDivisionError):rejected=True
        require(rejected,'bad fixture accepted: '+name);tests.append(dict(name=name,rejected=True))
    bad('missing_component',lambda r:r['components'].pop())
    bad('duplicate_component',lambda r:r['components'].append(copy.deepcopy(r['components'][0])))
    bad('missing_raw_form',lambda r:r['components'][0]['raw_forms'].pop('root_square'))
    bad('changed_task_geometry',lambda r:r['components'][0]['task']['parameters'].update(high='1'))
    bad('changed_geometry_digest',lambda r:r.update(geometry_sha256='0'*64))
    bad('changed_source_commit',lambda r:r.update(source_commit='0'*40))
    bad('wrong_normalization_units',lambda r:r['cap']['rounded_units'].update(I_lower=23685317817))
    bad('nonpositive_denominator',lambda r:r['cap']['normalized_forms'].update(denominator=as_interval(0)))
    bad('inverted_interval',lambda r:r['components'][0]['raw_forms'].update(root_square=as_interval(1,0)))
    bad('float_input',lambda r:r['components'][0]['raw_forms']['root_square'].update(upper=1e-30))
    bad('stale_component_cache',lambda r:r['components'][0].update(component_relative_units=0))
    bad('stale_aggregate_cache',lambda r:r.update(source_total_relative_units=0))
    bad('unsafe_tail_sign',lambda r:r['cap']['normalized_forms'].update(Jtail=as_interval(0,F(1,10**10))))
    # Exact boundary acceptance in the mathematical rational wrapper.
    equal=copy.deepcopy(good)
    for t in fixed_inventory(targets,geo)[:149]:
        row=next(r for r in equal['components'] if key(r['task'])==(t['group'],t['kind'],t['task_index']))
        row['raw_forms'][t['field']]=as_interval(F(t['absolute_bound']))
    equal['components']=round_rows(equal['cap'],equal['components'],targets)
    equal.update(assemble_model(equal['cap'],equal['components'],geo['tasks']))
    require(validate(equal,targets,geo)['conditional_arithmetic_pass'],'boundary equality rejected')
    # One source exceeds its fixed target, despite 148 others retaining slack.
    over=copy.deepcopy(equal); over['components'][0]['raw_forms']['root_square']['upper']=str(F(fixed_inventory(targets,geo)[0]['absolute_bound'])+F(1,10**60))
    over['components']=round_rows(over['cap'],over['components'],targets)
    over.update(assemble_model(over['cap'],over['components'],geo['tasks']))
    excess=validate(over,targets,geo)
    require(excess['failed_targets']==['G0:R00:root_square'],'single-row excess mislocalized')
    return dict(ok=True,scope='finite_arithmetic_and_transcribed_geometry_only',
      geometry_checks=geo['checks'],geometry_sha256=digest(geo),target_count=152,
      positive_fixture=dict(arithmetic_pass=True,fixture_kind='synthetic'),
      scaling_countermodel=dict(factor='2',both_upstream_model_pass=True,margin=good['final_margin_lower'],
         failed_fixed_targets=double['failed_target_count'],failed_source_targets=149,failed_cap_targets=['CAP:I_upper'],
         same_relative_units=True,naive_relative_comparisons_passed=149,
         interpretation='countermodel to aggregate-predicate sufficiency; not to real integral bounds'),
      rejected_mutations=tests,boundary_equality_accepted=True,single_row_excess_localized=True,
      actual_integral_evaluation=False,independent_verification=False,
      remaining_obligation='Authentic valid enclosures for the same 152 mathematical objects')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true');p.add_argument('--receipt',type=Path)
    p.add_argument('--write-results',type=Path);p.add_argument('--write-coverage',type=Path)
    a=p.parse_args()
    try:
        require(hashlib.sha256((HERE/'targets.json').read_bytes()).hexdigest()==TARGETS_SHA256,'fixed target file hash changed')
        targets=read_json(HERE/'targets.json');geo=build_geometry(targets)
        if a.write_coverage:
            obj=compact_coverage(targets,geo)
            a.write_coverage.write_text(json.dumps(obj,separators=(',',':'))+'\n')
        if (HERE/'coverage.json').exists():
            require(read_json(HERE/'coverage.json')==compact_coverage(targets,geo),'coverage ledger changed')
        if a.receipt:result=validate(read_json(a.receipt),targets,geo)
        elif a.self_test:result=self_test(targets,geo)
        else:p.error('choose --self-test or --receipt')
        text=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
        if a.write_results:a.write_results.write_text(text)
        print(text,end='')
        return 0 if result.get('ok',result.get('conditional_arithmetic_pass',False)) else 1
    except (ValueError,KeyError,TypeError,OSError,ZeroDivisionError) as exc:
        print(json.dumps({'ok':False,'error':str(exc),'axioms_discharged':False}));return 1

if __name__=='__main__':sys.exit(main())
