# Pre-genesis RH attempt: exact rank–trace defect rigidity

Status: `proof_candidate` (not independently verified)

Attempt ID: `A-RH-RTD-0001`

Actor/run: `openai-gpt-5.6-pro / run-20260829-rh-rank-trace-defect-01`

Source base:

- `anthropics/formal-math@2bafb8c88f177284a2123b5fefa2ff84e2365eb6`
- `zeta23/Zeta23/ZeroSide/RankTraceMult.lean`
- `zeta23/Zeta23/ZeroSide/TightMult.lean`
- `zeta23/Zeta23/ZeroSide/Mult.lean`
- `zeta23/Zeta23/Assembly/SeamMult.lean`

This is a pre-genesis staging note. It does not create a governed Riemann-hypothesis Project, advance a Project head, prove the Riemann hypothesis, or upgrade any imported Zeta23 result.

## 1. Motivation

Zeta23 proves a multiplicity-aware rank–trace inequality for a decomposition

\[
P=\sum_{j=1}^s m_j v_jv_j^*,\qquad P\succeq0,
\]

and a Hermitian matrix \(Q\) whose positive inertia is at most \(b\). For a fixed \(c>0\), define

\[
g_c(x)=x^2-cx-(x-c)_+^2,
\qquad
k_c(a)=c^2-(c-a)_+^2.
\]

The Zeta23 inequality has the form

\[
2c\,\operatorname{tr}(P+Q)-\|P+Q\|_F^2
\le
\sum_j k_c(a_j)+c^2b,
\qquad a_j=m_j\|v_j\|^2.
\tag{RT}
\]

For the zeta-zero application, \(c=2\) drives the lower bound for simple critical-line zeros, and \(c=3\) drives the lower bound for distinct zeros. The existing source proves sharpness by explicit extremal configurations. The goal here is to expose every source of slack in (RT) simultaneously, so that any near-extremal zeta configuration must satisfy quantitative compatibility conditions.

## 2. Definitions

Let the Jordan decomposition of \(Q\) be

\[
Q=Q_+-Q_-,\qquad Q_+,Q_-\succeq0,\qquad Q_+Q_-=0.
\]

Let \(r_+=\operatorname{rank}(Q_+)\) and let \(\Pi_+\) be the orthogonal projection onto the support of \(Q_+\). By spectral functional calculus, put

\[
A_c=(P-cI)_+,
\qquad
B_c=(cI-P)_+.
\]

The scalar identity

\[
x-c=(x-c)_+-(c-x)_+
\]

lifts to

\[
P-cI=A_c-B_c,
\qquad A_cB_c=0.
\]

Define the Schur-transfer defect

\[
J_c(P;\{m_j,v_j\})
:=
\operatorname{tr}g_c(P)-\sum_j g_c(a_j).
\]

The Zeta23 Schur-transfer step gives \(J_c\ge0\) under its atom-decomposition assumptions.

Define the full rank–trace defect

\[
\Delta_c
:=
\sum_j k_c(a_j)+c^2b
-
\left(2c\operatorname{tr}(P+Q)-\|P+Q\|_F^2\right).
\]

## 3. Candidate theorem: exact nonnegative defect decomposition

### Theorem A — exact decomposition

Under the assumptions above, with \(b\ge r_+\),

\[
\boxed{
\begin{aligned}
\Delta_c={}&J_c
+2\operatorname{tr}(PQ_+)
+\|Q_- - A_c\|_F^2
+2\operatorname{tr}(B_cQ_-)\\
&+\|Q_+-c\Pi_+\|_F^2
+c^2(b-r_+).
\end{aligned}}
\tag{D}
\]

Every term on the right is nonnegative. Consequently, (D) is not merely another proof of (RT): it is a quantitative rigidity theorem for every near-equality configuration.

### Proof

First observe

\[
k_c(a)=c^2-(c-a)_+^2
      =2ca-a^2+g_c(a),
\]

because \(g_c(a)=a^2-ca-(a-c)_+^2\) and
\(a-c=(a-c)_+-(c-a)_+\). Summing and using
\(\sum_j a_j=\operatorname{tr}P\),

\[
\sum_j k_c(a_j)
=2c\operatorname{tr}P-
 \sum_j a_j^2+
 \sum_j g_c(a_j).
\]

The Schur-transfer identity gives

\[
\sum_j g_c(a_j)=\operatorname{tr}g_c(P)-J_c.
\]

Since

\[
\operatorname{tr}g_c(P)
=
\operatorname{tr}(P^2)-c\operatorname{tr}P-
\|A_c\|_F^2,
\]

