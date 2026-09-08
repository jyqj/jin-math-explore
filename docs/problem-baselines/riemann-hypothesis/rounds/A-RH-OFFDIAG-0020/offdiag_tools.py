"""Finite tools for A-RH-OFFDIAG-0020; no actual-zero or asymptotic oracle."""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np

@dataclass(frozen=True)
class Profile:
    terms: tuple[tuple[float, float], ...]

    def values(self, u):
        x = np.asarray(u)
        out = sum(a*np.exp(2j*np.pi*v*x) for v, a in self.terms)
        if np.max(np.abs(np.imag(out))) > 1e-10*(1+np.max(np.abs(out))):
            raise ValueError('profile must be real on the real axis')
        return np.real(out)

    def transform(self, z):
        z = np.asarray(z, dtype=complex)
        return sum(a*np.sinc(z+v) for v, a in self.terms)

    def integral(self):
        return float(sum(a*np.sinc(v) for v,a in self.terms))

    def normalized(self):
        z = self.integral()
        if z <= 0:
            raise ValueError('positive integral required')
        return Profile(tuple((v,a/z) for v,a in self.terms))

    def product(self, other):
        terms = {}
        for v,a in self.terms:
            for w,b in other.terms:
                key = round(v+w, 13)
                terms[key] = terms.get(key,0.)+a*b
        return Profile(tuple(sorted(terms.items())))

    def potential(self, u):
        """Kf(x)=int |x-y| f(y)dy for an even profile; solve (Kf)''=2f."""
        x=np.asarray(u); m=self.integral()
        a0=sum(a for v,a in self.terms if abs(v)<1e-14)
        out=a0*(x*x-.25)+m/2
        for v,a in self.terms:
            if abs(v)>1e-14:
                out=out+a*(np.cos(np.pi*v)-np.exp(2j*np.pi*v*x))/(2*np.pi**2*v*v)
        return np.real(out)


def B(theta: float, f: Profile, g: Profile, nodes=96):
    if not 0 < theta <= 1:
        raise ValueError('theta outside (0,1]')
    u,w=np.polynomial.legendre.leggauss(nodes); u=u/2; w=w/2
    return float(np.dot(w,f.values(u)*(g.values(u)/theta+theta*g.potential(u))))


def make_symbol(taps):
    """Autocorrelation: g(x)=|sum b_j exp(-2 pi i j x)|^2 >=0."""
    b=np.asarray(taps,dtype=complex)
    if b.ndim!=1 or len(b)==0 or not np.isfinite(b).all():
        raise ValueError('nonempty finite taps required')
    out={}
    for j in range(len(b)):
        for k in range(len(b)):
            out[j-k]=out.get(j-k,0j)+b[j]*np.conj(b[k])
    return out


def symbol_value(coeffs, x):
    x=np.asarray(x)
    out=sum(c*np.exp(-2j*np.pi*h*x) for h,c in coeffs.items())
    return np.real_if_close(out)


def symbol_mean(coeffs, theta=1.):
    return float(np.real(sum(c*np.exp(-1j*np.pi*h*theta)*np.sinc(h*theta)
                             for h,c in coeffs.items())))


def toeplitz_test(q, d_values, coeffs):
    d=np.asarray(d_values,dtype=float)
    if q < 1 or d.shape!=(q,) or (d < 0).any() or not np.isfinite(d).all():
        raise ValueError('invalid matrix dimension or test weights')
    root=np.sqrt(d)
    C=np.empty((q,q),dtype=complex)
    for j in range(q):
        for k in range(q):
            C[j,k]=root[j]*root[k]*coeffs.get(j-k,0.)
    if not np.allclose(C,C.conj().T,atol=1e-10):
        raise ValueError('symbol is not Hermitian')
    return C


