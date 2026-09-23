# Model card

## What it does

Predicts which party won each West Bengal assembly seat in 2026, from the 2021
result plus a statewide swing. 293 seats, the ones that polled in both years.

Two things are on offer. A uniform swing baseline, which moves one number from
TMC to BJP in every seat and recounts. And fitted classifiers that add
seat-level features on top. The baseline is the point of comparison for
everything else.

## Intended use

Coursework and my own curiosity. It is a retrospective fit of one election to
the one before it, in one state, so a seat projection out of it is not a
prediction of anything and shouldn't be quoted as one.

## Data

`data/raw/bengal_elections.db`, built from Election Commission of India
statistical reports for the West Bengal Legislative Assembly, 2021 and 2026.
Provenance and known problems: [../data/raw/README.md](../data/raw/README.md).

Vote share is a percentage of valid votes with NOTA excluded, which is the
basis the Commission's published figures use. It reproduces 48.55 / 38.39 for
2021 and 41.12 / 46.20 for 2026, and `tests/test_features.py` checks that
against the raw results table rather than against the built features.

## Features

Two sets, kept apart on purpose.

**Pre-election.** 2021 vote shares for TMC, BJP and the Left/Congress bloc,
the 2021 margin and two-party lead, 2021 turnout, reservation status, region.
All knowable before polling day.

**Post-election.** The above plus the 2026 roll change and turnout change.
Both measured alongside the outcome. A model using them is explaining, not
predicting, and the gap between the two sets is the only thing the second is
good for.

The post set scores worse than the pre set. That is a finding, not a bug.

## Baseline

Uniform two-party swing, 7.60 points. Calls 198 BJP seats against an actual
207, and gets 246 of 293 seats right.

It is a two-party model deliberately. An earlier version picked winners by
argmax across aggregated blocs and invented winners that never existed, because
a bloc sum is not a candidate. The only third element now is the actual share
of the winning candidate in the two seats a third party held in 2021.

## Evaluation

Two numbers, because they disagree:

- **Seat-count error**, how far the statewide total is off.
- **Per-seat accuracy**, how many individual seats are called right.

A model can look good on the first while being bad on the second, if its misses
cancel. Uniform swing is 9 seats under on the total and wrong on 47 individual
seats.

Fitted models use 5-fold stratified cross-validation over seats.

## Known limitations

**There is no held-out election.** Two elections in one state. Cross-validation
over seats is the best available and it is not the same thing — every model
here has seen the election it is scored on, at the statewide level, because the
swing it is given is the swing that actually happened. Treat every accuracy
figure as an upper bound.

**The lead-scaling slope is fitted on the outcome.** The +0.0985 drift term in
the simulation was measured on 2026 and then used to predict 2026. It makes the
deterministic call better (198 to 204 against 207), and it would be worth
nothing in a genuine forecast.

**Swing uncertainty is an assumption.** The simulation's 2-point standard
deviation on the statewide swing is a guess at polling error. This data has one
election and cannot measure it. The interval widens or narrows with that
number, so read it as a sensitivity, not a confidence interval.

**The roll shrank by about 5 million names and I don't know why.** Anything
touching turnout inherits that. It turned out not to help predict seats, which
doesn't mean it didn't matter — only that its effect isn't visible in this
target.

**No candidate-level features.** Cross-year name matching in this data fans out
badly: joining 2026 winners to 2021 candidates returns 300 rows for 293 seats.
So incumbency, candidate switching and re-contest effects are all out of reach,
and they are plausibly a large part of what the residuals contain.

**The district mapping is derived, not sourced.** Inherited from the earlier
project, where it was inferred from the Commission's numbering rather than
taken from an official list. Regional claims here are safer than district ones.

**Falta is excluded.** It polled in 2021 and not in 2026, so 293 seats rather
than 294. Statewide 2021 figures computed on this table differ slightly from
published ones for that reason, and the tests pin both versions.

## Ethical notes

This is aggregate seat arithmetic. It says nothing about why anyone voted the
way they did, and nothing here supports a claim about individual voters or
about any group of them.

The roll contraction is the one result with obvious political weight. I've
deliberately kept it as an unexplained observation rather than attributing a
cause, because this data cannot distinguish between the explanations, and the
explanations are not politically neutral.