an equivalent and more direct bookkeeping route is to expand \(\Delta_c\) and group all scalar/atomic terms into \(J_c\). This yields

\[
\Delta_c
=J_c+c^2b+
\|Q\|_F^2+2\operatorname{tr}(PQ)-2c\operatorname{tr}Q
-
\|A_c\|_F^2.
\tag{1}
\]

Using \(Q=Q_+-Q_-\), \(Q_+Q_-=0\), and
\(P-cI=A_c-B_c\), the negative part contributes

\[
\begin{aligned}
\|Q_-\|_F^2-2\operatorname{tr}(PQ_-)+2c\operatorname{tr}Q_- -\|A_c\|_F^2
&=\|Q_-\|_F^2-2\operatorname{tr}((P-cI)Q_-)-\|A_c\|_F^2\\
&=\|Q_--A_c\|_F^2+2\operatorname{tr}(B_cQ_-).
\end{aligned}
\tag{2}
\]

For the positive part,

\[
\begin{aligned}
c^2b+
\|Q_+\|_F^2+2\operatorname{tr}(PQ_+)-2c\operatorname{tr}Q_+
={}&2\operatorname{tr}(PQ_+)\\
&+\|Q_+-c\Pi_+\|_F^2+c^2(b-r_+),
\end{aligned}
\tag{3}
\]

because \(Q_+=\Pi_+Q_+\Pi_+\) and \(\|\Pi_+\|_F^2=r_+\). Substituting (2) and (3) into (1) proves (D).

Nonnegativity follows from:

- \(J_c\ge0\) by the Zeta23 Schur-transfer theorem;
- \(\operatorname{tr}(PQ_+)\ge0\) for positive semidefinite \(P,Q_+\);
- \(\operatorname{tr}(B_cQ_-)\ge0\) for positive semidefinite \(B_c,Q_-\);
- squared Frobenius norms are nonnegative;
- \(b\ge r_+\).

## 4. Quantitative consequences

If \(\Delta_c\le\varepsilon\), then each nonnegative term is at most \(\varepsilon\). In particular,

\[
\|Q_--(P-cI)_+\|_F\le\sqrt\varepsilon,
\tag{4}
\]

\[
\|Q_+-c\Pi_+\|_F\le\sqrt\varepsilon,
\tag{5}
\]

\[
\operatorname{tr}(PQ_+)\le\varepsilon/2,
\qquad
\operatorname{tr}((cI-P)_+Q_-)\le\varepsilon/2,
\tag{6}
\]

\[
J_c\le\varepsilon,
\qquad
b-r_+\le\varepsilon/c^2.
\tag{7}
\]

Thus near equality forces all of the following at once:

1. the negative part of \(Q\) nearly equals the spectral excess \((P-cI)_+\);
2. every positive eigenvalue of \(Q\) is nearly \(c\);
3. the positive eigenspace of \(Q\) is nearly orthogonal to the range of \(P\);
4. \(Q_+\) nearly uses the entire allowed positive-inertia budget;
5. the atom decomposition nearly saturates the Schur-transfer step.

These are substantially stronger constraints than a scalar proportion bound.

## 5. Dual-compression compatibility inequality

Let two compression systems \((P_i,Q_i)\), \(i=1,2\), use the same parameter \(c\), with defects \(\Delta_{c,i}\). From (4) and the triangle inequality,

\[
\sqrt{\Delta_{c,1}}+\sqrt{\Delta_{c,2}}
\ge
\Bigl(
\|(P_1-cI)_+-(P_2-cI)_+\|_F
-
\|Q_{1,-}-Q_{2,-}\|_F
\Bigr)_+.
\]

Therefore

\[
\boxed{
\Delta_{c,1}+\Delta_{c,2}
\ge
\frac12
\Bigl(
\|(P_1-cI)_+-(P_2-cI)_+\|_F
-
\|Q_{1,-}-Q_{2,-}\|_F
\Bigr)_+^2.}
\tag{C}
\]

This identifies a precise analytic frontier for the proposed “joint-compression rigidity” route:

> Prove that two overlapping Weil/Gabor compressions make the thresholded positive parts of the on-line Gram matrices vary more than the negative parts generated by the same off-line zero pairs.

Any quantitative lower bound in (C), after controlling the Zeta23 tail perturbation, yields a nonzero aggregate slack and therefore rules out simultaneous near-saturation of the two scalar certificates.

## 6. Two-parameter incompatibility on the same matrix pair

For the same \((P,Q)\), take \(0<c<d\) and a common inertia budget \(b\). Applying the parallelogram inequality to the two negative-part square terms and to the two positive-part terms gives

