#!/usr/bin/env python3
"""Exact signed-budget checks for A-GB-ERR-0001 / CP-ERR-0001.

Python standard library only. This evaluates finite arithmetic and declared
contracts, not the analytic validity of the twelve Goldbach estimates.
--compute writes results.json. --check recomputes and checks it and the manifest.
--require-global deliberately fails until all semantic inputs are certified.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import sys
from fractions import Fraction as F
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
ID = 'A-GB-ERR-0001'
CP = 'CP-ERR-0001'
C = [3, 1, -4, -1, -1, 1, 1, -2, -1, -1, -1, -1]
V = ['14.87710','9.11587','0.84289','23.60636','19.51976','1.63357',
     '3.79029','0.60962','5.27231','5.40996','0.10191','0.66821']
EXPECTED_FILES = {
    'README.md','proof.md','signed-ledger.json','error-ledger.json',
    'parameter-plan.json','source-lock.json','check_budget.py',
    'results.json','computation-handoff.json','attempt.json',
}


class BudgetError(ValueError):
    """A frozen contract or exact arithmetic check failed."""


def need(ok: bool, message: str) -> None:
    if not ok:
        raise BudgetError(message)


def load(name: str) -> Any:
    return json.loads((ROOT/name).read_text(encoding='utf-8'))


def sha(name: str) -> str:
    return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


def decimal(x: F, digits: int = 18) -> str:
    """A labelled, truncated decimal display; all decisions use Fractions."""
    scale = 10**digits
    k = abs(x.numerator)*scale//x.denominator
    sign = '-' if x < 0 else ''
    return f'{sign}{k//scale}.{k%scale:0{digits}d}'


def pair(x: F) -> dict[str, str]:
    return {'exact':str(x), 'decimal_truncated':decimal(x)}


def topo(nodes: list[str], edges: list[list[str]]) -> list[str]:
    need(len(nodes) == len(set(nodes)), 'duplicate parameter node')
    dep = {n:set() for n in nodes}
    for src, dst in edges:
        need(src in dep and dst in dep, 'unknown dependency endpoint')
        dep[dst].add(src)
    order: list[str] = []
    while dep:
        ready = sorted(n for n,v in dep.items() if not v)
        need(bool(ready), 'parameter dependency cycle')
        for n in ready:
            order.append(n)
            del dep[n]
        for v in dep.values():
            v.difference_update(ready)
    return order


def validate_table(t: dict) -> tuple[list[int], list[F]]:
    need(t['attempt_id'] == ID and t['checkpoint'] == CP, 'identity mismatch')
    need(t['left_multiplier'] == 4, 'lost factor four')
    need(t['target_for_D_over_S'] == '0.0004', 'target drift')
    rows=t['rows']
    need([r['id'] for r in rows] == [f'G{i}' for i in range(1,13)], 'row inventory')
    need([r['weight'] for r in rows] == C, 'signed coefficients differ')
    need([r['displayed_bound'] for r in rows] == V, 'frozen decimals differ')
    for c,r in zip(C,rows):
        need(r['needed_direction'] == ('lower' if c>0 else 'upper'), 'wrong one-sided direction')
        need(bool(r['source_equations']), 'missing source equation')
        need(r['analytic_status'] == 'uninstantiated', 'unauthorized analytic promotion')
    need(t['sibling_numeric_improvement_imported'] is False, 'unverified numeric import')
    return C, list(map(F,V))


def validate_plan(p: dict) -> list[str]:
    need(p['attempt_id'] == ID, 'plan identity mismatch')
    order=topo(p['nodes'],p['edges'])
    pos={n:i for i,n in enumerate(order)}
    for n in p['fixed_before_N']:
        need(pos[n] < pos['N0'], 'parameter not fixed before N0')
    for rule in p['small_parameter_rules']:
        need(pos[rule['bound_coefficient']] < pos[rule['parameter']], 'coefficient selected too late')
    model=p['numeric_test_plan']
    need(model['d'] == model['dimension_model']*(model['J']+1), 'model cell exponent')
    need(model['A'] > model['d']+2, 'log normalization consumes two powers')
    need(model['normalized_log_exponent'] == model['d']+2-model['A'], 'wrong normalized exponent')
    need(model['semantic_cell_count_established'] is False, 'model promoted to coverage proof')
    return order


def require_global(t: dict, e: dict, p: dict) -> None:
    unresolved = [r['id'] for r in t['rows'] if r['analytic_status'] != 'certified']
    unresolved += [r['id'] for r in e['errors']
                   if r['kind']=='semantic_gate' and r['status']!='certified']
    need(not unresolved, 'global closure blocked: '+', '.join(unresolved))
    need(e['coverage_complete'] is True, 'error inventory is not complete')
    need(p['actual_uniform_coefficients'] is not None or
         p['vanishing_fixed_loss_modulus'] is not None, 'no fixed-loss modulus')


def rejected(action: Callable[[], Any]) -> str:
    try:
        action()
    except BudgetError as exc:
        return str(exc)
    raise BudgetError('negative control unexpectedly accepted')


def calculate() -> dict:
    table, errors, plan, sources = [load(n) for n in
        ('signed-ledger.json','error-ledger.json','parameter-plan.json','source-lock.json')]
    c,v=validate_table(table)
    order=validate_plan(plan)
    need(sources['sources'][0]['identifier']=='arXiv:2606.05224v2', 'source version drift')
    need(len({r['id'] for r in errors['errors']})==len(errors['errors']), 'duplicate error ID')
    need(errors['mode']=='mechanism_inventory_not_a_summable_list', 'deduplication boundary missing')
    gates=[r for r in errors['errors'] if r['kind']=='semantic_gate']
    need(all(r['numeric_cost'] is None for r in gates), 'opaque gate given a numeric cost')
    need(errors['coverage_complete'] is False, 'false complete coverage')
    M=sum((ci*vi for ci,vi in zip(c,v)),F(0))
    amp=sum((abs(ci)*vi for ci,vi in zip(c,v)),F(0))
    P=sum((ci*vi for ci,vi in zip(c,v) if ci>0),F(0))
    Q=sum((-ci*vi for ci,vi in zip(c,v) if ci<0),F(0))
    target=F(table['target_for_D_over_S'])
    reserve=M-4*target
    need(M==F(43,25000) and reserve==F(3,25000), 'budget mismatch')
    need(amp==F(5917017,50000) and P-Q==M and P+Q==amp, 'sensitivity mismatch')
    # A second elementary fixed-point accumulation, independent of Fraction sum.
    units=[int(s.replace('.','')) for s in V]
    need(sum(ci*vi for ci,vi in zip(C,units))==172, 'integer decimal accumulation')
    r=F(1,100000)
    corner_min=min(sum((ci*vi*(1+si*r) for ci,vi,si in zip(c,v,signs)),F(0))
                   for signs in itertools.product((-1,1),repeat=12))
    need(corner_min==M-amp*r, 'worst-sign corner mismatch')
    need(corner_min < 4*target < M*(1-r), 'negative sign-collapse witness failed')
    fixed,decay=F(plan['allocation']['fixed_loss_budget']),F(plan['allocation']['N_decaying_budget'])
    need(fixed==reserve/4 and decay==reserve/4, 'sample allocation not quarter reserve')
    result=(M-fixed-decay)/4
    need(result==F(83,200000)>target,'conditional allocation below target')
    alpha,tau0=F(4,53),F(9,19)
    tau_start=tau0-F(1,100)
    tau_weighted=F(32)/(tau_start*(1-tau_start))
    need(tau_weighted==F(115520000,897739),'tau drift coefficient')
    need(tau_weighted*F(1,10**10)<F(1287,10**11), 'tau displayed bound')
    # Finite telescoping checks corroborate, not replace, the general proof.
    product=F(1)
    for n in range(2,101):
        product*=1-F(1,n*n)
        need(product==F(n+1,2*n) and product>F(1,2), 'telescoping identity')
    reciprocal=F(1,4)-F(1,5)
    need(reciprocal==F(1,20)>0, 'reciprocal sign witness')
    tail=sum((F(1,n*(n-1)) for n in range(5,101)),F(0))
    need(tail==F(1,4)-F(1,100)<F(1,4),'reciprocal tail check')
    bridge_gap=(1+F(9,10))*F(1,1000)
    need(bridge_gap==F(19,10000),'two-parameter product exponent')
    negatives={}
    bad=copy.deepcopy(table);bad['rows'][3]['needed_direction']='lower'
    negatives['wrong_bound_direction']=rejected(lambda:validate_table(bad))
    bad=copy.deepcopy(table);bad['rows'][6]['displayed_bound']='3.79030'
    negatives['unreviewed_decimal_change']=rejected(lambda:validate_table(bad))
    badp=copy.deepcopy(plan);badp['edges'].append(['epsilon','uniform_coefficients'])
    negatives['epsilon_coefficient_cycle']=rejected(lambda:validate_plan(badp))
    badp=copy.deepcopy(plan);badp['numeric_test_plan']['A']=26
    negatives['missing_two_log_powers']=rejected(lambda:validate_plan(badp))
    negatives['uninstantiated_global_closure']=rejected(lambda:require_global(table,errors,plan))
    negatives['underestimated_amplifier']=rejected(lambda:need(M>=amp,'signed mass cannot bound all errors'))
    negatives['strict_target_at_equality']=rejected(lambda:need((M-reserve)/4>target,'equality is not strict'))
    eps=F(1,10**10)
    negatives['nonuniform_small_epsilon']=rejected(lambda:need((1/eps)*eps<reserve,'C(epsilon)*epsilon need not vanish'))
    return {
      'schema':'jin-math-signed-budget-result/v1','attempt_id':ID,'checkpoint':CP,
      'backend':{'python':sys.version.split()[0],'arithmetic':'stdlib fractions.Fraction and exact integers'},
      'source_decimals_are_assumptions':True,'arithmetic_check':'PASS',
      'actual_paper_error_closure':'INCONCLUSIVE','independent_verification':False,
      'positive_mass':pair(P),'negative_mass':pair(Q),'signed_main':pair(M),
      'target_for_D_over_S':pair(target),'reserve_before_division_by_four':pair(reserve),
      'absolute_relative_error_amplifier':pair(amp),'sum_absolute_integer_weights':sum(map(abs,c)),
      'uniform_relative_ceiling_with_no_other_errors':pair(reserve/amp),
      'relative_error_sensitivity_rank':[{'term':f'G{i}', 'weighted_mass':str(mass)}
         for i,mass in sorted(enumerate([abs(ci)*vi for ci,vi in zip(c,v)],1),key=lambda x:-x[1])],
      'top_three_relative_sensitivity_share':str(sum(sorted([abs(ci)*vi for ci,vi in zip(c,v)],reverse=True)[:3])/amp),
      'quarter_budget_uniform_relative_cap':pair(fixed/amp),
      'conditional_half_reserve_D_over_S':pair(result),
      'worst_sign_test':{'r':str(r),'corners_checked':4096,'minimum':pair(corner_min),
                       'invalid_common_error_prediction':pair(M*(1-r)),
                       'counterexample_scope':'finite independent-error model, not a counterexample to the paper'},
      'tau_weighted_drift_coefficient':str(tau_weighted),
      'tau_cost_at_1e_minus10_upper':str(tau_weighted*eps),
      'reciprocal_sign_witness':str(reciprocal),
      'singular_factor_lower_bound':'1/2','finite_telescoping_checks':99,
      'parameter_topological_order':order,'model_normalized_log_exponent':25+2-28,
      'negative_controls':negatives,'negative_control_count':len(negatives),
      'error_mechanisms':len(errors['errors'])-len(gates),'semantic_gates':len(gates),
      'input_sha256':{n:sha(n) for n in ('signed-ledger.json','error-ledger.json','parameter-plan.json','source-lock.json','check_budget.py')},
      'cannot_imply':['No analytic G_i estimate or source theorem is verified by this script.',
                      'A conditional common-N0 proof is not its application to the paper.',
                      'Acyclic declared dependencies do not detect hidden mathematical dependencies.',
                      'The toy sign/cycle witnesses do not refute the paper or binary Goldbach.'],
    }


def check_manifest() -> int:
    meta=load('attempt.json')
    need(meta['attempt_id']==ID and meta['checkpoint']==CP,'manifest identity mismatch')
    need(meta['overall_verdict']=='INCONCLUSIVE','global status overclaim')
    need(meta['authority']['independent_verification'] is False,'false verifier status')
    expected=meta['artifact_sha256']
    need(set(expected)==EXPECTED_FILES-{'attempt.json'},'exact artifact scope mismatch')
    need({p.name for p in ROOT.iterdir() if p.is_file()}==EXPECTED_FILES,'directory file set mismatch')
    for name,value in expected.items():
        need(Path(name).name==name and name!='attempt.json','unsafe/self hash')
        need(sha(name)==value,'artifact hash mismatch: '+name)
    return len(expected)


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--compute',action='store_true')
    ap.add_argument('--check',action='store_true')
    ap.add_argument('--require-global',action='store_true')
    args=ap.parse_args()
    if args.require_global:
        require_global(load('signed-ledger.json'),load('error-ledger.json'),load('parameter-plan.json'))
    result=calculate()
    if args.compute:
        (ROOT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    else:
        need(load('results.json')==result,'saved result does not reproduce')
    hashes=check_manifest() if (ROOT/'attempt.json').exists() else 0
    print(json.dumps({'ok':True,'arithmetic':'PASS','actual_paper_error_closure':'INCONCLUSIVE',
          'signed_main':result['signed_main'],'reserve':result['reserve_before_division_by_four'],
          'error_amplifier':result['absolute_relative_error_amplifier'],
          'negative_controls_rejected':result['negative_control_count'],'hashes_checked':hashes,
          'mathematical_truth_verified':False},ensure_ascii=False))
    return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (BudgetError,KeyError,OSError,TypeError,json.JSONDecodeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
