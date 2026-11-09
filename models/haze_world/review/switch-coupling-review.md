# Independent review of the reduced switch coupling

Codex (GPT-6), 9 November 2026; reviews historical commit `aae88c5`.
**The reference mixed-state feedback calculation is correct within its
reduced equations. Its capture closure is assumed, and the root finder and
stability labels need repairs.** This does not validate a full population
coupling or establish a new biological thermostat.

The [checker](check_switch_coupling.py) loads the reviewed source from Git,
leaving subsequent repairs and historical outputs intact. It checks the
Jacobian independently, compares physiological capture, and supplies root
and stability counterexamples. [Results and hashes](switch_coupling_review.json):

```sh
uv run python models/haze_world/review/check_switch_coupling.py
```

## 1. Shared capture at coexistence does not identify the inherited η

Sharing one R* makes both guilds share the **actual** captured flux

    C = J − k_ex (R* − p_atm).

It does not make C/J equal the old haze-world η, which uses different
thermal physiology and resource parameters. The methanogen-only η-limit
test establishes an identity after setting maintenance, cessation pressure,
atmospheric pressure and biomass allocation to their specified limits; the
imported switches were not generated in those limits.

Using the central fixed-energy, 300 Pa lifeless-pressure configurations:

| Acetogen law | Switch (K) | Actual C/J | Inherited η | Acetogen post-assimilation factor b_A |
|---|---:|---:|---:|---:|
| Saturating | 281.534823 | 0.925046 | 0.923627 | 0.894871 |
| First order | 282.780106 | 0.933601 | 0.977094 | 0.898385 |

The default methanogen factor b_M is 1. If s means the acetogen share of
**captured H₂**, physiological methane delivery is

    S = C/4 [(1−s)b_M + f_ac s b_A] + S_abiotic,
    b_i = 1 − a_i d/Q_i,    Q_i = m_i + d/Y_i.

The reduced factor 1−(1−f_ac)s omits this distinction. Calling s a catabolic
share instead would change its connection to the competition/population
model and would not restore the inherited η automatically.

**Required qualification:** inherited η and routing are explicit closures
even at mixed states. Full acetate recycling makes the reduced methane
equation identical to the old budget by construction. It does not establish
that the two physiological guilds capture or deliver methane identically.
Even in the reduced model, equality concerns the r trajectory: composition
continues to evolve unless it is at an endpoint or T = T_sw.

## 2. The mixed Jacobian is correct; the trace condition matters

Independent analytic derivatives and central differences agree for the four
mixed reference states at (281.5 K, f_ac=0) and (282.8 K, f_ac=0.5). The
determinant is f_x g T_r. Thus greenhouse states are saddles. On the haze
branch, stability for every positive g additionally requires **f_r < 0**.
The reference switches lie on the cold flank of the inherited growth curve,
where η_T > 0, so negative T_r and positive loss slope make f_r negative.

This is not a theorem for every parameterized haze branch. An allowed
counterexample changes only the inherited optimum to 275 K, uses T_sw=293 K
and f_ac=0. Its cooling mixed state has r=0.17557418, s=0.17092326,
T_r=−450.094, trace **+2.31557×10⁻⁴ yr⁻¹**, determinant 0.00134654 and maximum
eigenvalue real part **+1.15779×10⁻⁴ yr⁻¹** at g=1. The code correctly calls
it unstable. Retain the trace condition when stating the all-g result.

These are local results for the prescribed two-dimensional dynamics.
Neither the assumed fast-competition reduction nor absence of delay-induced
instability in a resource–population–methane system follows from them.

## 3. Strict sign-change detection drops supported states

`_sign_changes` requires opposite nonzero signs at adjacent samples. It
omits exact sampled roots, interval endpoints and tangencies. Explicitly
inserting climate vertices therefore does not make their roots safe.

Concrete example with the unchanged reference budget: T_sw=**282.005 K**,
f_ac=0 has a valid cooling mixed state at the climate vertex
**r=0.19445499**, **s=0.08168167**. The original finder returns only its
greenhouse counterpart, r=0.03527437, and drops the cooling candidate.
The synthetic checks also miss x=0 on [0,1] and an interior double root.

Retain exact roots and distinguish crossing roots from contacts. For a
complete bifurcation claim, folds require an extremum/tangency search or
continuation, not only a denser sign grid. The reported nine reference
scenarios are not themselves disproved by this vertex example, but a
general assertion that no other branch or cold state exists is unsupported.

## 4. Pure and no-capture flags mix different stability questions

On the compact share coordinate s, a pure-methanogen state's composition
eigenvalue is −g(T−T_sw); the pure-acetogen eigenvalue is +g(T−T_sw).
Away from equality, the living-state orientation filter uses the correct
sign. At equality the eigenvalue is zero, yet the code can mark the state
stable from its methane direction alone. That is a nonhyperbolic branch
boundary, not strict invasion resistance; one-sided or nonlinear analysis
is needed to characterize it.

For the reference abiotic climate, the saved no-capture row has s=0,
T=265.596242 K and `stable=True`. With T_sw=281.5 K its compact composition
eigenvalue is **+15.903758 yr⁻¹**. The deduplication kept the unstable s=0
representative and discarded s=1, which has the same climate and the opposite
composition sign. Capture share is physically undefined when capture is zero.
Label its climate stability separately, rather than attaching full-state
stability to the saved share. This does not remove the old abiotic climate
attractor or demonstrate biological reinvasion in a population model.

## Accepted result and next test

Within the imposed reduced equations, an interior mixture on the reference
haze branch can pin temperature at T_sw and absorb supply changes into
composition. The local restoring sign and Jacobian support that result.
Capture magnitude, source allocation, selection dynamics and establishment
must come from the same physiological configuration before treating that
pinning as a result of the population model. Preserve the reduced output
as a transparent prototype and test those quantities in the full coupling.
