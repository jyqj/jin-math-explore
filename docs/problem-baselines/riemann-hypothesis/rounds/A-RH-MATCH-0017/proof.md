# A-RH-MATCH-0017 — certified orbit matching with a charged deletion budget

Date: 2026-09-07. Issue #106. Status: **proof_candidate; no independent receipt**.
Parent: A-RH-SOURCE-0016 at `02e081262c0f1cadc1ad87043915bd7a2c65c27c`,
proof blob `93b456345071bd34a794511ff29e620fee6d1ae5`.
The contribution is a finite construction/certificate interface for that parent's
supplied injection. It is not a proof that actual zeta zeros admit small-cost
assignments. Hall matching, augmenting paths and residual-flow optimality are
classical, not new discoveries; primary attributions are in source-scope.md.

## 1. Objects, exact mass, and the deliberately explicit geometry

A finite source consists of conjugation orbits i=1,...,n_orb. Each has real center
x_i, normalized depth a_i>=0 and original integer mass c_i>=1. A simple real
atom has c_i=1 and a_i=0. A real nonsimple atom has a_i=0,c_i>=2. A nonreal
reflection pair has even c_i>=2 and members x_i +/- i a_i/(2pi). It is ONE
matching object, not two. Different original zeros are not merged.

Clip each nonsimple orbit to mass two and leave original simples unchanged:

    m_i=1 if c_i=1, otherwise m_i=2; mandatory removal b_i=c_i-m_i.

No clipping creates a simple atom. Further removal is of whole clipped orbits.
Choose the target cell count Q>=1 BEFORE solving, an inset 0<e<=1/2, a maximum
displacement h>=0 and retained depth cap A. Target cell j=0,...,Q-1 uses the
closed interval J_j=[j+e,j+1-e], a subset of its half-open unit cell. This
removes endpoint-attainment ambiguities; the inset is a restriction, not an
assertion about all possible half-open-cell matchings. Retained depths are not
changed, so the parent's depth-transport error Z is zero.

For a_i<=A let y_ij be the metric projection of x_i onto J_j and set

    N_i={j: |x_i-y_ij|<=h}; for a_i>A set N_i=empty.              (1)

These are empty sets or consecutive integer intervals. Before intersecting
with {0,...,Q-1}, their integer bounds are
ceil(x_i-h-1+e) and floor(x_i+h-e). Projection is the least-displacement target
in a chosen cell. Every allowed target assignment has an at-least-as-good one
using these projections, without changing any retention or deletion decision.

A feasible assignment chooses z_i in {0,1} and an injection pi on {i:z_i=1},
with pi(i) in N_i and

    sum_i m_i z_i=Q.                                          (2)

This MASS equation is not a cardinality condition. With N=sum c_i and n the
number of original simples, n_del the number of deleted original simples,

    removed mass=N-Q,
    s_model=(n-n_del)/Q=(N/Q)(n/N)-n_del/Q.                     (3)

The target period has mean mass one. It is not legitimate to solve a matching
and then silently reset Q to its retained mass: this would change the target
cell set, admissible edges, all normalizations and the certificate.

The mathematical statements allow arbitrary finite real inputs. The delivered
exact solver accepts rational x_i,a_i,e,h,A and objective coefficients. Certified
interval ordinates for actual zeros, with rounding residuals, are a separate
unimplemented input layer. Implementation guards Q<=128, n_orb<=256 and depths
<=64 are resource limits, not hypotheses of the abstract theorems.

## 2. Exact interval-Hall deficiency and a lower charge witness

This section initially ignores (2); it concerns maximum whole-orbit injection.
Let n_empty=#{i:N_i=empty}. For consecutive cells I=[u,v], define

    C(I)=#{i: nonempty N_i subset I}.

**Lemma 1.** The minimum number of whole orbits left unmatched is exactly

    d_H=n_empty+max_{pairwise disjoint integer intervals I_l}
                        sum_l (C(I_l)-|I_l|).                 (4)

The empty interval collection is allowed. In particular a full injection exists
iff n_empty=0 and C(I)<=|I| for EVERY consecutive I. Checking only the full
range, or only the single worst interval to compute d_H, is insufficient.

Proof. For any bipartite graph the maximum deficiency is
max_S(|S|-|N(S)|)=n_orb-maximum_matching_size. One direct proof starts from a
maximum matching, explores alternating paths from all unmatched left vertices,
and obtains reached left/right sets S,R with R=N(S) and
|S|-|R| equal to the unmatched count. A reached free right vertex would give
an augmentation, impossible. Conversely every matching leaves at least
|S|-|N(S)| vertices of S unmatched. This proves both inequalities, including
empty neighborhoods, without assuming the graph has a perfect matching.

