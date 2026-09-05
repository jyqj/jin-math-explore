#!/usr/bin/env python3
"""Exact direct-sum cross-checks for the contraction and its marked channel."""
from __future__ import annotations
import json,math,sys
from pathlib import Path
from fractions import Fraction as F
from itertools import product
from collections import Counter
import exact_poly as ep
from contract_stage import Moments,dual_mul,partitions,falling
from kernel_stage import lk,exp_iv


def naive(a,b,n):
 out=[F(0)]*n
 for i,x in enumerate(a):
  for j,y in enumerate(b[:max(0,n-i)]):out[i+j]+=x*y
 return out

def full_upper(seed,high,mark,minimum,n,bits):
 q=1<<bits;term=[q]+[0]*(n-1);a=[0]*n;b=[0]*n
 for r in range((n-1)//minimum+1):
  for extra,acc in [(0,a),(1,b)]:
   v=lk.eulerian_integers(r+extra+1);d=math.factorial(r+extra+1)
   v=[ep.ceildiv(t*q,d) for t in v]
   ans=ep.mul_up(term,v,n,bits)
   for i,x in enumerate(ans):acc[i]+=x
  if r<(n-1)//minimum:
   term=[ep.ceildiv(v,r+1) for v in ep.mul_up(term,high,n,bits)]
 return ep.mul_up(a,seed,n,bits),ep.mul_up(ep.mul_up(b,mark,n,bits),seed,n,bits)

def kernel_oracle():
 n=72;m=2;bits=160;q=1<<bits
 H=[F(0) if j<m or j>=12 else F(1,j) for j in range(n)]
 B=[H[j] if j<5 else F(0) for j in range(n)]
 L=[F(1,2**min(j,70)) for j in range(n)]
 term=[F(1)]+[F(0)]*(n-1);a=[F(0)]*n;b=[F(0)]*n
 for r in range((n-1)//m+1):
  for extra,target in [(0,a),(1,b)]:
   ans=naive(term,lk.carry(r+extra+1),n)
   for j,v in enumerate(ans):target[j]+=v
  term=[v/F(r+1) for v in naive(term,H,n)]
 a=naive(a,L,n);b=naive(naive(b,B,n),L,n)
 up=lambda v:[ep.ceildiv(x.numerator*q,x.denominator) for x in v]
 ua,ub=full_upper(up(L),up(H),up(B),m,n,bits)
 ep.require(all(F(u,q)>=x for u,x in zip(ua,a)) and all(F(u,q)>=x for u,x in zip(ub,b)),'full carry majorant failed')
 ep.require((n-1)//m==35,'test must include counts beyond32')
 return {'full_finite_channels_checked':2*n,'largest_tested_high_count':35,'max_upper_gap':str(max([F(u,q)-x for u,x in zip(ua,a)]+[F(u,q)-x for u,x in zip(ub,b)]))}

def compositions(total,d):
 if d==1:
  yield (total,);return
 for i in range(total+1):
  for rest in compositions(total-i,d-1):yield (i,)+rest

def direct_squares():
 n=8;bits=160;q=1<<bits;h=F(1,10)
 sigs=[(),(2,),(3,),(4,),(5,),(6,),(2,2),(2,3),(2,4),(3,3),(2,2,2)]
 c=[F((-1)**i*(i+1),17) for i in range(len(sigs))]
 alpha=[(j+1)*q//64 for j in range(n)];beta=[0 if j<2 else (j+3)*q//128 for j in range(n)]
 C=Counter()
 for i,s in enumerate(sigs):
  for j in range(i,len(sigs)):
   for block,mult in partitions(tuple(sorted(s+sigs[j]))).items():
    C[block]+=c[i]*c[j]*mult*(1 if i==j else 2)
 cases=0;interval_checks=0
 for d in [1,3,5]:
  en=Moments(alpha,beta,h,n=n,bits=bits)
  lo=[F(0)]*n;hi=[F(0)]*n;ml=[F(0)]*n;mu=[F(0)]*n
  for block,coef in C.items():
   if len(block)>d:continue
   if not block:z=en.power(d)
   else:z=dual_mul(en.power(d-len(block)),en.block(block),n,bits)
   coef*=falling(d,len(block))
   for r in range(n):
    if coef>=0:
     lo[r]+=coef*F(z[0][0][r],q);hi[r]+=coef*F(z[0][1][r],q)
     ml[r]+=coef*F(z[1][0][r],q);mu[r]+=coef*F(z[1][1][r],q)
    else:
     lo[r]+=coef*F(z[0][1][r],q);hi[r]+=coef*F(z[0][0][r],q)
     ml[r]+=coef*F(z[1][1][r],q);mu[r]+=coef*F(z[1][0][r],q)
  for r in range(n):
   direct=marked=F(0)
   for js in compositions(r,d):
    ts=[(j+F(1,2))*h for j in js]
    ps=[math.prod(sum(t**e for t in ts) for e in sig) for sig in sigs]
    p=sum((a*b for a,b in zip(c,ps)),F(0))
    w=math.prod(F(alpha[j],q) for j in js)
    markedw=sum((F(beta[js[i]],q)*math.prod(F(alpha[js[v]],q) for v in range(d) if v!=i) for i in range(d)),F(0))
    direct+=p*p*w;marked+=p*p*markedw;cases+=1
   ep.require(lo[r]<=direct<=hi[r] and ml[r]<=marked<=mu[r],'direct signed-square mismatch')
   interval_checks+=2
 return {'enumerated_configurations':cases,'direct_normal_and_marked_squares':interval_checks,'dimensions':[1,3,5]}

def test_fiber_formula():
 # Test both erased-coordinate witness and retained-coordinate witness terms.
 n=8;d=3;A=[F(j+1,11) for j in range(n)];B=[F(0) if j<2 else F(j,19) for j in range(n)]
 R=[F(0)]*n
 for i in range(4,8):R[i]=F(i+2,7)
 counts=0
 for r in range(n):
  fa=sum((A[j]*R[r+j] for j in range(n-r)),F(0));fb=sum((B[j]*R[r+j] for j in range(n-r)),F(0))
  for js in compositions(r,d):
   a=math.prod(A[j] for j in js)
   b=sum((B[js[i]]*math.prod(A[js[t]] for t in range(d) if t!=i) for i in range(d)),F(0))
   lhs=sum((R[r+j]*(B[j]*a+A[j]*b) for j in range(n-r)),F(0))
   ep.require(lhs==fb*a+fa*b,'two witness channels omitted');counts+=1
 return counts

def tests():
 packed=ep.tests();kernel=kernel_oracle();squares=direct_squares()
 carrytests=0
 for m in range(1,45):
  a=lk.eulerian_integers(m)
  b=[sum((-1)**j*math.comb(m+1,j)*(k+1-j)**m for j in range(k+2)) for k in range(m)]
  ep.require(a==b,'Eulerian inclusion-exclusion mismatch');carrytests+=len(a)
 rejected=[]
 for name,a in [('negative',[-1]),('floating',[1.0]),('boolean',[True])]:
  try:ep.conv_int(a,[1],1)
  except ValueError:rejected.append(name)
  else:raise AssertionError('invalid coefficient accepted')
 return dict(ok=True,scope='exact finite arithmetic tests; not independent mathematical review',packed=packed,kernel=kernel,squares=squares,fiber_configurations=test_fiber_formula(),eulerian_formula_coefficients=carrytests,rejected_invalid_inputs=rejected)
if __name__=='__main__':print(json.dumps(tests(),indent=2))
