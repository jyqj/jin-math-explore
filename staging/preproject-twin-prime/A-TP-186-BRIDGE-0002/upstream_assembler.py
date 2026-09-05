"""Independent model of the read upstream rounding/aggregation predicates.

NOT the full upstream program or a source-byte copy. Pure rational arithmetic.
Source functions: round_source_component, assemble_fresh_certificate, at
PrimeGaps186@61340d0b74163003b32756bb16e91d9209a5e330 (Python lines 2588-2700).
The actual integral engine and its validity are explicitly outside this model.
"""
from fractions import Fraction as F
import math


def key(task):
    return (task['group'],task['kind'],int(task['index']))


def round_rows(cap,rows,targets):
    d=F(cap['rounded_units']['I_lower'],10**24)
    if d<=0:raise ValueError('fresh denominator is not positive')
    a,b=F(*targets['a_h']),F(*targets['b_h'])
    output=[]
    for row in rows:
        task=row['task']; units={}
        for field,interval in row['raw_forms'].items():
            lo,hi=F(interval['lower']),F(interval['upper'])
            if not 0<=lo<=hi:raise ValueError('invalid nonnegative interval')
            units[field]=math.ceil(hi*10**18/d)
        if task['group'].startswith('outer'):
            c=F(task['young_q'],10**6)
            if c<=0 or c!=F(task['young']) or task['young_denominator']!=10**6:
                raise ValueError('Young parameter mismatch')
            cost=(c*units['root_square']+units['outer_face_square']/c)/10**18
        else:
            c=1-a-b if task['group'].startswith('old_inner') else 1-b
            if c<=0 or c!=F(task['restoration_coefficient']):raise ValueError('coefficient mismatch')
            cost=c*units['inner_face']/10**18
        budget=math.ceil(cost*10**12)
        output.append(dict(row,raw_relative_units=units,component_relative_units=budget,
                           normalized_loss_upper=str(d*F(budget,10**12))))
    return output


def assemble_model(cap,rows,tasks):
    """Model all task/coverage/aggregate arithmetic relevant to upstream passed.

    Like the read function, it does not compare against the fixed Lean tables.
    This is NOT a validation of the production numerical engine.
    """
    expected={key(t):t for t in tasks}; seen={}
    for row in rows:
        k=key(row['task'])
        if k not in expected or row['task']!=expected[k] or k in seen:
            raise ValueError('wrong or duplicate task')
        seen[k]=row
    if set(seen)!=set(expected) or sum(len(r['raw_forms']) for r in rows)!=149:
        raise ValueError('coverage mismatch')
    d=F(cap['rounded_units']['I_lower'],10**24)
    i=F(cap['rounded_units']['I_upper'],10**24)
    j=F(cap['rounded_units']['J_lower'],10**24)
    total=sum(r['component_relative_units'] for r in rows)
    loss=d*F(total,10**12)
    margin=F(2624989,10**7)*(j-loss)/i-1
    return dict(passed=margin>F(1,50000),final_margin_lower=str(margin),
                source_total_relative_units=total,source_normalization_denominator=str(d),
                normalized_source_loss_upper=str(loss),final_quotient_lower=str(margin+1),
                component_count=len(rows),raw_form_count=149)