For interval neighborhoods, decompose N(S) into its maximal consecutive
components I_l. Each nonempty N_i for i in S lies in just one component, so
|S|-|N(S)|<=n_empty+sum_l(C(I_l)-|I_l|). Conversely, for any disjoint I_l,
choose all nonempty neighborhoods contained in one of them, plus all empty
ones. Their union of neighbors is contained in union I_l, giving a deficiency
at least that displayed sum. This proves (4).

An exact dynamic program evaluates it: D(-1)=0, and

    D(v)=max(D(v-1), max_{0<=u<=v}{D(u-1)+C([u,v])-(v-u+1)}).

Then d_H=n_empty+D(Q-1). Recording the selected intervals gives an obstruction
witness. This formula is elementary interval matching, not a novelty claim.
It does NOT enforce exact retained mass or prefer inexpensive deletions.

There is also an energy-CHARGE lower certificate. For a violating interval I,
put t=C(I)-|I|>0 and S_I={i:nonempty N_i subset I}. Every injection of a retained
subset deletes at least t whole clipped orbits from S_I. Let l_i<=cosh(a_i) be
positive lower bounds and let W_I be the sum of the t smallest m_i l_i in S_I.
Let K_I be the number of DISTINCT original integer cells containing S_I. For
the parent's actual depth-weighted deletion charge Xi_1, Cauchy-Schwarz gives

    Xi_1 >= W_I^2/(Q K_I).                                    (5)

Mandatory clipping only adds nonnegative deleted coefficients, so cannot
invalidate this lower bound. Several witnesses can be summed if their ORIGINAL
source-cell sets are disjoint; disjoint TARGET intervals alone do not justify
summing (5). Empty neighborhoods force deletion separately.

A lower bound for Xi_1 is NOT a lower bound for the signed operator norm.
Xi is a sufficient majorizing charge, and cancellation can reduce the actual
operator. This distinction is essential for negative conclusions.

## 3. A separable upper charge, including all mandatory clipping

Choose rational upper bounds w_i>=cosh(a_i). In each original half-open integer
cell k define

    W_k=sum_{floor x_i=k} c_i w_i,
    R_k(z)=sum_{floor x_i=k}(c_i-m_i z_i)w_i,
    Xi_enc=Q^(-1)sum_k R_k(z)^2,
    Xi_hat=Q^(-1)sum_k W_k R_k(z).

Because 0<=R_k<=W_k and cosh(alpha a)<=cosh(a) for 0<alpha<=1,

    Xi_alpha <= Xi_enc <= Xi_hat.                             (6)

The last expression is linear in retention indicators; the first enclosed
quadratic expression can be recomputed after solving and is often sharper.
A mandatory clipped coefficient is charged at its ORIGINAL center and depth.
No source cell capacity or depth cap is assumed for the deleted part.

The useful supplementary sufficient condition is explicit: if W_k<=B for all
source cells, then Xi_hat<=(B/Q)sum_i(c_i-m_i z_i)w_i. If original cell mass is
<=M and all w_i<=w_max, this is at most
M w_max^2 (N-Q)/Q. Thus count-based smallness is safe only with the additional
local-load/depth bounds; the parent's count-only counterexamples remain valid.

Set P=Q^(-1)sum_{retained i}m_i(x_i-y_i,pi(i))^2. For given nonnegative
lambda,mu,nu, minimize the NONNEGATIVE scalar surrogate

    F=lambda Q P + mu Q Xi_hat + nu n_del.                     (7)

It penalizes both displacement and a rigorous deletion-energy majorant, while
recording original simple-count loss. It is not the true quadratic deletion
objective, the actual signed residual norm, or a general multi-budget feasibility
problem. Scalarization need not find every Pareto-optimal constrained solution.

For lambda,mu,nu>0, any returned F gives simultaneously
P<=F/(lambda Q), Xi_alpha<=F/(mu Q), n_del/Q<=F/(nu Q). Small F/Q is therefore
a sufficient common error criterion. A LARGE optimum of (7) excludes only small
SURROGATE cost; it does not rule out a small actual Xi or a small operator norm.

## 4. Exact mass-preserving minimum-cost flow and its certificates

Let r2 be the number of retained nonsimple orbits, and r1 the number of retained
simples. Equation (2) is equivalent to r1=Q-2r2 with
0<=r2<=floor(Q/2). Enumerate EVERY such r2, including infeasible quotas.
For one quota create the directed network

    source -> class 1 (capacity r1), class 2 (capacity r2);
    class m_i -> orbit i (capacity 1);
    orbit i -> cell j in N_i (capacity 1);
    cell j -> sink (capacity 1).