\[
\boxed{
\Delta_c+\Delta_d
\ge
\frac12\|(P-cI)_+-(P-dI)_+\|_F^2
+
\frac12(d-c)^2b.}
\tag{P}
\]

For the Zeta23 choices \(c=2,d=3\),

\[
\Delta_2+\Delta_3
\ge
\frac12\|(P-2I)_+-(P-3I)_+\|_F^2+\frac b2.
\]

This is useful when off-line pairs are present, because they consume positive-inertia budget. It does **not**, by itself, improve the simple-zero bound; the following exact countermodel explains why.

## 7. Exact no-go model for merely combining the c=2 and c=3 inequalities

Take five mutually orthogonal unit vectors. Give four atoms multiplicity \(1\) and one atom multiplicity \(2\):

\[
P=\operatorname{diag}(1,1,1,1,2),
\qquad Q=0,
\qquad b=0.
\]

Then the total multiplicity is

\[
N=1+1+1+1+2=6,
\]

there are four simple zeros and five distinct zeros. Hence

\[
\frac{N_0^s}{N}=\frac46=\frac23,
\qquad
\frac{N_d}{N}=\frac56.
\]

Moreover,

\[
4\operatorname{tr}P-\|P\|_F^2-2N
=4\cdot6-8-12=4=N_0^s,
\]

and

\[
6\operatorname{tr}P-\|P\|_F^2-3N
=6\cdot6-8-18=10=2N_d.
\]

Thus the \(c=2\) and \(c=3\) scalar certificates are simultaneously sharp in a completely on-line orthogonal model.

### No-go conclusion

No argument that merely combines the two existing scalar inequalities, without using an additional cross-window, cross-scale, geometric, depth-sensitive, or higher-moment constraint, can force either

\[
N_0^s/N>2/3
\quad\text{or}\quad
N_d/N>5/6.
\]

This narrows the search space: the next useful object is not another linear combination of the \(c=2\) and \(c=3\) count certificates, but a compatibility estimate such as (C).

## 8. Special c=2 frame-energy interpretation

Assume all atom loads satisfy \(a_j\le2\). Then

\[
g_2(a_j)=a_j^2-2a_j,
\]

and direct expansion gives

\[
J_2
=
\sum_{i\ne j}m_im_j|\langle v_i,v_j\rangle|^2
-
\|(P-2I)_+\|_F^2.
\tag{F}
\]

In particular, if \(P\preceq2I\) and \(Q=0\), then

\[
\Delta_2=J_2
=
\sum_{i\ne j}m_im_j|\langle v_i,v_j\rangle|^2.
\]

So in the no-off-line, sub-threshold regime, the exact slack is the weighted off-diagonal Gram energy. This gives a second concrete route to an improvement: prove that two or more genuine zeta compressions cannot make all relevant on-line atoms mutually orthogonal at once.

## 9. What has and has not been established

Established in this attempt, subject to independent checking:

- the exact identity (D);
- quantitative rigidity estimates (4)–(7);
- the dual-compression compatibility bound (C);
- the same-matrix two-parameter bound (P);
- the exact five-atom no-go model;
- the frame-energy formula (F).

Evidence currently attached:

- a complete algebraic derivation in this note;
- deterministic numerical checks over random Hermitian test instances;
- an exact integer check of the five-atom no-go model.

Not established:

- an unconditional improvement beyond Zeta23's \(2/3\) or \(0.67250\) constants;
- a nonzero lower bound for the right side of (C) for actual zeta-zero compressions;
- the transfer of finite-dimensional defect to the final asymptotic theorem with all tail errors tracked;
- independent verification or Lean formalization of this candidate;
- any implication toward the full Riemann hypothesis.

## 10. Next decisive lemma

The most focused next target is the following.

> **Two-window separation lemma (candidate frontier).** Find two admissible tapers or two nearby compression scales for which, uniformly along an unbounded sequence of heights,
> \[
> \|(P_1-2I)_+-(P_2-2I)_+\|_F
> \ge
> \|Q_{1,-}-Q_{2,-}\|_F+\eta\sqrt{N(T,2T)}
> \]
> for some fixed \(\eta>0\), or prove a weaker averaged form sufficient after summation over windows.

By (C), this would force aggregate defect \(\gg \eta^2N(T,2T)\). The remaining task would then be to propagate that defect through `SeamMult.lean` and the prime-side asymptotics into an explicit improvement in the simple-zero proportion.

The alternative outcome is also valuable: construct an exact joint-compression model satisfying all currently known constraints and simultaneously saturating both windows. Such a model would certify that a new analytic observable is necessary.