def expand_orbits(t,m,a):
    t=np.asarray(t,float); m=np.asarray(m); a=np.asarray(a,float)
    if t.ndim!=1 or not (t.shape==m.shape==a.shape):
        raise ValueError('orbit shapes differ')
    if not np.isfinite(t).all() or not np.isfinite(a).all() or (a<0).any():
        raise ValueError('invalid coordinates/depth')
    if not np.all(m==m.astype(int)) or (m<1).any():
        raise ValueError('positive integer multiplicities required')
    if np.any((a>0)&((m.astype(int)%2)!=0)):
        raise ValueError('positive-depth pair mass must be even')
    if len(set(t.tolist()))!=len(t):
        raise ValueError('this checker uses distinct centers; group duplicates first')
    z=[]
    for x,c,y in zip(t,m.astype(int),a):
        if y==0:
            z.extend([complex(x)]*c)
        else:
            z.extend([x+1j*y/(2*np.pi)]*(c//2))
            z.extend([x-1j*y/(2*np.pi)]*(c//2))
    return np.array(z,complex)


def operators(q,t,m,a,r: Profile):
    if not isinstance(q,int) or not 1<=q<=512:
        raise ValueError('test implementation supports 1<=q<=512')
    z=expand_orbits(t,m,a)
    if not len(z):
        raise ValueError('nonempty source required')
    u=(np.arange(q)-(q-1)/2)/q
    rv=r.values(u)
    if (rv<0).any() or not np.isfinite(rv).all() or rv.sum()<=0:
        raise ValueError('nonnegative sampled profile required')
    p=rv/rv.sum(); v=np.sqrt(p)[:,None]*np.exp(2j*np.pi*u[:,None]*np.asarray(t))
    m=np.asarray(m,int); a=np.asarray(a,float)
    simple=(m==1)&(a==0); V=v[:,simple]
    G=v[:,~simple]*np.sqrt(m[~simple])*np.cosh(u[:,None]*a[~simple])
    H=v[:,~simple]*np.sqrt(m[~simple])*np.sinh(u[:,None]*a[~simple])
    S=V@V.conj().T; T=S+G@G.conj().T-H@H.conj().T
    return {'T':T,'S':S,'z':z,'u':u,'r':rv,'Z':float(rv.mean()),
            'N':len(z),'n':int(simple.sum()),'p':p}


def lag_products(data, d_values, h):
    """Exact finite pair formula for a nonnegative lag, not its limiting approximation."""
    q=len(data['u'])
    if not isinstance(h,int) or not 0<=h<q:
        raise ValueError('lag must satisfy 0<=h<q')
    d=np.asarray(d_values,float)
    if d.shape!=(q,) or (d<0).any():
        raise ValueError('invalid d')
    u=data['u']; z=data['z']; Z=data['Z']; r=data['r']; N=data['N']
    v=np.sqrt(d*r); w=z[:,None]-z[None,:]
    Fr=np.sum(r[:,None,None]*np.exp(2j*np.pi*u[:,None,None]*w),axis=0)/q
    lead=v[:q-h]*v[h:]
    H=np.sum(lead[:,None,None]*np.exp(2j*np.pi*u[:q-h,None,None]*w),axis=0)/q
    phase=np.exp(-2j*np.pi*h*z/q)[None,:]
    pair=np.sum(phase*H*Fr)/(N*Z*Z)
    # Exact source/target ordering is deliberate: phase contains the SECOND point.
    wrong_difference_only=np.sum(H*Fr)/(N*Z*Z)
    T=data['T']; T2=T@T; roots=np.sqrt(d[:q-h]*d[h:])
    direct=sum(roots[j]*T2[j,j+h] for j in range(q-h))/N
    beta=float(lead.sum()/(q*Z))
    linear=beta*np.sum(np.exp(-2j*np.pi*h*z/q))/N
    simple_centers=[]
    # S gives the simple version directly; list not reconstructed from repeated members.
    direct_linear=sum(roots[j]*T[j,j+h] for j in range(q-h))/N
    return direct,pair,direct_linear,linear,wrong_difference_only


def kernel_pair(f: Profile,g: Profile,z):
    w=np.asarray(z)[:,None]-np.asarray(z)[None,:]
    return f.transform(w)*g.transform(w)


def continuous_integral(f: Profile,g: Profile,z,nodes=80):
    u,w=np.polynomial.legendre.leggauss(nodes); u=u/2; w=w/2
    v=u[:,None]+u[None,:]
    Bz=sum(np.exp(2j*np.pi*zz*v) for zz in z)
    return float(np.sum((w*f.values(u))[:,None]*(w*g.values(u))[None,:]*abs(Bz)**2)/len(z))