All but the orbit-cell edges have cost zero. Give that edge cost

    lambda m_i(x_i-y_ij)^2 - mu W_floor(x_i) m_i w_i
                                  -nu 1_{m_i=1}.              (8)

Send exactly r1+r2 units. Integrality and the capacity constraints give exactly
r1 retained simples and r2 retained nonsimple orbits, with one cell each.
Conversely every feasible assignment of that quota defines such an integral
flow. The constant baseline is

    B=mu sum_k W_k^2 + nu n.

The flow cost plus B is EXACTLY (7). Mandatory clipping remains in B minus the
retained rewards; it has not disappeared from the objective. Taking the least
cost over all feasible quotas therefore finds the global optimum of (7).

The implementation uses exact rational Bellman-Ford shortest augmenting paths,
not float tolerances or an assumed Monge/order property. The initial network is
a DAG, so it has no negative-cost cycle despite negative edge costs. A shortest
augmentation from a minimum-cost flow of a given integer value produces a
minimum-cost flow of the next value: the difference with any competitor
splits into one residual source-sink path plus cycles, and all residual cycles
of the old optimum have nonnegative cost. No path means maximum flow has been
reached. At most Q unit augmentations occur per quota; a deliberately coarse
arithmetic-operation bound for all quotas is O(Q^2 |V| |E|). This ignores
rational bit complexity and is not advertised as a large-zero-data solver.

**Lemma 2 (checkable certificates).** For a full flow f, furnish rational node
potentials p_v such that EVERY residual arc u->v of cost c has

    c+p_u-p_v >=0.                                            (9)

Check capacities, integral flows, conservation and required value directly.
For any competitor of the same value, its difference from f decomposes into
residual cycles. Potentials telescope on each cycle, so (9) forces a nonnegative
cost change. This proves optimality. Such potentials exist for a minimum-cost
flow: add a virtual zero-edge source to all vertices and use shortest distances
when no negative residual cycle exists.

For an infeasible quota, furnish a feasible flow of value v<r1+r2 and a source/
sink separating cut whose ORIGINAL forward capacity is v. Summing conservation
on the cut bounds any flow value by v, proving infeasibility. These cut and
potential arguments are classical network-flow certificates, re-derived here
so the archive does not require trust in an optimizer library.

The checker reconstructs the graph from canonical rational INPUT, validates all
quota certificates, and then compares their exact objectives. It never calls
the optimizer during certificate verification. It also recomputes the complete
assignment and charge ledger. Seven corrupted copies are explicitly rejected.
This is same-run exact finite checking, not a fresh independent-mathematics
receipt or a formal kernel proof. The verifier and solver share input parsing;
independent brute-force checks of small instances provide a separate algorithmic
check, not a claim of full software verification.

## 5. How a successful assignment enters the source operator budget

Let A_source,alpha be the finite signed source operator on the unit-normalized
alpha-box, and S_alpha=||A_source,alpha||_HS^2/N. Apply the parent's deletion
bound and supplied-transport inequality to the NOW CONSTRUCTED retained core.
Its depths stay unchanged and do not exceed A. Let

    C_alpha=3+1/(3alpha^2),
    L_alpha,h=sqrt(2/alpha)[exp(pi alpha(h+1/2))+exp(pi alpha/2)],
    eps_alpha=sqrt(C_alpha Xi_enc)
                  +pi alpha L_alpha,h cosh(alpha A) sqrt(P).  (10)

Then

    ||A_source,alpha-A_target,alpha||_HS/sqrt(Q)<=eps_alpha.    (11)

For audit, the deletion kernel has absolute bound
cosh(alpha a_i)cosh(alpha a_j), and away from zero separation the bound is divided
by pi^2 alpha^2 d^2. Grouping by ORIGINAL cells gives the convolution sequence
1 at lags 0 and +/-1, and 1/[pi^2 alpha^2(|r|-1)^2] otherwise. Its sum is
C_alpha, proving the first term in (10) with (6). No signed cross term is
assumed positive. The transport term expands the retained exponential synthesis
about the distinct target integer cells. Source/target displacements from cell
midpoints are bounded by h+1/2 and 1/2 respectively; the hyperbolic synthesis
product bounds give exactly the second term. This is the pinned parent's
lemma, not a newly claimed constant or an independent audit of that lemma.

Periodize only the target list, with Q cells and mean mass one. For Q>=2 its
periodic moment satisfies the parent's finite-boundary estimate

    E_model,alpha <= U_alpha
      :=(sqrt((N/Q)S_alpha)+eps_alpha)^2+b_alpha,A(Q),
    b_alpha,A(Q)=cosh(alpha A)^2/Q
                    [8+32(2+log Q)/(pi^2 alpha^2)].            (12)

