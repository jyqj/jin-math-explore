#!/usr/bin/env python3
"""CP-ERR-0003: lower-sieve endpoint certificates and explicit contract checks.

--compute actually recomputes three interval midpoint integrals. Before freeze it
writes results.json; once a manifest exists it compares, without overwriting it.
--check checks saved arithmetic, contract declarations, controls and file hashes.
--require-global intentionally rejects unverified full-paper closure.
Numerics use mpmath.iv 1.3.0; all decisions/serialization use exact Fraction.
The analytic derivative bound and source-to-count transfer remain manual inputs.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import itertools
import json
import platform
import sys
from fractions import Fraction as F
from pathlib import Path
import mpmath
from mpmath import iv

ROOT = Path(__file__).resolve().parent
CP = 'CP-ERR-0003'
A, B = F(4, 53), F(4, 33)
RHO = F(1, 10**8)
SIGMA = {'G1_fixed': F(6), 'G2_fixed': F(33,8)-RHO, 'G2_log_limit': F(33,8)}
EXP = {'G1_fixed': A, 'G2_fixed': B, 'G2_log_limit': B}
FLOOR = {'G1_fixed': F('14.877114'), 'G2_fixed': F('9.1158704'), 'G2_log_limit': F('9.1158704')}
UPPER = {'G1_fixed': F(15), 'G2_fixed': F(10), 'G2_log_limit': F(10)}
N = 4096
D2 = F(3)
DPS = 50
FILES = {'README.md','proof.md','source-lock.json','contracts.json','error-handoff.json',
         'check_g12.py','results.json','computation-handoff.json','attempt.json'}

class CheckError(ValueError):
    pass

def need(ok, message):
    if not ok:
        raise CheckError(message)

def load(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))

def iq(q):
    q=F(q)
    return iv.mpf(q.numerator)/q.denominator

def endpoint(t):
    sign,m,e,bc=t
    need(bc>=0,'nonfinite interval endpoint')
    return (-1 if sign else 1)*F(m)*F(2)**e

def decimal(q, upper=False, digits=18):
    q=F(q); scale=10**digits; num=q.numerator*scale
    k=-((-num)//q.denominator) if upper else num//q.denominator
    sign='-' if k<0 else ''; k=abs(k)
    return f'{sign}{k//scale}.{k%scale:0{digits}d}'

def constants():
    k1=A*SIGMA['G1_fixed']; k2=B*SIGMA['G2_fixed']
    gap1=F(1,2)-k1; gap2=F(1,2)-k2
    need(k1==F(24,53) and gap1==F(5,106),'G1 level')
    need(gap2==F(1,825000000) and k1<k2<F(1,2),'G2 fixed level')
    need(F(1,2)-4*B==F(1,66),'G2 logarithmic mode margin')
    need(2+2*F(1,3)+F(1,9)==F(25,9)<D2,'quadrature envelope')
    need(F(8,7)*F(4,3)==F(32,21),'cutoff factor')
    need(3*15+10==55,'weighted coefficient cap')
    return {
        'alpha':str(A),'beta':str(B),'rho':str(RHO),
        'kappa1':str(k1),'kappa2':str(k2),
        'BV_gap1':str(gap1),'BV_gap2':str(gap2),
        'common_fixed_mode_h_ceiling':str(gap2),
        'log_mode_h_ceiling':'1/66','normalized_f_sup':'1',
        'normalized_f_Lipschitz':'1/4','cutoff_ratio_bound':'32/21',
        'midpoint_derivative_envelope':'25/9','midpoint_D2':'3',
        'pair_cost_coefficients':{'epsilon0':'1760/21','q_alpha':'45','q_beta':'10',
             'e_star':'384','L_CBV_T_2_minus_A0':'8','h_fixed_mode':'0','h_log_mode':'1089/16'},
        'minimum_logQ_over_logN':'24/53'
    }

def compute():
    need(mpmath.__version__=='1.3.0','re-lock interval backend version')
    iv.dps=DPS
    vals={}
    for key,s in SIGMA.items():
        lo,hi=F(2),s-2; step=(hi-lo)/N
        subtotal=iv.mpf(0)
        for k in range(N):
            u=iq(lo+F(2*k+1,2)*step)
            subtotal+=iv.ln(u-1)/u*iv.ln(iq(s-1)/(u+1))
        raw=iq(step)*subtotal
        err=D2*(hi-lo)**3/(24*N*N)
        factor=F(4)/(EXP[key]*s)
        raw_lo,raw_hi=map(endpoint,raw._mpi_)
        base=iv.ln(iq(s-1))
        base_lo,base_hi=map(endpoint,base._mpi_)
        lower=factor*(base_lo+raw_lo-err)
        upper=factor*(base_hi+raw_hi+err)
        need(FLOOR[key]<lower<=upper<UPPER[key],key+': target certificate failed')
        vals[key]={'s':str(s),'sifting_exponent':str(EXP[key]),'factor':str(factor),
          'integration_domain':[str(lo),str(hi)],
          'midpoint_binary':[list(t) for t in raw._mpi_],
          'base_log_binary':[list(t) for t in base._mpi_],
          'integral_error_exact':str(err),
          'coefficient_outward_decimal':[decimal(lower),decimal(upper,True)],
          'certified_floor':str(FLOOR[key]),'coefficient_cap':str(UPPER[key])}
    return {'schema':'jin-math-g12-endpoint-certificate/v1','attempt_id':'A-GB-ERR-0001',
       'checkpoint':CP,'backend':{'python':platform.python_version(),'mpmath':mpmath.__version__,'iv_dps':DPS},
       'method':'interval midpoint plus exact analytic second-derivative remainder',
       'subintervals_per_value':N,'midpoint_evaluations':N*len(SIGMA),
       'constants':constants(),'values':vals,
       'G1_comparison_not_identity':'G1_fixed uses f(6), NOT the paper coefficient involving f(53/8).',
       'source_bounds_preserved':True,'global_ledger_modified':False,
       'independent_verification':False,'global_closure':False,
       'trust_basis':['mpmath.iv outward arithmetic/log','exact Fraction arithmetic',
                     'manual single-integral identity and derivative bound in proof.md'],
       'cannot_imply':['No analytic sieve, BV or normalization input is proved by this code.',
                      'No unbounded prime enumeration or full twelve-term closure.',
                      'The G2 fixed-level route trades a larger source onset for zero kernel drift.']}

def validate_contract(c):
    need(c['checkpoint']==CP and c['global_closure'] is False,'unauthorized closure')
    need(c['sequence_action']=='retain_original_truncated_sequence','invalid lower-bound enlargement')
    need(c['uniform_sieve_constant']['uniform_in_eta'] is True,'missing source uniformity hypothesis')
    need(c['endpoint_policy']=='strict_count_via_maximal_endpoint_BV','endpoint ambiguity')
    need(c['primary_mode']=='fixed_fixed','wrong active mode')
    need(c['constants']==constants(),'contract coefficient mismatch')
    need(c['G1_numeric_object']=='53*psi(6)','false G1 coefficient identity')
    need(c['global_inputs_imported'] is False,'unverified global import')
    for name in ('G1','G2'):
        need(c['rows'][name]['direction']=='lower','wrong one-sided direction')
        need(c['rows'][name]['cutoff_cost_retained'] is True,'cutoff loss erased')

def reject(fn):
    try:
        fn()
    except CheckError as exc:
        return str(exc)
    raise CheckError('negative control unexpectedly accepted')

def check_signs():
    count=0
    for q,theta,psi0,psih,e,sign in itertools.product(
        (F(0),F(1,2),F(1)),(F(0),F(1,2),F(1)),
        (F(0),F(1,3),F(1)),(F(0),F(1,2),F(1)),(F(0),F(1),F(2)),(-1,1)):
        actual=(1+sign*q)*(1-theta)*(psih-e)
        lower=psi0-(q+theta)*psi0-abs(psih-psi0)-(1+q)*e
        need(actual>=lower,'separated main/error inequality failed')
        count+=1
    return count

def check_saved():
    r,c=load('results.json'),load('contracts.json')
    validate_contract(c)
    need(r['checkpoint']==CP and r['constants']==constants(),'result identity')
    need(r['subintervals_per_value']==N and r['midpoint_evaluations']==3*N,'mesh metadata')
    need(r['global_closure'] is False and r['independent_verification'] is False,'result status')
    for key,s in SIGMA.items():
        row=r['values'][key]
        need(F(row['s'])==s and F(row['sifting_exponent'])==EXP[key],'endpoint substitution')
        err=D2*(s-4)**3/(24*N*N)
        need(F(row['integral_error_exact'])==err,'quadrature remainder')
        ml,mh=map(endpoint,row['midpoint_binary']); bl,bh=map(endpoint,row['base_log_binary'])
        need(ml<=mh and bl<=bh,'reversed saved interval')
        fac=4/(EXP[key]*s)
        need(F(row['factor'])==fac,'normalization factor')
        low,high=fac*(bl+ml-err),fac*(bh+mh+err)
        dl,dh=map(F,row['coefficient_outward_decimal'])
        need(dl<=low<=high<=dh,'inward decimal serialization')
        need(F(row['certified_floor'])==FLOOR[key]<low,'unjustified lower floor')
        need(high<UPPER[key]==F(row['coefficient_cap']),'unjustified error coefficient cap')
    negative={}
    mutations=[('enlarged_lower_sequence',lambda x:x.update(sequence_action='enlarge')),
      ('cutoff_erased',lambda x:x['rows']['G1'].update(cutoff_cost_retained=False)),
      ('wrong_direction',lambda x:x['rows']['G2'].update(direction='upper')),
      ('source_uniformity_removed',lambda x:x['uniform_sieve_constant'].update(uniform_in_eta=False)),
      ('false_G1_identity',lambda x:x.update(G1_numeric_object='53*psi(53/8)')),
      ('global_upgrade',lambda x:x.update(global_closure=True))]
    for name,mutate in mutations:
        bad=copy.deepcopy(c); mutate(bad)
        negative[name]=reject(lambda:validate_contract(bad))
    negative['illegal_fixed_level']=reject(lambda:need(F(1,1000)<=F(1,825000000),'Q2 exceeds BV cutoff at this h'))
    negative['negative_bracket_factoring']=reject(lambda:need(F(-9,5)>=F(0),'cannot lower a multiplier on a negative bracket'))
    hashes=0
    if (ROOT/'attempt.json').exists():
        m=load('attempt.json'); expected=m['artifact_sha256']
        need(set(expected)==FILES-{'attempt.json'},'manifest scope')
        need({p.name for p in ROOT.iterdir() if p.is_file()}==FILES,'unexpected checkpoint files')
        for name,digest in expected.items():
            need(Path(name).name==name,'unsafe artifact name')
            need(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'artifact hash: '+name)
            hashes+=1
    return {'ok':True,'scope':'saved_arithmetic_contract_declarations_and_hashes',
       'enclosures':{k:v['coefficient_outward_decimal'] for k,v in r['values'].items()},
       'bounded_sign_checks':check_signs(),'negative_controls':negative,'hashes_checked':hashes,
       'global_closure':False,'independent_verification':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compute',action='store_true')
    p.add_argument('--check',action='store_true')
    p.add_argument('--require-global',action='store_true')
    args=p.parse_args()
    if args.require_global:
        raise CheckError('global closure blocked: other one-sided estimates and independent receipts missing')
    if args.compute:
        fresh=compute()
        if (ROOT/'attempt.json').exists():
            old=load('results.json')
            # Runtime version belongs to reproduction metadata, not frozen numerics.
            old_cmp=copy.deepcopy(old); fresh_cmp=copy.deepcopy(fresh)
            old_cmp.pop('backend'); fresh_cmp.pop('backend')
            need(old_cmp==fresh_cmp,'fresh numeric reproduction differs')
        else:
            (ROOT/'results.json').write_text(json.dumps(fresh,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    out=check_saved(); out['full_quadrature_executed_this_command']=bool(args.compute)
    print(json.dumps(out,ensure_ascii=False))
    return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (CheckError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
