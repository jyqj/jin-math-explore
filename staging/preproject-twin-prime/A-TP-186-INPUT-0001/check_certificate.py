#!/usr/bin/env python3
"""Exact arithmetic only; does NOT validate physical integrals or a Lean build.

Python >=3.10, standard library only. From any working directory:
  python3 -B check_certificate.py --write    # regenerate results.json
  python3 -B check_certificate.py --check    # compare frozen deterministic result
  python3 -B check_certificate.py --self-test

Every comparison uses integers/Fraction. Decimal strings are display-only.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
from decimal import Decimal, localcontext
from fractions import Fraction as F
from math import isqrt
from pathlib import Path

GROUPS = {'outer_2':17, 'outer_5_2':35, 'inner_base_2':7,
          'inner_base_5_2':10, 'inner_enlarged_2':11, 'inner_enlarged_5_2':17}

class CertificateError(ValueError):
    pass

def require(test: bool, message: str) -> None:
    if not test:
        raise CertificateError(message)

def ceil_scaled(x: F, denominator: int) -> int:
    return -((-x.numerator * denominator) // x.denominator)

def show(x: F) -> dict[str, str]:
    with localcontext() as context:
        context.prec = 32
        dec = str(Decimal(x.numerator) / Decimal(x.denominator))
    return {'fraction':str(x), 'decimal_display_only':dec}

def evaluate(d: dict) -> dict:
    require(d['upstream_commit']=='61340d0b74163003b32756bb16e91d9209a5e330', 'source lock')
    rho, ah, bh = F(*d['rho']), F(*d['a_h']), F(*d['b_h'])
    d0, new_weight = 1-ah-bh, 1-bh
    require(0<rho<1 and d0>0 and new_weight>0 and bh<0, 'coefficient signs')
    norm = d['normalization']
    cd, bd, sd = norm['component_denominator'], norm['budget_denominator'], norm['outer_scale_denominator']
    require((cd,bd,sd)==(10**18,10**12,10**6),'table unit convention')
    groups, rows = {}, []
    total, fine_total, changed = 0, 0, 0
    optimal_lower = F(0)
    for name, count in GROUPS.items():
        require(len(d[name])==count, f'{name}: row count')
        budget_sum, fine_sum = 0, 0
        for j, row in enumerate(d[name]):
            require(all(type(v) is int and v>0 for v in row), f'{name}[{j}]: positive integers')
            if name.startswith('outer'):
                require(len(row)==4,'outer width')
                scale, a, b, budget = row
                c = F(scale,sd)
                value = (c*a+b/c)/cd
                # Bracket sqrt(b/a) with two positive rational grid points,
                # then choose by exact objective comparison, not floating point.
                grid = 10**12
                root = isqrt((b*grid*grid)//a)
                candidates = [c, F(root+1,grid)]
                if root>0:
                    candidates.append(F(root,grid))
                chosen = min(candidates, key=lambda z: z*a+b/z)
                optimized = (chosen*a+b/chosen)/cd
                # AM-GM identifies the continuous minimum 2*sqrt(a*b)/cd.
                # Integer sqrt gives a rigorous rational LOWER bound on it.
                opt_floor = isqrt(a*b*grid*grid)
                require(opt_floor**2<=a*b*grid*grid<(opt_floor+1)**2,'sqrt enclosure')
                optimal_lower += F(2*opt_floor,grid*cd)
                require(optimized<=value,'optimization regressed')
                chosen_numerator = ceil_scaled(optimized,cd)
                require(optimized<=F(chosen_numerator,cd),'outward rounding')
                require(F(chosen_numerator,cd)<=F(budget,bd),'fine bound regressed')
                changed += chosen!=c
                rows.append({'group':name,'index_zero_based':j,
                             'original_young':str(c),'new_young':str(chosen),
                             'new_budget_units_1e18':chosen_numerator})
            else:
                require(len(row)==2,'inner width')
                a,budget = row
                weight = d0 if 'base' in name else new_weight
                value = weight*a/cd
                optimal_lower += value
                chosen_numerator = ceil_scaled(value,cd)
                require(value<=F(chosen_numerator,cd)<=F(budget,bd),'inner rounding')
                rows.append({'group':name,'index_zero_based':j,
                             'new_budget_units_1e18':chosen_numerator})
            require(value<=F(budget,bd), f'{name}[{j}]: original budget violated')
            budget_sum += budget
            fine_sum += chosen_numerator
        groups[name] = {'rows':count,'original_budget_units_1e12':budget_sum,
                        'new_budget_units_1e18':fine_sum}
        total += budget_sum
        fine_total += fine_sum
    require(total==d['paper_loss_budget'],'published loss sum mismatch')
    old_loss, new_loss = F(total,bd), F(fine_total,cd)
    require(new_loss<old_loss,'no strict arithmetic improvement')
    require(0<=new_loss-optimal_lower<F(1,10**16),'Young-family optimality gap')
    caps = d['cap_bounds']
    ilo, ihi, jl = (F(caps[key],norm['cap_denominator']) for key in ('I_lower','I_upper','J_lower'))
    require(0<ilo<=ihi,'cap order')
    raw_ratio = rho*jl/ihi
    ratio_floor = F(*d['paper_ratio_lower'])
    paper_margin = F(*d['paper_margin'])
    require(raw_ratio>ratio_floor,'main ratio inequality failed')
    coarse_margin = ratio_floor-1-rho*old_loss
    old_margin = raw_ratio-1-rho*old_loss*ilo/ihi
    new_margin = raw_ratio-1-rho*new_loss*ilo/ihi
    require(coarse_margin>paper_margin,'paper coarse margin failed')
    require(new_margin>old_margin>paper_margin,'restored margin failed')
    H = d['admissible_tuple']
    require(all(type(x) is int and x>=0 for x in H),'tuple integers')
    require(H==sorted(set(H)) and len(H)==40,'tuple distinct cardinality')
    require(H[0]==0 and H[-1]==186,'tuple diameter')
    primes = [p for p in range(2,41) if all(p%q for q in range(2,isqrt(p)+1))]
    missing = {}
    for p in primes:
        omitted = sorted(set(range(p))-{h%p for h in H})
        require(bool(omitted),f'tuple not admissible mod {p}')
        missing[str(p)] = omitted
    penalty = rho*new_loss*ilo/ihi
    return {
      'ok':True, 'scope':'exact_table_arithmetic_and_finite_admissibility_only',
      'physical_integrals_verified':False, 'full_prime_gap_theorem_verified':False,
      'component_counts':{'outer_pairs':52,'outer_integral_bounds':104,'inner_integral_bounds':45,'cap_bounds':3,'total_scalar_input_inequalities':152},
      'coefficients':{'rho':str(rho),'d0':str(d0),'one_minus_bh':str(new_weight)},
      'groups':groups, 'original_loss':show(old_loss), 'new_loss':show(new_loss),
      'loss_improvement':show(old_loss-new_loss),'new_young_choices':changed,
      'fixed_table_young_family':{'infimum_lower_bound':show(optimal_lower),
        'remaining_improvement_upper_bound':show(new_loss-optimal_lower),
        'scope':'positive Young parameters only; fixed root/face/inner/cap bounds and coefficients'},
      'raw_ratio':show(raw_ratio),'coarse_margin':show(coarse_margin),
      'original_cap_margin':show(old_margin),'new_cap_margin':show(new_margin),
      'margin_improvement':show(new_margin-old_margin),
      'sensitivity':{'relative_J_lower_loss_coefficient':show(raw_ratio),
        'relative_I_upper_increase_coefficient':'1',
        'relative_aggregate_loss_increase_coefficient':show(penalty),
        'positive_margin_budget':show(new_margin),
        'extra_loss_fraction_to_zero':show(new_margin/penalty),
        'extra_loss_fraction_preserving_1_over_50000':show((new_margin-paper_margin)/penalty),
        'boundary_is_strict_for_positivity':True},
      'tuple_certificate':{'cardinality':40,'diameter':186,'omitted_residues':missing,
                           'primes_above_40':'at most 40 represented residues cannot cover p>40'},
      'row_certificates':rows,
      'cannot_imply':d['cannot_imply']
    }

def self_test(d: dict) -> dict:
    # Explicit adversarial cases ensure failures are detected even with python -O.
    bad=[]
    x=copy.deepcopy(d); x['outer_2'][3][3]=1; bad.append(('too_small_budget',x))
    x=copy.deepcopy(d); x['cap_bounds']['I_lower']=x['cap_bounds']['I_upper']+1; bad.append(('reversed_caps',x))
    x=copy.deepcopy(d); x['b_h'][0]=abs(x['b_h'][0]); bad.append(('lost_negative_sign',x))
    x=copy.deepcopy(d); x['admissible_tuple'][1]=1; bad.append(('inadmissible_mod_2',x))
    x=copy.deepcopy(d); x['inner_base_2'].pop(); bad.append(('missing_row',x))
    rejected=[]
    for name,x in bad:
        try:
            evaluate(x)
        except CertificateError:
            rejected.append(name)
        else:
            raise CertificateError('self-test failed to reject '+name)
    return {'ok':True,'rejected_mutations':rejected}

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    actions=parser.add_mutually_exclusive_group()
    actions.add_argument('--write',action='store_true')
    actions.add_argument('--check',action='store_true')
    actions.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    try:
        raw=(root/'inputs.json').read_bytes(); d=json.loads(raw)
        if args.self_test:
            result=self_test(d)
        else:
            result=evaluate(d)
            result['inputs_sha256']=hashlib.sha256(raw).hexdigest()
            if args.write:
                (root/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            elif args.check:
                saved=json.loads((root/'results.json').read_text(encoding='utf-8'))
                require(saved==result,'stored result differs from recomputation')
                result={'ok':True,'exact_reproduction':True,'inputs_sha256':result['inputs_sha256'],'scope':result['scope']}
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError,ZeroDivisionError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 1

if __name__=='__main__':
    sys.exit(main())