Keep s_model=(n-n_del)/Q EXACT. Put Delta=s_model+U_1-2. If Delta<0, the
asserted assignment and source bounds are inconsistent. Otherwise the
round-15 mixed-model candidate, inherited through round 16, implies

    U_alpha+Err_alpha,A(L,Delta)
                    >= f_alpha(2-s_model)+c_alpha,            (13)
    f_alpha=(2alpha-1)/alpha^2, c_alpha=(1-alpha)/alpha^2.

Here Err is exactly A-RH-HSTAB-0015 equations (18),(21), not an error term
invented or estimated by the matching solver. This last implication is
DEPENDENT on that unverified analytic candidate. The combinatorial flow and
certificate theorems do not require accepting it or the source PC theorem.

For sequences with Q->infinity, fixed h,A and positive objective weights,
F*/Q->0 suffices for eps_alpha->0 at both 1 and 3/4. Still retain N/Q and
s_model. Nothing here proves F*/Q->0 for actual zeros. The parent's fixed
subcritical source bandwidth theta gives kappa(alpha theta), NOT kappa(alpha),
and its endpoint/moving-bandwidth limitations remain unchanged. The exact
solver contains no zero enumeration or source-asymptotic experiment.

## 6. Three exact failures that the new interface prevents

**Weighted order preservation is false for COST.** Take Q=3, e=1/2, h=3/2,
all depths zero, original masses (1,2), and centers (0,1/10). There are no
removals because N=Q. The order-preserving least-cost assignment uses targets
(1/2,3/2) and has displacement sum 417/100. The crossing assignment to
(3/2,1/2) has sum 257/100 and is globally optimal (the third cell cannot improve
these distances). Thus unweighted uncrossing cannot justify an ordered
weighted-cost dynamic program. This does not deny existence of an ordered
maximum-cardinality interval matching; the statement concerns the objective.

**Disjoint overloads add; exact mass can fail even without overload.** At Q=3,
e=1/16,h=0, place simple points 9/20,11/20,49/20,51/20. Their neighborhoods
are {0},{0},{2},{2}. The largest SINGLE-interval deficiency is one, but d_H=2.
Separately, two mass-two real orbits in distinct cells admit full injection
into three cells, but cannot retain mass Q=3 while keeping whole clipped
orbits. Their possible retained masses are 0,2,4. A Hall PASS alone does not
solve the source/core normalization problem.

**Correct global counts do not give small local charge.** For Q=6k, repeat at
locations 6b+(1/5,3/10,2/5,1/2) four simple real orbits, plus a real double at
6b+3/2, for b=0,...,k-1. Set e=1/16,h=1/8. Total source mass is Q, simple
fraction is 2/3, and orbit count is 5Q/6<Q. Nevertheless each group of four
simples has only cell 6b available, so every injection deletes at least three
of them, giving d_H=3k. The original cells for these witnesses are disjoint,
and the actual depth-weighted deletion charge satisfies

    Xi_1 >= 9k/(6k)=3/2.                                     (14)

With exact retained mass Q no assignment exists at all. If mass is relaxed,
(14) still obstructs a small CHARGE at the chosen reference normalization.
All points are distinct except for the intentional real-double multiplicity.
These examples are not zeta zeros, do not have a proved small signed defect,
and do not satisfy all PC/moment constraints. They refute only using mean
mass, global simple ratio or spare orbit capacity as a matching theorem.

## 7. Exact transcendental enclosures and next research obligation

For a rational a>=0, let t_n=a^(2n)/(2n)! and S_n=sum_{j=0}^n t_j. Whenever
r=a^2/[(2n+3)(2n+4)]<1, positivity and decreasing subsequent ratios give

    S_n <= cosh(a) <= S_n+t_(n+1)/(1-r).                       (15)

These bounds provide l_i,w_i for (5)-(8) using rational arithmetic. The solver
stops when the enclosure width is <=10^-18(1+S_n); that threshold controls
surrogate conservatism, not the validity of the enclosure. Depth zero is exact.
The implementation refuses floats as purported exact inputs. This is a
closed-form certificate argument, not an assertion that mpmath decimals are
interval bounds. Numerical high-precision comparisons are secondary tests.

Next proposed task A-RH-CONGEST-0018: find an ANALYTIC source-compatible
hypothesis bounding the interval overload witnesses AND the depth-weighted
cost F*/Q, or prove that the current charged representation is too restrictive.
A density statement alone is insufficient by (14). A large surrogate optimum
cannot be treated as impossibility for the true operator. Actual certified
zero inputs, retained cap/tail bounds and the independent mathematical reviews
remain distinct debts. No unconditional zero-proportion improvement, RH proof,
literature-wide novelty, main merge or authority promotion is claimed.
