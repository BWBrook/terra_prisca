# Post-review endpoint classes: fixed criteria

This is a descriptive amendment following Claude's review, not a change to
the original experiment, stopping rule, or 128 stored strict labels. The
candidate set is the 41 `dormant_stock_only_stationarity_failure` paths in
the existing checksum-pinned endpoint diagnostic. The criteria below are
fixed before fitting their bank trajectories.

An additional **macro state stationary** label requires the original final
20,000-year criteria on every active stock, hydrogen, acetate and methane:
relative span below 0.001 with the original floors, temperature span below
0.01 K, scaled terminal derivative below 0.001, and unchanged local census
occupancy. Total active-plus-dormant biomass in every habitat/guild must pass
the same span and derivative checks. No late census removal may occur. Every
individual stock failing the original span test must be dormant.

For **settled up to dormant relaxation**, also recover a root on the observed
present-guild face. Its active/chemical stocks, total guild biomass,
temperature and census occupancy must agree with the endpoint under those
same comparisons. Pure-resident roots come from the recorded preparation
candidates at identical model parameters; mixed roots are refined from the
late mean with the existing positive-stock equations and stationary bank
balance. This does not enumerate roots or establish full-community stability
against reintroduction of a censused guild.

At the root the dormant bank obeys a stable affine linear system

    Zdot = A* Z + S*,
    A* = -diag(rho* + epsilon L + d) + d 1 w^T,
    S* = sigma* X*.

Starting at the first saved late state, propagate this frozen bank system
over the actual saved intervals by a matrix exponential. For **each failing
dormant stock**, its maximum prediction error must be at most 0.001 of its
observed late-window range, and at most 0.001 of its original mean/floor
normalization. This tests the resolved trajectory, not merely a small biomass
fraction. The output also reports all-bank fits and sampled source variation.
Exact zero entry at every saved late state distinguishes a sampled
source-free bank from root-supported relaxation; it is not a between-sample
absence proof. Relative accuracy of tiny terminal banks is not inferred.

If the macro tests pass but these root/trajectory tests fail, retain the
separate **macro state stationary; dormant bank unresolved** description.
Smallness alone never earns the verified-relaxation class.

Endpoint pairs retain the original strict comparison. An additional macro
comparison requires both macro labels plus matching active/chemical stocks,
total guild biomass, temperature and local/global one-cell occupancy. A
limiting full-root comparison is reported only where both bank fits qualify;
unresolved banks are not silently projected onto roots. All conclusions are
finite-record descriptions, not global-attractor or stochastic-persistence
claims.
