#!/usr/bin/env python3
"""Build frozen signed marginal columns. Pure standard-library integer arithmetic.
Usage: python3 -B run_marginals.py --output-dir fresh-output
"""
from __future__ import annotations
import argparse,hashlib,json,sys,time
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
import marginal as m

INPUT_SHA256='10f1b1cd8df483d49e30974c07595a0fbe57d13e560d3e99a5b88238bccadadc'


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output-dir',type=Path,required=True)
    args=ap.parse_args();out=args.output_dir
    m.require(not out.exists(),'output directory already exists')
    raw=Path(__file__).with_name('inputs.json').read_bytes()
    m.require(hashlib.sha256(raw).hexdigest()==INPUT_SHA256,'frozen input hash mismatch')
    x=json.loads(raw);out.mkdir(parents=True)
    n=x['n'];bits=x['work_bits'];Q=1<<bits;h=F(x['h']);outbits=x['output_bits']
    scale=m.polynomial_scale(h,x['coefficient_denominator']);den=Q*scale[-1]
    g=m.fiber_groups(x['signatures'],x['coefficient_integer_matrix']);grouped=defaultdict(list)
    for (sig,e),poly in g.items():grouped[sig].append((e,poly))
    sigs=sorted(grouped); cumulative={s:([0]*n,[0]*n) for s in sigs}
    columns=[];caps=[];anchors=[];direct=[];samples=[];begin=time.monotonic()
    print(json.dumps(dict(event='START',n=n,groups=len(g),signatures=len(sigs)),sort_keys=True),flush=True)
    for shell in x['shells']:
        sid=shell['id'];L=shell['first'];U=shell['last'];M=shell['cap_index']
        tick=time.monotonic();cap=m.cap_cells(M,n,bits,x['taylor_even_order'])
        caps.append(m.write_column(out/f'cap-{sid}.zlib',cap['mass_lower'],cap['mass_upper'],Q,bits,
                    dict(kind='cap_cell_mean',cap_index=M,interpretation='mu_cap(C_j)/h; not midpoint density')))
        for j in sorted({0,M-1,M,min(2*M,n),n}):
            anchors.append(dict(cap_index=M,j=j,node_lower=str(F(cap['node_lower'][j],Q)),node_upper=str(F(cap['node_upper'][j],Q))))
        weights=m.profile_weights(h,cap,6,bits)
        print(json.dumps(dict(event='CAP_READY',shell=sid,seconds=time.monotonic()-tick,max_width_units=cap['max_mass_width_units']),sort_keys=True),flush=True)
        for si,sig in enumerate(sigs):
            lo=[0]*n;hi=[0]*n
            for e,poly in grouped[sig]:m.correlate_scan(weights[e],poly,L,U,scale,lo,hi)
            for r in sorted({U,max(0,U-7),max(0,L-1),0}):
                dl=du=0
                for e,poly in grouped[sig]:
                    a,b=m.correlate_direct(weights[e],poly,L,U,r,scale);dl+=a;du+=b
                m.require(lo[r]<=dl<=du<=hi[r],f'direct contraction not contained: {sid}/{sig}/{r}')
                direct.append(dict(shell=sid,signature=list(sig),r=r,passed=True,terms=max(0,U-r-max(0,L-r)+1)))
            cl,ch=cumulative[sig]
            for r in range(n):cl[r]+=lo[r];ch[r]+=hi[r]
            info=m.write_column(out/f'prefix-{sid+1}-sig-{si:02d}.zlib',cl,ch,den,outbits,
                dict(kind='signed_prefix_coefficient',prefix_shell_count=sid+1,signature=list(sig),
                     excluded_factors=['h','product_retained_profiles','retained_angular_monomial'],input_sha256=INPUT_SHA256))
            hd,rl,ru=m.read_column(out/info['file'])
            m.require(all(a==(v<<outbits)//den and b==m.ceildiv(w<<outbits,den) for a,b,v,w in zip(rl,ru,cl,ch)), 'column serialization roundtrip failed')
            info.update(negative_cells=sum(b<0 for b in ru),positive_cells=sum(a>0 for a in rl),mixed_or_zero_cells=sum(a<=0<=b for a,b in zip(rl,ru)))
            columns.append(info)
            for r in [0,2331,46580,68225,89196,94919,95598,95638,98263]:
                samples.append(dict(prefix=sid+1,signature=list(sig),r=r,lower_units=rl[r],upper_units=ru[r],bits=outbits))
            print(json.dumps(dict(event='COLUMN',shell=sid,signature=list(sig),max_width_units=info['max_width_units'],bytes=info['bytes'],elapsed=time.monotonic()-begin),sort_keys=True),flush=True)
        del weights,cap
    maxwidth=max(c['max_width_units'] for c in columns);S=h*98304
    angular_bound=sum((S**sum(s) for s in sigs),F(0)); uniform=h*F(maxwidth,1<<outbits)*angular_bound
    report=dict(format='tp-marginal-generation/v1',input_sha256=INPUT_SHA256,
        arithmetic='exact integer endpoint arithmetic; no floating point acceptance',
        n=n,shell_count=3,remaining_signature_count=len(sigs),fiber_group_count=len(g),
        cap_cell_interval_count=3*n,prefix_coefficient_interval_count=3*len(sigs)*n,
        direct_exact_checks=len(direct),direct_checks=direct,complete_column_readback_checks=len(columns),
        work_bits=bits,output_bits=outbits,max_stored_coefficient_width_units=maxwidth,
        uniform_physical_marginal_width_bound=str(uniform),
        uniform_bound_scope='All retained 39-coordinate midpoint configurations with summed indices <=98263 and every cap-prefix, conditional on the stated physical marginal formula; no normalization by I0.',
        caps=caps,columns=columns,dickman_anchor_intervals=anchors,samples=samples,
        final_first_row_root_bound_verified=False,final_first_row_face_bound_verified=False,
        full_upstream_numerical_run=False,independent_verification=False)
    (out/'generation.json').write_text(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(event='COMPLETE',elapsed_seconds=time.monotonic()-begin,coefficient_intervals=report['prefix_coefficient_interval_count'],uniform_width=str(uniform),total_bytes=sum(p.stat().st_size for p in out.iterdir())),sort_keys=True),flush=True)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,ArithmeticError,OSError,KeyError) as e:
        print(f'FAIL: {e}',file=sys.stderr);raise SystemExit(1)
