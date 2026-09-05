#!/usr/bin/env python3
"""Exact row, seed, and terminal-aggregation checks; not independent review."""
from __future__ import annotations
import argparse, copy, importlib, json, math, os, struct, subprocess, sys, zlib
from fractions import Fraction as F
from pathlib import Path
import run_row as r

EXPECTED={'first_index':3497,'last_index':4704,'cap_index':49152,
          'radial_first':93607,'radial_last':95638,'slope':140,
          'background_max_count':28,'designated_max_unmarked':27}

def validate_row(row):
    r.need(row==r.reconstruct_row(),'row identity differs from fixed recurrence')
    for k,v in EXPECTED.items():r.need(row[k]==v,'incorrect '+k)
    r.need(row['relative_targets']=={'root':2285,'face':577},'target mismatch')
    h=F(row['h']);lo,hi=F(row['low']),F(row['high'])
    r.need(row['first_index']*h<=lo<(row['first_index']+1)*h,'lower outward rounding')
    r.need((row['last_index']-1)*h<hi<=row['last_index']*h,'upper outward rounding')
    r.need(row['radial_first']==F(row['radial_cutoff'])//h-39,'missing dimensional shift')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--include-results',action='store_true');args=ap.parse_args()
    w=args.work;o=w/'output';row=json.loads((o/'source-row.json').read_text());validate_row(row)
    p5=w/'predecessor05/A-TP-186-CONTRACTION-0005';p3=w/'predecessor03/A-TP-186-LOW-0003';p4=w/'predecessor04/A-TP-186-MARGINAL-0004'
    sys.path[:0]=list(map(str,[p5,p3,p4]));low=importlib.import_module('low_kernel')
    inp=json.loads((p4/'inputs.json').read_text());budget=r.error_budget(inp,row)
    r.need(budget==json.loads((o/'rounding-budget.json').read_text()),'stale error budget')
    old_budget=json.loads((p4/'rounding-budget.json').read_text())
    r.need(F(budget['energy_error_upper'])==6*F(old_budget['energy_error_upper']),'row-specific error scaling')
    r.need(F(budget['energy_error_upper'])<F(1,10**77),'error bound not sufficient')
    old=r.reconstruct_row(0);old_reference=json.loads((p4/'source-row.json').read_text())
    for key in ['low','high','threshold','radial_first','radial_last','first_index','last_index','cap_index','slope']:
        r.need(F(old[key])==F(old_reference[key]),'row0 recurrence does not reproduce predecessor')
    mutations=[]
    for key in ['first_index','last_index','cap_index','radial_first','radial_last','slope']:
        bad=copy.deepcopy(row);bad[key]+=1
        try:validate_row(bad)
        except ValueError:mutations.append(key)
        else:raise ArithmeticError('corrupted geometry accepted')
    bad=copy.deepcopy(row);bad['relative_targets']['face']=578
    try:validate_row(bad)
    except ValueError:mutations.append('target')
    else:raise ArithmeticError('changed target accepted')
    seed=low.seed_cells(3497,98304,140*F(row['h']),640)
    raw=zlib.decompress((o/'seed-enclosures.bin.zlib').read_bytes())
    magic,bits,n,width=struct.unpack('>8sIII',raw[:20]);r.need((magic,bits,n)==(b'TPSEED06',640,98304),'seed format mismatch')
    vals=memoryview(raw)[20:];r.need(len(vals)==2*n*width,'seed size mismatch')
    for j in range(n):
        for k,arr in enumerate((seed['seed_lower'],seed['seed_upper'])):
            r.need(arr[j]==int.from_bytes(vals[(2*j+k)*width:(2*j+k+1)*width],'big'),'seed endpoint replay failed')
    # Production-length packing, with direct integer coefficients across the grid.
    gp=importlib.import_module('gmp_poly');a=[(1<<319)//(j+7) for j in range(r.N)];b=[(1<<311)//(j+19) for j in range(r.N)]
    prod=gp.convolution(a,b,r.N);probes=[0,1,3497,4704,49151,93607,95638,98263]
    for q in probes:r.need(prod[q]==sum(a[j]*b[q-j] for j in range(q+1)),'production-length direct coefficient mismatch')
    del a,b,prod
    # Independent signed-sum / polynomial tests of unchanged inherited engine.
    env=dict(os.environ,PYTHONPATH=os.pathsep.join(map(str,[p5,p3,p4])),TP_PREVIOUS3=str(p3))
    tests={}
    for name in ['test_contraction.py','test_signed_contraction.py']:
        cp=subprocess.run([sys.executable,'-B',str(p5/name)],capture_output=True,text=True,env=env,check=True)
        tests[name]=json.loads(cp.stdout)
    ans={'scope':'finite_exact_checks_not_isolated_verification','source_row_valid':True,'large_convolution_direct_probes':probes,
         'row0_regression_fields':9,'corruptions_rejected':mutations,'fresh_seed_endpoints_replayed':2*n,
         'error_budget_is_six_times_previous':True,'tests':tests,'independent_verification':False}
    if args.include_results:
        result=json.loads((o/'results.json').read_text());agg=result['aggregation'];terms=[]
        for i in range(53):terms.append(json.loads((w/'scratch/terms'/f'{i:02}.json').read_text()))
        signatures=[tuple(t['signature']) for t in terms]
        wanted=sorted({tuple(sorted(a+b)) for a in map(tuple,inp['signatures']) for b in map(tuple,inp['signatures'])},key=lambda s:(sum(s),s))
        r.need(signatures==wanted,'square signature coverage/order mismatch')
        rh=F(40*sum(int(t['root_upper_numerator']) for t in terms),int(agg['root_denominator']))
        prefix=[F(agg['face_factor'])*sum(int(t['face_prefix_upper_numerators'][p]) for t in terms) for p in range(3)]
        tau=F(agg['tau']);E=F(budget['energy_error_upper']);fh=(1+tau)*sum(prefix[1:])+(1+1/tau)*E
        r.need(rh==F(result['root']['upper']) and fh==F(result['face']['upper_including_error']),'terminal exact reassembly mismatch')
        unit=F(row['I0'])/10**18
        r.need(result['root']['pass']==(rh<=2285*unit),'root verdict inconsistent')
        r.need(result['face']['pass']==(fh<=577*unit),'face verdict inconsistent')
        r.need(F(result['face']['all_prefix_upper'])==(1+tau)*sum(prefix)+(1+1/tau)*E,'conservative prefix assembly mismatch')
        ans.update(term_count=53,terminal_reassembly=True,root_pass=result['root']['pass'],face_pass=result['face']['pass'])
    print(json.dumps(ans,indent=2,sort_keys=True))

if __name__=='__main__':main()
